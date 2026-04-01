from __future__ import annotations

import json
import os
import re
import sys
import time
import signal
import ipaddress
import socket
import ssl
import shutil
import zipfile
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urlparse
import requests
from urllib3.exceptions import InsecureRequestWarning

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from dotenv import load_dotenv


CONNECT_TIMEOUT_SWITCH_THRESHOLD = 3
DOWNLOAD_FAILURE_COOLDOWN_SECONDS = 1800


class MinerUConnectTimeoutBudgetExceeded(Exception):
    def __init__(self, *, proxy_mode: str, proxy_desc: str, stage: str, count: int):
        self.proxy_mode = proxy_mode
        self.proxy_desc = proxy_desc
        self.stage = stage
        self.count = count
        super().__init__(
            f"MinerU 在 {proxy_desc} 模式的 {stage} 阶段连接超时累计 {count} 次。"
        )


class MinerUDownloadNetworkBudgetExceeded(Exception):
    def __init__(self, *, proxy_mode: str, proxy_desc: str, stage: str, count: int, error_kind: str):
        self.proxy_mode = proxy_mode
        self.proxy_desc = proxy_desc
        self.stage = stage
        self.count = count
        self.error_kind = error_kind
        super().__init__(
            f"MinerU 在 {proxy_desc} 模式的 {stage} 阶段 {error_kind} 累计 {count} 次。"
        )


class MinerUTemporarilyDisabled(Exception):
    def __init__(self, *, disabled_until: int, reason: str):
        self.disabled_until = disabled_until
        self.reason = reason
        formatted_until = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(disabled_until))
        super().__init__(
            f"MinerU 因近期 CDN 下载失败已临时停用，恢复时间不早于 {formatted_until}。原因：{reason}"
        )


class KnowledgeProcessor:
    def __init__(
        self,
        api_token: str,
        *,
        proxy_mode: str = "inherit",
        http_proxy: str | None = None,
        https_proxy: str | None = None,
        connect_timeout_seconds: int = 5,
        status_file_path: str | None = None,
        public_dns_bypass_enabled: bool = True,
        public_dns_server: str = "223.5.5.5",
        public_dns_port: int = 53,
        public_dns_hosts: str = "cdn-mineru.openxlab.org.cn",
    ):
        self.api_token = api_token
        self.batch_url = "https://mineru.net/api/v4/file-urls/batch"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        self.proxy_mode = proxy_mode
        self.active_proxy_mode = proxy_mode
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy
        self.connect_timeout_seconds = connect_timeout_seconds
        self.session = requests.Session()
        self.proxy_desc = ""
        self.status_file_path = Path(status_file_path) if status_file_path else None
        self.public_dns_bypass_enabled = public_dns_bypass_enabled
        self.public_dns_server = public_dns_server
        self.public_dns_port = public_dns_port
        self.public_dns_hosts = {
            host.strip().lower()
            for host in re.split(r"[,\s]+", public_dns_hosts or "")
            if host.strip()
        }

        self._set_session(proxy_mode, announce=True)

    def _load_status(self) -> dict:
        if self.status_file_path is None or not self.status_file_path.exists():
            return {}
        try:
            with self.status_file_path.open("r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
                if isinstance(payload, dict):
                    return payload
        except Exception:
            pass
        return {}

    def _save_status(self, payload: dict) -> None:
        if self.status_file_path is None:
            return
        try:
            self.status_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.status_file_path.open("w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _clear_status(self) -> None:
        if self.status_file_path is None:
            return
        try:
            self.status_file_path.unlink(missing_ok=True)
        except Exception:
            pass

    def _check_temporary_disable(self) -> None:
        payload = self._load_status()
        disabled_until = int(payload.get("disabled_until") or 0)
        if disabled_until <= 0:
            return
        if disabled_until <= int(time.time()):
            self._clear_status()
            return
        reason = str(payload.get("reason") or "recent CDN download failures")
        raise MinerUTemporarilyDisabled(disabled_until=disabled_until, reason=reason)

    def _disable_temporarily(self, reason: str, *, cooldown_seconds: int = DOWNLOAD_FAILURE_COOLDOWN_SECONDS) -> None:
        disabled_until = int(time.time()) + int(cooldown_seconds)
        self._save_status(
            {
                "disabled_until": disabled_until,
                "reason": reason,
                "cooldown_seconds": int(cooldown_seconds),
            }
        )
        formatted_until = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(disabled_until))
        print(f"⚠️ [MinerU] 已临时停用云端解析，恢复时间不早于 {formatted_until}。原因: {reason}")

    def _should_try_public_dns_bypass(self, hostname: str) -> bool:
        return bool(
            self.public_dns_bypass_enabled
            and hostname
            and hostname.lower() in self.public_dns_hosts
        )

    def _is_usable_public_ipv4(self, ip_text: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip_text)
        except ValueError:
            return False

        fake_ip_range = ipaddress.ip_network("198.18.0.0/15")
        return bool(
            ip_obj.version == 4
            and ip_obj not in fake_ip_range
            and not ip_obj.is_private
            and not ip_obj.is_loopback
            and not ip_obj.is_link_local
            and not ip_obj.is_multicast
            and not ip_obj.is_reserved
            and not ip_obj.is_unspecified
        )

    def _public_doh_candidates(self, hostname: str) -> list[tuple[str, str]]:
        primary = (self.public_dns_server or "").strip().lower()
        candidates: list[tuple[str, str]] = []

        def _append(label: str, url: str) -> None:
            if url not in {candidate_url for _, candidate_url in candidates}:
                candidates.append((label, url))

        if primary in {"223.5.5.5", "dns.alidns.com", "alidns"}:
            _append("AliDNS", f"https://223.5.5.5/resolve?name={hostname}&type=A")
        elif primary in {"1.1.1.1", "cloudflare-dns.com", "cloudflare"}:
            _append("Cloudflare DoH", f"https://1.1.1.1/dns-query?name={hostname}&type=A")
        elif primary:
            _append("Configured DoH /resolve", f"https://{primary}/resolve?name={hostname}&type=A")
            _append("Configured DoH /dns-query", f"https://{primary}/dns-query?name={hostname}&type=A")

        _append("AliDNS", f"https://223.5.5.5/resolve?name={hostname}&type=A")
        _append("Cloudflare DoH", f"https://1.1.1.1/dns-query?name={hostname}&type=A")
        return candidates

    def _request_public_doh_json(self, url: str, label: str) -> dict:
        last_error: Exception | None = None
        session_attempts = [
            ("代理/环境网络", self._create_session("inherit")[0]),
            ("直连网络", self._create_session("direct")[0]),
        ]

        for mode_label, session in session_attempts:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", InsecureRequestWarning)
                    response = session.get(
                        url,
                        headers={"accept": "application/dns-json"},
                        timeout=(self.connect_timeout_seconds, 12),
                        verify=False,
                    )
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
                raise RuntimeError("DoH endpoint returned non-JSON payload")
            except Exception as exc:
                last_error = exc
                print(f"   ⚠️ 公共 DoH 查询失败: {label} ({mode_label}): {exc}")

        raise RuntimeError(f"public DoH query failed for {label}: {last_error}")

    def _resolve_hostname_via_public_dns(self, hostname: str) -> list[str]:
        collected: list[str] = []
        seen: set[str] = set()

        for label, url in self._public_doh_candidates(hostname):
            try:
                payload = self._request_public_doh_json(url, label)
            except Exception as exc:
                print(f"   ⚠️ 公共 DoH 提供方不可用: {label}: {exc}")
                continue

            answers = payload.get("Answer") or []
            candidate_ips = [
                str(item.get("data", "")).strip()
                for item in answers
                if isinstance(item, dict) and int(item.get("type") or 0) == 1
            ]

            usable_ips = [
                ip_text
                for ip_text in candidate_ips
                if ip_text and self._is_usable_public_ipv4(ip_text)
            ]
            ignored_ips = [ip_text for ip_text in candidate_ips if ip_text and ip_text not in usable_ips]
            if ignored_ips:
                print(f"   ⚠️ 公共 DoH 返回了不可用地址，已忽略: {', '.join(ignored_ips[:4])}")

            for ip_text in usable_ips:
                if ip_text not in seen:
                    seen.add(ip_text)
                    collected.append(ip_text)

            if collected:
                return collected

        return collected

    def _decode_chunked_http_body(self, body: bytes) -> bytes:
        decoded = bytearray()
        cursor = 0
        while True:
            line_end = body.find(b"\r\n", cursor)
            if line_end < 0:
                raise RuntimeError("invalid chunked HTTP response")
            chunk_size_line = body[cursor:line_end].split(b";", 1)[0]
            chunk_size = int(chunk_size_line.decode("ascii"), 16)
            cursor = line_end + 2
            if chunk_size == 0:
                return bytes(decoded)
            decoded.extend(body[cursor : cursor + chunk_size])
            cursor += chunk_size + 2

    def _https_get_via_ip(self, ip_address: str, hostname: str, path_with_query: str) -> bytes:
        request_bytes = (
            f"GET {path_with_query} HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            "User-Agent: ai-tutor-agent/mineru-dns-bypass\r\n"
            "Connection: close\r\n\r\n"
        ).encode("utf-8")

        context = ssl.create_default_context()
        with socket.create_connection((ip_address, 443), timeout=15) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=hostname) as tls_sock:
                tls_sock.settimeout(15)
                tls_sock.sendall(request_bytes)
                chunks: list[bytes] = []
                while True:
                    chunk = tls_sock.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)

        response = b"".join(chunks)
        header_bytes, _, body = response.partition(b"\r\n\r\n")
        if not header_bytes:
            raise RuntimeError("empty HTTPS response from CDN")
        header_lines = header_bytes.decode("iso-8859-1").split("\r\n")
        status_parts = header_lines[0].split(" ", 2)
        if len(status_parts) < 2:
            raise RuntimeError(f"invalid HTTP status line: {header_lines[0]!r}")
        status_code = int(status_parts[1])
        headers: dict[str, str] = {}
        for line in header_lines[1:]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        if 300 <= status_code < 400 and headers.get("location"):
            raise RuntimeError(f"unexpected CDN redirect to {headers['location']}")
        if status_code >= 400:
            raise RuntimeError(f"CDN HTTP {status_code}")
        if headers.get("transfer-encoding", "").lower() == "chunked":
            return self._decode_chunked_http_body(body)
        return body

    def _requests_get_via_ip(self, ip_address: str, hostname: str, path_with_query: str, *, mode: str) -> bytes:
        session, _ = self._create_session(mode)
        url = f"https://{ip_address}{path_with_query}"
        headers = {
            "Host": hostname,
            "User-Agent": "ai-tutor-agent/mineru-dns-bypass",
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            response = session.get(
                url,
                headers=headers,
                timeout=(self.connect_timeout_seconds, 30),
                verify=False,
            )
        response.raise_for_status()
        return response.content

    def _download_bytes_via_public_dns(self, full_zip_url: str) -> bytes:
        parsed = urlparse(full_zip_url)
        hostname = (parsed.hostname or "").strip()
        if not hostname:
            raise RuntimeError("missing hostname in MinerU CDN url")
        if parsed.scheme != "https":
            raise RuntimeError(f"unsupported MinerU CDN scheme: {parsed.scheme}")

        path_with_query = parsed.path or "/"
        if parsed.query:
            path_with_query = f"{path_with_query}?{parsed.query}"

        ip_addresses = self._resolve_hostname_via_public_dns(hostname)
        if not ip_addresses:
            raise RuntimeError(f"public DNS did not return IPv4 addresses for {hostname}")

        last_error: Exception | None = None
        for ip_address in ip_addresses[:3]:
            attempt_handlers = [
                ("继承代理/IP URL", lambda: self._requests_get_via_ip(ip_address, hostname, path_with_query, mode="inherit")),
                ("直连/IP URL", lambda: self._requests_get_via_ip(ip_address, hostname, path_with_query, mode="direct")),
                ("直连/IP+SNI", lambda: self._https_get_via_ip(ip_address, hostname, path_with_query)),
            ]
            for attempt_label, loader in attempt_handlers:
                try:
                    body = loader()
                    print(f"   ✅ 公共 DNS 绕过下载成功: {hostname} -> {ip_address} ({attempt_label})")
                    return body
                except Exception as exc:
                    last_error = exc
                    print(f"   ⚠️ 公共 DNS 绕过下载失败: {hostname} -> {ip_address} ({attempt_label}): {exc}")

        raise RuntimeError(
            f"public DNS bypass failed for {hostname}: {last_error or 'no reachable IPs'}"
        )

    def _create_session(self, proxy_mode: str) -> tuple[requests.Session, str]:
        session = requests.Session()

        if proxy_mode == "direct":
            session.trust_env = False
            proxy_desc = "直连"
        elif self.http_proxy or self.https_proxy:
            session.trust_env = False
            if self.http_proxy:
                session.proxies["http"] = self.http_proxy
            if self.https_proxy:
                session.proxies["https"] = self.https_proxy
            proxy_desc = f"专用代理 http={self.http_proxy or '-'} https={self.https_proxy or '-'}"
        else:
            session.trust_env = True
            proxy_desc = "继承环境变量 HTTP_PROXY / HTTPS_PROXY"

        return session, proxy_desc

    def _set_session(self, proxy_mode: str, *, announce: bool) -> None:
        self.session, self.proxy_desc = self._create_session(proxy_mode)
        self.active_proxy_mode = proxy_mode

        if announce:
            self._log_network_config()

    def _log_network_config(self) -> None:
        print(f"🛠️ MinerU 网络模式: {self.proxy_desc}")
        print(f"🛠️ MinerU 连接超时: {self.connect_timeout_seconds}s")

    def parse_pdf_to_md(self, local_path: str) -> str:
        """
        使用 MinerU Token + 本地文件上传方式解析 PDF，并返回 full.md 的文本内容
        """
        load_dotenv()
        self._check_temporary_disable()

        token = os.getenv("MINERU_API_TOKEN") or self.api_token
        if not token:
            raise ValueError("❌ 错误：未在 .env 文件中找到 MINERU_API_TOKEN，且未传入 api_token。")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"❌ 文件不存在: {local_path}")

        file_name = os.path.basename(local_path)
        file_size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"📄 [任务] 准备解析本地文件: {file_name} ({file_size_mb:.2f} MB)")

        modes_to_try = [self.active_proxy_mode]
        if self.active_proxy_mode != "direct":
            modes_to_try.append("direct")

        last_timeout_error: MinerUConnectTimeoutBudgetExceeded | None = None

        for mode in modes_to_try:
            if mode != self.active_proxy_mode:
                print("⚠️ [MinerU] 当前网络模式连接超时累计 3 次，自动切换为直连 direct 重试。")
                self._set_session("direct", announce=True)

            try:
                markdown_content = self._parse_pdf_to_md_once(local_path, token=token, file_name=file_name)
                self._clear_status()
                return markdown_content
            except MinerUConnectTimeoutBudgetExceeded as exc:
                last_timeout_error = exc
                if mode == "direct":
                    raise Exception(
                        "⏱️ MinerU 在直连模式下连接超时累计 3 次，停止云端解析。"
                    ) from exc

        if last_timeout_error is not None:
            raise Exception(str(last_timeout_error)) from last_timeout_error

        raise RuntimeError("MinerU 解析未执行。")

    def _parse_pdf_to_md_once(self, local_path: str, *, token: str, file_name: str) -> str:
        BASE_URL = "https://mineru.net/api/v4"
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        connect_timeout_count = 0

        def _record_connect_timeout(stage: str, exc: Exception) -> None:
            nonlocal connect_timeout_count

            connect_timeout_count += 1
            print(
                f"   ⚠️ {stage} 发生连接超时，当前模式 {self.proxy_desc} "
                f"({connect_timeout_count}/{CONNECT_TIMEOUT_SWITCH_THRESHOLD})。"
            )
            if connect_timeout_count >= CONNECT_TIMEOUT_SWITCH_THRESHOLD:
                raise MinerUConnectTimeoutBudgetExceeded(
                    proxy_mode=self.active_proxy_mode,
                    proxy_desc=self.proxy_desc,
                    stage=stage,
                    count=connect_timeout_count,
                ) from exc
            time.sleep(1)

        def _download_and_extract_markdown(full_zip_url: str) -> str:
            """
            下载 MinerU 返回的 zip 结果包，解压并读取 full.md
            """
            temp_dir = tempfile.mkdtemp(prefix="mineru_")
            zip_path = os.path.join(temp_dir, "result.zip")
            network_failure_count = 0
            zip_bytes: bytes | None = None
            parsed = urlparse(full_zip_url)
            hostname = (parsed.hostname or "").strip()

            try:
                print("📥 [Step 4] 正在下载解析结果压缩包...")
                while True:
                    try:
                        resp_zip = self.session.get(full_zip_url, timeout=120)
                        resp_zip.raise_for_status()
                        zip_bytes = resp_zip.content
                        break
                    except requests.exceptions.ConnectTimeout as exc:
                        _record_connect_timeout("下载解析结果", exc)
                    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
                        error_kind = "SSL/连接异常"
                        network_failure_count += 1
                        print(
                            f"   ⚠️ 下载解析结果发生{error_kind}，当前模式 {self.proxy_desc} "
                            f"({network_failure_count}/{CONNECT_TIMEOUT_SWITCH_THRESHOLD})。"
                        )
                        if network_failure_count >= CONNECT_TIMEOUT_SWITCH_THRESHOLD:
                            if self.active_proxy_mode != "direct":
                                print("   ⚠️ 下载解析结果连续失败 3 次，自动切换为直连 direct 重试。")
                                self._set_session("direct", announce=True)
                                network_failure_count = 0
                                continue
                            if self._should_try_public_dns_bypass(hostname):
                                print(
                                    "   ⚠️ 检测到可能的 WSL fake-ip / DNS 干扰，"
                                    "尝试通过项目内公共 DNS 解析真实地址直连下载。"
                                )
                                try:
                                    zip_bytes = self._download_bytes_via_public_dns(full_zip_url)
                                    break
                                except Exception as bypass_exc:
                                    print(f"   ❌ 公共 DNS 直连下载仍然失败: {bypass_exc}")
                            self._disable_temporarily(
                                "cdn-mineru.openxlab.org.cn 在代理和直连模式下都发生 SSL/连接异常"
                            )
                            raise MinerUDownloadNetworkBudgetExceeded(
                                proxy_mode=self.active_proxy_mode,
                                proxy_desc=self.proxy_desc,
                                stage="下载解析结果",
                                count=network_failure_count,
                                error_kind=error_kind,
                            ) from exc
                        time.sleep(1)

                if zip_bytes is None:
                    raise RuntimeError("MinerU zip download returned empty content")

                with open(zip_path, "wb") as f:
                    f.write(zip_bytes)

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
                while True:
                    try:
                        resp_apply = self.session.post(
                            apply_url,
                            headers=HEADERS,
                            json=payload,
                            timeout=(self.connect_timeout_seconds, 30),
                        )
                        resp_apply.raise_for_status()
                        result_apply = resp_apply.json()
                        break
                    except requests.exceptions.ConnectTimeout as exc:
                        _record_connect_timeout("申请上传链接", exc)
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

            print("📤 [Step 2] 正在上传文件到云端 (请勿关闭)...")

            try:
                while True:
                    try:
                        with open(local_path, "rb") as f:
                            resp_upload = self.session.put(upload_url, data=f, timeout=300)
                            resp_upload.raise_for_status()
                            break
                    except requests.exceptions.ConnectTimeout as exc:
                        _record_connect_timeout("上传文件", exc)
            except requests.exceptions.Timeout:
                raise Exception("⏱️ 文件上传超时，请检查网络后重试。")
            except requests.exceptions.RequestException as e:
                raise Exception(f"❌ 文件上传失败: {e}")

            print("✅ [Step 2] 文件上传成功！系统已自动提交解析任务。")

            print("⏳ [Step 3] 等待云端解析完成 (通常需 10-60 秒)...")
            print("💡 提示：按 Ctrl+C 可随时安全终止任务。")

            max_wait_time = 600
            start_time = time.time()
            poll_interval = 10

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
                    resp_query = self.session.get(
                        query_url,
                        headers=HEADERS,
                        timeout=(self.connect_timeout_seconds, 15),
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

                    if state == "failed":
                        raise Exception(f"❌ 云端解析失败: {err_msg or '未知错误'}")

                    if state in ["waiting-file", "pending", "running", "converting"]:
                        pass
                    else:
                        print(f"   ❓ 遇到未知状态: {state}")

                except requests.exceptions.ConnectTimeout as exc:
                    _record_connect_timeout("查询解析状态", exc)
                except requests.exceptions.Timeout:
                    print(f"   ⚠️ 查询请求超时 (>15s)，重试中... ({elapsed}s)")
                except KeyboardInterrupt:
                    print("\n⚠️ 检测到中断信号，停止当前解析任务。")
                    raise
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
        # 第一步：按 Markdown 标题切
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
        )
        header_docs = header_splitter.split_text(md_content)

        # 第二步：再按长度细切，避免单块过长
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )

        final_docs = []
        chunk_id = 0

        for doc in header_docs:
            content = (doc.page_content or "").strip()
            if not content:
                continue

            base_meta = dict(doc.metadata) if doc.metadata else {}

            # 尝试抽取 section
            # 🔥 提取 section（统一字段）
            section = (
                base_meta.get("H3")
                or base_meta.get("H2")
                or base_meta.get("H1")
                or "UNKNOWN"
            )
            # 太长的块继续切
            sub_docs = text_splitter.split_text(content)

            for chunk in sub_docs:
                chunk = chunk.strip()
                if not chunk:
                    continue

                meta = dict(base_meta)
                meta["chunk_id"] = chunk_id
                meta["section"] = section
                meta["char_length"] = len(chunk)

                final_docs.append(
                    Document(
                        page_content=chunk,
                        metadata=meta
                    )
                )
                chunk_id += 1

        return final_docs
