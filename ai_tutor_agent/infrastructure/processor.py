import os
import re
import time
import json
import shutil
import zipfile
import tempfile
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
#图表公式功能添加的
import hashlib
from pathlib import Path
#----图表公式------

@dataclass
class MinerUParseResult:
    full_md: str
    extract_dir: str
    assets_dir: Optional[str]
    json_files: Dict[str, str]


class KnowledgeProcessor:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.batch_url = "https://mineru.net/api/v4/file-urls/batch"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        self.session = requests.Session()
        self.session.trust_env = False
        print(f"🛠️ [DEBUG] Processor 初始化成功. Token 前四位: {self.api_token[:4] if self.api_token else 'NONE'}")

    # ---------------------------
    # MinerU 下载与解压
    # ---------------------------
    def parse_pdf(self, local_path: str, keep_extract_dir: bool = True) -> MinerUParseResult:
        load_dotenv()

        token = os.getenv("MINERU_API_TOKEN") or self.api_token
        if not token:
            raise ValueError("❌ 未找到 MINERU_API_TOKEN。")

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

        def _normalize_extract_result(data_obj: dict, expected_file_name: str) -> dict:
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

        def _download_and_extract(full_zip_url: str) -> MinerUParseResult:
            temp_dir = tempfile.mkdtemp(prefix="mineru_")
            zip_path = os.path.join(temp_dir, "result.zip")

            print("📥 [Step 4] 正在下载解析结果压缩包...")
            resp_zip = self.session.get(full_zip_url, timeout=120)
            resp_zip.raise_for_status()

            with open(zip_path, "wb") as f:
                f.write(resp_zip.content)

            print("📦 [Step 5] 正在解压结果文件...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            md_path = None
            json_files: Dict[str, str] = {}
            assets_dir = None

            for root, _, files in os.walk(temp_dir):
                for name in files:
                    lower = name.lower()
                    abs_path = os.path.join(root, name)

                    if name == "full.md":
                        md_path = abs_path
                    if lower.endswith(".json"):
                        json_files[name] = abs_path

                # 常见图片目录名
                if os.path.basename(root).lower() in {"images", "imgs", "figures", "assets"}:
                    assets_dir = root

            if not md_path:
                raise FileNotFoundError("❌ 解压后未找到 full.md")

            with open(md_path, "r", encoding="utf-8") as f:
                full_md = f.read()

            if not keep_extract_dir:
                # 不保留时，直接读完再删
                result = MinerUParseResult(
                    full_md=full_md,
                    extract_dir=temp_dir,
                    assets_dir=assets_dir,
                    json_files=json_files,
                )
                shutil.rmtree(temp_dir, ignore_errors=True)
                return result

            return MinerUParseResult(
                full_md=full_md,
                extract_dir=temp_dir,
                assets_dir=assets_dir,
                json_files=json_files,
            )

        # Step 1 申请链接
        print("📡 [Step 1] 正在向 MinerU 申请上传链接...")
        apply_url = f"{BASE_URL}/file-urls/batch"
        data_id = f"local_{int(time.time())}_{file_name}"
        payload = {
            "files": [{"name": file_name, "data_id": data_id}],
            "model_version": "vlm",
        }

        resp_apply = self.session.post(apply_url, headers=HEADERS, json=payload, timeout=30)
        resp_apply.raise_for_status()
        result_apply = resp_apply.json()

        if result_apply.get("code") != 0:
            raise Exception(f"❌ 申请链接失败: {result_apply}")

        data_content = result_apply.get("data", {})
        batch_id = data_content.get("batch_id")
        upload_urls = data_content.get("file_urls", [])
        if not batch_id or not upload_urls:
            raise Exception("❌ MinerU 返回缺少 batch_id 或 upload url")

        upload_url = upload_urls[0]
        print(f"✅ [Step 1] 链接获取成功 (Batch ID: {batch_id})")

        # Step 2 上传
        print("📤 [Step 2] 正在上传文件到云端...")
        with open(local_path, "rb") as f:
            resp_upload = self.session.put(upload_url, data=f, timeout=300)
            resp_upload.raise_for_status()
        print("✅ [Step 2] 文件上传成功！")

        # Step 3 轮询
        print("⏳ [Step 3] 等待云端解析完成...")
        max_wait_time = 600
        start_time = time.time()
        poll_interval = 10

        final_state = None
        result_url = None

        while True:
            elapsed = int(time.time() - start_time)
            if elapsed > max_wait_time:
                raise TimeoutError(f"解析超时 ({max_wait_time}s), batch_id={batch_id}")

            query_url = f"{BASE_URL}/extract-results/batch/{batch_id}"
            resp_query = self.session.get(query_url, headers=HEADERS, timeout=15)
            resp_query.raise_for_status()

            query_result = resp_query.json()
            if query_result.get("code") != 0:
                print(f"⚠️ 服务端返回异常: {query_result}")
                time.sleep(poll_interval)
                continue

            data_obj = query_result.get("data", {})
            task_info = _normalize_extract_result(data_obj, file_name)
            state = task_info.get("state")
            full_zip_url = task_info.get("full_zip_url")
            final_state = state

            print(f"   ⏱ 状态: {state} ({elapsed}s)")

            if state == "done":
                result_url = full_zip_url
                break
            if state == "failed":
                raise Exception(f"❌ 云端解析失败: {task_info.get('err_msg')}")
            time.sleep(poll_interval)

        if final_state != "done" or not result_url:
            raise Exception(f"❌ 解析完成但结果异常: state={final_state}, url={result_url}")

        result = _download_and_extract(result_url)
        if not result.full_md.strip():
            raise Exception("⚠️ Markdown 内容为空")
        print("✅ [完成] MinerU 解析成功。")
        return result
    
    # ---------------------------
    #缓存下载工具
    # ---------------------------
    def _file_md5(self, file_path: str) -> str:
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _ensure_dir(self, path: str) -> str:
        os.makedirs(path, exist_ok=True)
        return path

    def _copy_if_not_exists(self, src: str, dst: str) -> str:
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
        return dst

    def persist_parse_result(
        self,
        local_pdf_path: str,
        parse_result: MinerUParseResult,
        cache_root: str = "data/mineru_cache"
    ) -> Dict[str, Any]:
        """
        把 MinerU 临时解压结果转存到固定缓存目录，并返回缓存信息
        """
        pdf_name = os.path.basename(local_pdf_path)
        pdf_md5 = self._file_md5(local_pdf_path)
        pdf_slug = self._slugify_name(pdf_name)
        doc_cache_dir = os.path.join(cache_root, f"{pdf_slug}__{pdf_md5[:8]}")
        images_dir = os.path.join(doc_cache_dir, "images")
        json_dir = os.path.join(doc_cache_dir, "json")

        self._ensure_dir(doc_cache_dir)
        self._ensure_dir(images_dir)
        self._ensure_dir(json_dir)

        # 保存 full.md
        full_md_path = os.path.join(doc_cache_dir, "full.md")
        if not os.path.exists(full_md_path):
            with open(full_md_path, "w", encoding="utf-8") as f:
                f.write(parse_result.full_md)

        # 保存 json
        persisted_json = {}
        for name, src_path in (parse_result.json_files or {}).items():
            dst_path = os.path.join(json_dir, name)
            self._copy_if_not_exists(src_path, dst_path)
            persisted_json[name] = dst_path

        # 保存图片
        persisted_images = {}
        if parse_result.assets_dir and os.path.isdir(parse_result.assets_dir):
            all_image_files = []

            for root, _, files in os.walk(parse_result.assets_dir):
                for name in files:
                    src_path = os.path.join(root, name)
                    rel_path = os.path.relpath(src_path, parse_result.assets_dir).replace("\\", "/")
                    ext = os.path.splitext(name)[1].lower() or ".jpg"
                    all_image_files.append((rel_path, src_path, ext))

            all_image_files.sort(key=lambda x: x[0])

            for idx, (rel_path, src_path, ext) in enumerate(all_image_files, start=1):
                new_name = f"figure_{idx:02d}{ext}"
                dst_path = os.path.join(images_dir, new_name)

                self._copy_if_not_exists(src_path, dst_path)

                persisted_images[rel_path] = {
                    "original_name": os.path.basename(src_path),
                    "original_rel_path": rel_path,
                    "friendly_name": new_name,
                    "abs_path": dst_path,
                    "index": idx,
                }

        manifest = {
            "pdf_name": pdf_name,
            "pdf_md5": pdf_md5,
            "cache_dir": doc_cache_dir,
            "full_md_path": full_md_path,
            "images_dir": images_dir,
            "json_dir": json_dir,
            "images": persisted_images,
            "json_files": persisted_json,
        }

        manifest_path = os.path.join(doc_cache_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        manifest["manifest_path"] = manifest_path
        return manifest

    
    def _resolve_image_abs_path(self, img_path: str, persisted_manifest: Dict[str, Any]) -> str:
        """
        将 markdown 中的相对图片路径映射到缓存目录中的绝对路径
        """
        img_path = (img_path or "").strip().replace("\\", "/")
        images_map = persisted_manifest.get("images", {})

        if img_path in images_map:
            return images_map[img_path]["abs_path"]

        image_name = os.path.basename(img_path)
        for _, item in images_map.items():
            if item.get("original_name") == image_name:
                return item.get("abs_path", "")

        fallback = os.path.join(persisted_manifest["images_dir"], image_name)
        return fallback


     # -------------
     #图片索引
     # -------------
    
    def _parse_figure_caption_line(self, line: str) -> Optional[Dict[str, Any]]:
        line = (line or "").strip()
        m = re.match(r"^\s*(Figure|Fig\.?)\s*(\d+)\s*[:\.]\s*(.*)$", line, flags=re.I)
        if not m:
            return None

        num = int(m.group(2))
        tail = (m.group(3) or "").strip()
        label = f"Figure {num}"
        caption = f"{label}: {tail}" if tail else label

        return {
            "figure_num": num,
            "figure_label": label,
            "caption": caption,
        }   

    def _extract_image_paths_from_line(self, line: str) -> List[str]:
        matches = re.findall(r"!\[(.*?)\]\((.*?)\)", line or "")
        paths = []
        for _, img_path in matches:
            img_path = (img_path or "").strip().replace("\\", "/")
            if img_path:
                paths.append(img_path)
        return paths

    def _parse_table_caption_line(self, line: str) -> Optional[Dict[str, Any]]:
        line = (line or "").strip()
        m = re.match(r"^\s*(Table|表)\s*(\d+)\s*[:：\.]?\s*(.*)$", line, flags=re.I)
        if not m:
            return None

        num = int(m.group(2))
        tail = (m.group(3) or "").strip()
        label = f"Table {num}"
        caption = f"{label}: {tail}" if tail else label

        return {
            "table_num": num,
            "table_label": label,
            "caption": caption,
        }

    def _is_markdown_table_line(self, line: str) -> bool:
        line = (line or "").strip()
        if not line:
            return False

        if line.count("|") >= 2:
            return True

        if re.match(r"^\s*\|?[\-\:\|\s]{3,}\|?\s*$", line):
            return True

        return False

    def _normalize_math_text(self, text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def extract_figure_objects(
        self,
        md_content: str,
        persisted_manifest: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        lines = md_content.splitlines()
        figure_objects: List[Dict[str, Any]] = []

        pending_images: List[str] = []
        current_obj: Optional[Dict[str, Any]] = None

        def flush_current():
            nonlocal current_obj
            if not current_obj:
                return

            # 去重保持顺序
            seen = set()
            dedup_rel = []
            for p in current_obj["image_paths"]:
                p = (p or "").replace("\\", "/").strip()
                if p and p not in seen:
                    seen.add(p)
                    dedup_rel.append(p)

            image_paths_abs = []
            image_friendly_names = []

            for rel_path in dedup_rel:
                abs_path = self._resolve_image_abs_path(rel_path, persisted_manifest)
                image_paths_abs.append(abs_path)

                image_info = persisted_manifest.get("images", {}).get(rel_path, {})
                image_friendly_names.append(
                    image_info.get("friendly_name", os.path.basename(abs_path))
                )

            current_obj["image_paths"] = dedup_rel
            current_obj["image_paths_abs"] = image_paths_abs
            current_obj["image_friendly_names"] = image_friendly_names
            current_obj["surrounding_text"] = self._safe_text(
                " ".join(current_obj["surrounding_text_parts"]),
                max_len=1200
            )

            figure_objects.append(current_obj)
            current_obj = None

        for i, raw_line in enumerate(lines):
            line = (raw_line or "").strip()
            if not line:
                continue

            # 1) 图片行：先暂存，等后面的 Figure X caption 来认领
            image_paths = self._extract_image_paths_from_line(line)
            if image_paths:
                if current_obj is None:
                    pending_images.extend(image_paths)
                else:
                    text_after_caption_count = current_obj.get("text_after_caption_count", 0)
                    current_has_images = bool(current_obj.get("image_paths"))

                    # 情况1：caption 后立刻跟图，属于当前 figure
                    if text_after_caption_count == 0:
                        current_obj["image_paths"].extend(image_paths)

                    # 情况2：caption 后已经出现过正文，再出现图片，更可能是下一个 figure 的图
                    else:
                        pending_images.extend(image_paths)

                continue

            # 2) caption 行
            cap = self._parse_figure_caption_line(line)
            if cap:
                flush_current()

                prev_text = " ".join(lines[max(0, i - 3):i]).strip()
                next_text = " ".join(lines[i + 1:i + 4]).strip()

                current_obj = {
                    "figure_num": cap["figure_num"],
                    "figure_label": cap["figure_label"],
                    "caption": cap["caption"],
                    "image_paths": list(pending_images),
                    "surrounding_text_parts": [],
                    "text_after_caption_count": 0,
                }
                pending_images = []

                if prev_text:
                    current_obj["surrounding_text_parts"].append(prev_text)
                current_obj["surrounding_text_parts"].append(line)
                if next_text:
                    current_obj["surrounding_text_parts"].append(next_text)
                continue

            # 3) 普通正文
            if current_obj is not None:
                if len(" ".join(current_obj["surrounding_text_parts"])) < 1500:
                    current_obj["surrounding_text_parts"].append(line)

                current_obj["text_after_caption_count"] = current_obj.get("text_after_caption_count", 0) + 1

        flush_current()
        return figure_objects

    # ---------------------------
    # 工具函数
    # ---------------------------
    def _safe_text(self, text: str, max_len: int = 1800) -> str:
        text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
        return text[:max_len]

    def extract_table_objects(self, md_content: str) -> List[Dict[str, Any]]:
        lines = md_content.splitlines()
        table_objects: List[Dict[str, Any]] = []
        debug_table = True

        current_obj: Optional[Dict[str, Any]] = None

        def flush_current():
            nonlocal current_obj
            if not current_obj:
                return
            if debug_table:
                print(
                    f"🧪 [TABLE DEBUG] flush {current_obj['table_label']} | "
                    f"rows={len(current_obj['table_lines'])} | "
                    f"preview={(current_obj['caption'][:80])}"
                )

            current_obj["table_text"] = self._safe_text(
                "\n".join(current_obj["table_lines"]),
                max_len=4000
            )
            current_obj["surrounding_text"] = self._safe_text(
                " ".join(current_obj["surrounding_text_parts"]),
                max_len=1200
            )

            table_objects.append(current_obj)
            current_obj = None

        i = 0
        while i < len(lines):
            stripped = (lines[i] or "").strip()

            if not stripped:
                i += 1
                continue

            cap = self._parse_table_caption_line(stripped)
            if cap:
                if debug_table:
                    print(f"🧪 [TABLE DEBUG] 命中 caption: {cap['table_label']} @ line {i+1}")

                flush_current()

                current_obj = {
                    "table_num": cap["table_num"],
                    "table_label": cap["table_label"],
                    "caption": cap["caption"],
                    "table_lines": [],
                    "surrounding_text_parts": [stripped],
                }
                i += 1
                continue

            if current_obj is not None:
                # 遇到下一个 Table / Figure caption，先收束当前 table
                if self._parse_table_caption_line(stripped) or self._parse_figure_caption_line(stripped):
                    flush_current()
                    continue

                # 收集 html table
                if re.search(r"<table.*?>", stripped, flags=re.I):
                    if debug_table:
                        print(f"🧪 [TABLE DEBUG] {current_obj['table_label']} 开始收集 HTML table @ line {i+1}")

                    # 先处理“单行完整 table”
                    single_match = re.search(r"(<table.*?</table>)", stripped, flags=re.S | re.I)
                    if single_match:
                        current_obj["table_lines"].append(single_match.group(1).strip())
                        i += 1
                        continue

                    # 再处理“多行 table”
                    html_parts = [stripped]
                    i += 1
                    while i < len(lines):
                        html_line = (lines[i] or "").rstrip()
                        html_strip = html_line.strip()

                        # 如果还没遇到 </table>，却先遇到新的 Table / Figure caption，
                        # 说明前一个 table 收集范围有问题，立刻停止，把机会留给外层重新识别
                        if self._parse_table_caption_line(html_strip) or self._parse_figure_caption_line(html_strip):
                            i -= 1
                            break

                        html_parts.append(html_line)

                        if re.search(r"</table>", html_strip, flags=re.I):
                            break

                        i += 1

                    html_blob = "\n".join(html_parts)
                    m = re.search(r"(<table.*?</table>)", html_blob, flags=re.S | re.I)
                    if m:
                        current_obj["table_lines"].append(m.group(1).strip())
                    else:
                        current_obj["table_lines"].append(html_blob.strip())

                    i += 1
                    continue

                # 收集 markdown table
                if self._is_markdown_table_line(stripped):
                    current_obj["table_lines"].append(stripped)
                    i += 1
                    continue

                # 少量附近正文
                if len(" ".join(current_obj["surrounding_text_parts"])) < 1200:
                    current_obj["surrounding_text_parts"].append(stripped)

            i += 1

        flush_current()

        if debug_table:
            print("🧪 [TABLE DEBUG] 最终抽到的 table 对象：")
            for obj in table_objects:
                print(f"   - {obj['table_label']} | rows={len(obj['table_lines'])}")

        return table_objects

    def _guess_section(self, meta: Dict[str, Any]) -> str:
        return (
            meta.get("H3")
            or meta.get("H2")
            or meta.get("H1")
            or "UNKNOWN"
        )

    def _build_base_meta(self, doc_meta: Dict[str, Any], block_type: str, chunk_id: int) -> Dict[str, Any]:
        meta = dict(doc_meta or {})
        meta["chunk_id"] = chunk_id
        meta["section"] = self._guess_section(meta)
        meta["block_type"] = block_type
        return meta

    # ---------------------------
    # 文本块
    # ---------------------------
    def build_text_chunks(self, md_content: str, start_chunk_id: int = 0) -> List[Document]:
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
        )
        header_docs = header_splitter.split_text(md_content)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )

        final_docs: List[Document] = []
        chunk_id = start_chunk_id

        for doc in header_docs:
            content = (doc.page_content or "").strip()
            if not content:
                continue

            base_meta = dict(doc.metadata) if doc.metadata else {}
            sub_docs = text_splitter.split_text(content)

            for chunk in sub_docs:
                chunk = chunk.strip()
                if not chunk:
                    continue

                meta = self._build_base_meta(base_meta, "text", chunk_id)
                meta["char_length"] = len(chunk)

                final_docs.append(Document(page_content=chunk, metadata=meta))
                chunk_id += 1

        return final_docs

    # ---------------------------
    # 公式块
    # ---------------------------
    def build_formula_chunks(
        self,
        md_content: str,
        persisted_manifest: Dict[str, Any],
        start_chunk_id: int = 100000
    ) -> List[Document]:
        docs: List[Document] = []
        chunk_id = start_chunk_id

        lines = md_content.splitlines()
        pending_images: List[str] = []

        i = 0
        while i < len(lines):
            raw_line = lines[i]
            line = (raw_line or "").rstrip()
            stripped = line.strip()

            # 先缓存图片，留给后面的公式块认领
            image_paths = self._extract_image_paths_from_line(stripped)
            if image_paths:
                pending_images.extend(image_paths)
                i += 1
                continue

            formula_lines: List[str] = []
            surrounding_parts: List[str] = []

            # 情况1：```math ... ```
            if stripped.startswith("```math"):
                j = i + 1
                while j < len(lines):
                    candidate = lines[j]
                    if (candidate or "").strip().startswith("```"):
                        break
                    formula_lines.append(candidate)
                    j += 1

                if formula_lines:
                    prev_text = " ".join(lines[max(0, i - 3):i]).strip()
                    next_text = " ".join(lines[j + 1:min(len(lines), j + 4)]).strip()
                    if prev_text:
                        surrounding_parts.append(prev_text)
                    if next_text:
                        surrounding_parts.append(next_text)

                    latex = self._normalize_math_text("\n".join(formula_lines))
                    surrounding_text = self._safe_text(" ".join(surrounding_parts), max_len=1200)

                    # 把 pending_images 归给当前公式
                    seen = set()
                    dedup_rel = []
                    seen = set()
                    dedup_rel = []
                    for p in pending_images:
                        p = (p or "").replace("\\", "/").strip()
                        if p and p not in seen:
                            seen.add(p)
                            dedup_rel.append(p)

                    # 公式图最多保留 3 张
                    dedup_rel = dedup_rel[:3]

                    image_paths_abs = []
                    image_friendly_names = []
                    for rel_path in dedup_rel:
                        abs_path = self._resolve_image_abs_path(rel_path, persisted_manifest)
                        image_paths_abs.append(abs_path)

                        image_info = persisted_manifest.get("images", {}).get(rel_path, {})
                        image_friendly_names.append(
                            image_info.get("friendly_name", os.path.basename(abs_path))
                        )

                    page_content = (
                        f"公式块\n"
                        f"LaTeX：{latex}\n"
                        f"关联图片数量：{len(image_paths_abs)}\n"
                        f"图片相对路径列表：{dedup_rel}\n"
                        f"图片友好文件名列表：{image_friendly_names}\n"
                        f"图片绝对路径列表：{image_paths_abs}\n"
                        f"附近正文：{surrounding_text}\n"
                        f"该块为论文中的公式或数学表达式。"
                    )

                    meta = {
                        "chunk_id": chunk_id,
                        "block_type": "formula",
                        "section": "FORMULA",
                        "char_length": len(page_content),
                        "latex": latex[:1000],
                        "surrounding_text": surrounding_text[:1000],
                        "image_count": len(image_paths_abs),
                    }

                    if dedup_rel:
                        meta["image_paths"] = dedup_rel
                    if image_paths_abs:
                        meta["image_paths_abs"] = image_paths_abs
                    if image_friendly_names:
                        meta["image_friendly_names"] = image_friendly_names

                    docs.append(Document(page_content=page_content, metadata=meta))
                    chunk_id += 1
                    pending_images = []

                i = j + 1
                continue

            # 情况2：$$ ... $$
            if stripped.startswith("$$"):
                after = stripped[2:]
                closed_same_line = False

                if after.endswith("$$") and len(after) > 2:
                    formula_lines.append(after[:-2].strip())
                    closed_same_line = True
                    j = i
                else:
                    if after.strip():
                        formula_lines.append(after)
                    j = i + 1
                    while j < len(lines):
                        candidate = (lines[j] or "").rstrip()
                        cstrip = candidate.strip()

                        if cstrip.endswith("$$"):
                            content = cstrip[:-2].rstrip()
                            if content:
                                formula_lines.append(content)
                            break

                        formula_lines.append(candidate)
                        j += 1

                if formula_lines:
                    prev_text = " ".join(lines[max(0, i - 3):i]).strip()
                    next_text = " ".join(lines[j + 1:min(len(lines), j + 4)]).strip()
                    if prev_text:
                        surrounding_parts.append(prev_text)
                    if next_text:
                        surrounding_parts.append(next_text)

                    latex = self._normalize_math_text("\n".join(formula_lines))
                    surrounding_text = self._safe_text(" ".join(surrounding_parts), max_len=1200)

                    seen = set()
                    dedup_rel = []
                    for p in pending_images:
                        p = (p or "").replace("\\", "/").strip()
                        if p and p not in seen:
                            seen.add(p)
                            dedup_rel.append(p)
                    dedup_rel = dedup_rel[:1]

                    image_paths_abs = []
                    image_friendly_names = []
                    for rel_path in dedup_rel:
                        abs_path = self._resolve_image_abs_path(rel_path, persisted_manifest)
                        image_paths_abs.append(abs_path)

                        image_info = persisted_manifest.get("images", {}).get(rel_path, {})
                        image_friendly_names.append(
                            image_info.get("friendly_name", os.path.basename(abs_path))
                        )

                    page_content = (
                        f"公式块\n"
                        f"LaTeX：{latex}\n"
                        f"关联图片数量：{len(image_paths_abs)}\n"
                        f"图片相对路径列表：{dedup_rel}\n"
                        f"图片友好文件名列表：{image_friendly_names}\n"
                        f"图片绝对路径列表：{image_paths_abs}\n"
                        f"附近正文：{surrounding_text}\n"
                        f"该块为论文中的公式或数学表达式。"
                    )

                    meta = {
                        "chunk_id": chunk_id,
                        "block_type": "formula",
                        "section": "FORMULA",
                        "char_length": len(page_content),
                        "latex": latex[:1000],
                        "surrounding_text": surrounding_text[:1000],
                        "image_count": len(image_paths_abs),
                    }

                    if dedup_rel:
                        meta["image_paths"] = dedup_rel
                    if image_paths_abs:
                        meta["image_paths_abs"] = image_paths_abs
                    if image_friendly_names:
                        meta["image_friendly_names"] = image_friendly_names

                    docs.append(Document(page_content=page_content, metadata=meta))
                    chunk_id += 1
                    pending_images = []

                i = j + 1 if not closed_same_line else i + 1
                continue

            i += 1

        return docs

    # ---------------------------
    # 图片/图表块
    # ---------------------------
    def build_table_chunks(
        self,
        md_content: str,
        persisted_manifest: Dict[str, Any],
        start_chunk_id: int = 200000
    ) -> List[Document]:
        docs: List[Document] = []
        chunk_id = start_chunk_id

        table_objects = self.extract_table_objects(md_content)

        for obj in table_objects:
            table_num = obj["table_num"]
            table_label = obj["table_label"]
            caption = obj["caption"]
            table_text = obj["table_text"]
            surrounding_text = obj["surrounding_text"]

            page_content = (
                f"表格块 {table_label}\n"
                f"表标题或说明：{caption}\n"
                f"表格内容：\n{table_text if table_text else '[未抽取到结构化表格正文]'}\n"
                f"附近正文：{surrounding_text}\n"
            )

            meta = {
                "chunk_id": chunk_id,
                "block_type": "table",
                "section": "TABLE",
                "table_id": table_num,
                "table_label": table_label,
                "table_caption": caption[:500],
                "surrounding_text": surrounding_text[:1000],
                "char_length": len(page_content),
            }

            if table_text:
                meta["table_text"] = table_text[:3500]

                m = re.search(r"(<table.*?</table>)", table_text, flags=re.S | re.I)
                if m:
                    meta["table_html"] = m.group(1).strip()

            docs.append(Document(page_content=page_content, metadata=meta))
            chunk_id += 1

        return docs

    def build_figure_chunks(
        self,
        md_content: str,
        persisted_manifest: Dict[str, Any],
        start_chunk_id: int = 300000
    ) -> List[Document]:
        docs: List[Document] = []
        chunk_id = start_chunk_id

        figure_objects = self.extract_figure_objects(md_content, persisted_manifest)

        for obj in figure_objects:
            figure_num = obj["figure_num"]
            figure_label = obj["figure_label"]
            caption = obj["caption"]
            image_paths = obj["image_paths"]
            image_paths_abs = obj["image_paths_abs"]
            image_friendly_names = obj["image_friendly_names"]
            surrounding_text = obj["surrounding_text"]

            page_content = (
                f"图片/图表块 {figure_label}\n"
                f"图标题或说明：{caption}\n"
                f"关联图片数量：{len(image_paths_abs)}\n"
                f"图片相对路径列表：{image_paths}\n"
                f"图片友好文件名列表：{image_friendly_names}\n"
                f"图片绝对路径列表：{image_paths_abs}\n"
                f"附近正文：{surrounding_text}\n"
            )

            meta = {
                "chunk_id": chunk_id,
                "block_type": "figure",
                "section": "FIGURE",
                "figure_num": figure_num,
                "figure_label": figure_label,
                "figure_caption": caption[:500],
                "surrounding_text": surrounding_text[:1000],
                "char_length": len(page_content),
                "image_count": len(image_paths_abs),
            }

            if image_paths:
                meta["image_paths"] = image_paths
            if image_paths_abs:
                meta["image_paths_abs"] = image_paths_abs
            if image_friendly_names:
                meta["image_friendly_names"] = image_friendly_names

            docs.append(Document(page_content=page_content, metadata=meta))
            chunk_id += 1

        return docs
    # ---------------------------
    # 预留VLM模型接口，用于后续接入mineru图像理解模型
    # ---------------------------
    def describe_image_with_vlm(self, image_path: str) -> str:
        """
        这里先写占位逻辑。
        后面可以接 OpenAI/Gemini/Qwen-VL 等 VLM。
        """
        return ""

    #清洗文件名，用于生成图表块的 section 字段，后续也可以用于生成更友好的 chunk_id 或者索引 key
    def _slugify_name(self, text: str, max_len: int = 80) -> str:
        text = os.path.splitext(os.path.basename(text))[0]
        text = re.sub(r"[^\w\u4e00-\u9fff\-\.]+", "-", text)
        text = re.sub(r"-{2,}", "-", text).strip("-_.")
        if not text:
            text = "document"
        return text[:max_len]

    # ---------------------------
    # 总装配
    # ---------------------------
    def build_multitype_documents(
        self,
        parse_result: MinerUParseResult,
        persisted_manifest: Dict[str, Any],
    ) -> List[Document]:
        md = parse_result.full_md

        text_docs = self.build_text_chunks(md, start_chunk_id=0)
        formula_docs = self.build_formula_chunks(md, persisted_manifest=persisted_manifest,start_chunk_id=100000)
        table_docs = self.build_table_chunks(md, persisted_manifest=persisted_manifest,start_chunk_id=200000)
        figure_docs = self.build_figure_chunks(md, persisted_manifest=persisted_manifest,start_chunk_id=300000)

        all_docs = text_docs + formula_docs + table_docs + figure_docs
        print(
            f"📚 [DEBUG] 多类型切块完成: "
            f"text={len(text_docs)}, formula={len(formula_docs)}, "
            f"table={len(table_docs)}, figure={len(figure_docs)}, total={len(all_docs)}"
        )
        return all_docs