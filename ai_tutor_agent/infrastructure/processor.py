import os
import sys
import time
import signal
import shutil
import zipfile
import tempfile
import requests

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from dotenv import load_dotenv


class KnowledgeProcessor:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.batch_url = "https://mineru.net/api/v4/file-urls/batch"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        print(f"🛠️ [DEBUG] Processor 初始化成功. Token 前四位: {self.api_token[:4]}")

    def parse_pdf_to_md(self, local_path: str) -> str:
        """
        使用 MinerU Token + 本地文件上传方式解析 PDF，并返回 full.md 的文本内容
        """
        load_dotenv()

        token = os.getenv("MINERU_API_TOKEN") or self.api_token
        if not token:
            raise ValueError("❌ 错误：未在 .env 文件中找到 MINERU_API_TOKEN，且未传入 api_token。")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"❌ 文件不存在: {local_path}")

        BASE_URL = "https://mineru.net/api/v4"
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        file_name = os.path.basename(local_path)
        file_size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"📄 [任务] 准备解析本地文件: {file_name} ({file_size_mb:.2f} MB)")

        def _download_and_extract_markdown(full_zip_url: str) -> str:
            """
            下载 MinerU 返回的 zip 结果包，解压并读取 full.md
            """
            temp_dir = tempfile.mkdtemp(prefix="mineru_")
            zip_path = os.path.join(temp_dir, "result.zip")

            try:
                print("📥 [Step 4] 正在下载解析结果压缩包...")
                resp_zip = requests.get(full_zip_url, timeout=120)
                resp_zip.raise_for_status()

                with open(zip_path, "wb") as f:
                    f.write(resp_zip.content)

                print("📦 [Step 5] 正在解压结果文件...")
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(temp_dir)

                md_candidates = []
                for root, _, files in os.walk(temp_dir):
                    for name in files:
                        if name == "full.md":
                            md_candidates.append(os.path.join(root, name))

                if not md_candidates:
                    raise FileNotFoundError("❌ 解压完成，但未找到 full.md")

                md_path = md_candidates[0]
                print(f"✅ [Step 5] 找到 Markdown 文件: {md_path}")

                with open(md_path, "r", encoding="utf-8") as f:
                    return f.read()

            finally:
                # 你如果想保留中间文件做调试，可以先把下面这行注释掉
                shutil.rmtree(temp_dir, ignore_errors=True)

        def _normalize_extract_result(data_obj: dict, expected_file_name: str) -> dict:
            """
            兼容 MinerU 批量结果接口中 extract_result 为 dict 或 list 的情况
            优先找 file_name 匹配当前文件的结果
            """
            extract_result = data_obj.get("extract_result", {})

            if isinstance(extract_result, dict):
                return extract_result

            if isinstance(extract_result, list):
                if len(extract_result) == 1:
                    return extract_result[0]

                for item in extract_result:
                    if isinstance(item, dict) and item.get("file_name") == expected_file_name:
                        return item

                for item in extract_result:
                    if isinstance(item, dict):
                        return item

            return {}

        try:
            # ---------------------------------------------------------
            # 步骤 1: 申请上传链接
            # ---------------------------------------------------------
            print("📡 [Step 1] 正在向 MinerU 申请上传链接...")

            apply_url = f"{BASE_URL}/file-urls/batch"
            data_id = f"local_{int(time.time())}_{file_name}"

            payload = {
                "files": [
                    {"name": file_name, "data_id": data_id}
                ],
                "model_version": "vlm"
            }

            try:
                resp_apply = requests.post(
                    apply_url,
                    headers=HEADERS,
                    json=payload,
                    timeout=30
                )
                resp_apply.raise_for_status()
                result_apply = resp_apply.json()
            except requests.exceptions.Timeout:
                raise Exception("⏱️ 申请上传链接超时！请检查网络、代理或 MinerU 服务状态。")
            except requests.exceptions.RequestException as e:
                raise Exception(f"🌐 申请上传链接失败: {e}")

            if result_apply.get("code") != 0:
                msg = result_apply.get("msg", "未知错误")
                raise Exception(f"❌ 申请链接失败 (Code {result_apply.get('code')}): {msg}")

            data_content = result_apply.get("data", {})
            batch_id = data_content.get("batch_id")
            upload_urls = data_content.get("file_urls", [])

            if not batch_id:
                raise Exception("❌ 服务器返回数据中缺少 batch_id")
            if not upload_urls:
                raise Exception("❌ 服务器未返回上传链接")

            upload_url = upload_urls[0]
            print(f"✅ [Step 1] 链接获取成功 (Batch ID: {batch_id})")

            # ---------------------------------------------------------
            # 步骤 2: 上传文件
            # ---------------------------------------------------------
            print("📤 [Step 2] 正在上传文件到云端 (请勿关闭)...")

            try:
                with open(local_path, "rb") as f:
                    resp_upload = requests.put(upload_url, data=f, timeout=300)
                    resp_upload.raise_for_status()
            except requests.exceptions.Timeout:
                raise Exception("⏱️ 文件上传超时，请检查网络后重试。")
            except requests.exceptions.RequestException as e:
                raise Exception(f"❌ 文件上传失败: {e}")

            print("✅ [Step 2] 文件上传成功！系统已自动提交解析任务。")

            # ---------------------------------------------------------
            # 步骤 3: 轮询查询结果
            # ---------------------------------------------------------
            print("⏳ [Step 3] 等待云端解析完成 (通常需 10-60 秒)...")
            print("💡 提示：按 Ctrl+C 可随时安全终止任务。")

            max_wait_time = 600
            start_time = time.time()
            poll_interval = 10

            def signal_handler(sig, frame):
                print("\n\n⚠️ 用户主动终止 (Ctrl+C)。正在退出...")
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)

            final_state = None
            result_url = None

            while True:
                elapsed = int(time.time() - start_time)
                if elapsed > max_wait_time:
                    raise TimeoutError(
                        f"解析超时 ({max_wait_time}s)。Batch ID: {batch_id}。请稍后去官网控制台查看。"
                    )

                try:
                    query_url = f"{BASE_URL}/extract-results/batch/{batch_id}"
                    resp_query = requests.get(
                        query_url,
                        headers=HEADERS,
                        timeout=15
                    )

                    print(f"   🔍 轮询状态码: {resp_query.status_code}")
                    resp_query.raise_for_status()

                    query_result = resp_query.json()
                    code = query_result.get("code")

                    if code != 0:
                        msg = query_result.get("msg", "Unknown")
                        print(f"   ⚠️ 服务端返回异常 Code {code}: {msg}")
                        time.sleep(poll_interval)
                        continue

                    data_obj = query_result.get("data", {})
                    task_info = _normalize_extract_result(data_obj, file_name)

                    state = task_info.get("state")
                    err_msg = task_info.get("err_msg", "")
                    full_zip_url = task_info.get("full_zip_url")
                    final_state = state

                    if state:
                        print(f"   ⏱ 解析进行中... 状态: [{state.upper()}] ({elapsed}s)")
                    else:
                        keys = list(task_info.keys()) if isinstance(task_info, dict) else []
                        print(f"   ⏱ 解析进行中... 状态: None (数据键值: {keys}) ({elapsed}s)")

                    if state == "done":
                        print(f"\n🎉 解析完成！耗时: {elapsed}s")
                        if not full_zip_url:
                            raise Exception("❌ 任务已完成，但未返回 full_zip_url")
                        result_url = full_zip_url
                        break

                    elif state == "failed":
                        raise Exception(f"❌ 云端解析失败: {err_msg or '未知错误'}")

                    elif state in ["waiting-file", "pending", "running", "converting"]:
                        pass

                    else:
                        print(f"   ❓ 遇到未知状态: {state}")

                except requests.exceptions.Timeout:
                    print(f"   ⚠️ 查询请求超时 (>15s)，重试中... ({elapsed}s)")
                except KeyboardInterrupt:
                    print("\n⚠️ 检测到中断信号，正在退出...")
                    sys.exit(0)
                except Exception as e:
                    print(f"   ❌ 轮询发生异常: {e}")

                time.sleep(poll_interval)

            if final_state != "done" or not result_url:
                raise Exception(f"❌ 解析结束但结果异常，final_state={final_state}, result_url={result_url}")

            markdown_content = _download_and_extract_markdown(result_url)

            if not markdown_content.strip():
                raise Exception("⚠️ Markdown 内容为空，请检查 PDF 内容或 MinerU 输出结果。")

            print("✅ [完成] Markdown 提取成功。")
            return markdown_content

        except Exception:
            raise

    def split_by_semantics(self, md_content: str) -> list[Document]:
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
        )
        return splitter.split_text(md_content)