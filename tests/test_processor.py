import os
import time
from io import BytesIO
import zipfile

import pytest
import requests

from ai_tutor_agent.infrastructure.processor import (
    KnowledgeProcessor,
    MinerUConnectTimeoutBudgetExceeded,
    MinerUDownloadNetworkBudgetExceeded,
    MinerUTemporarilyDisabled,
)


def test_mineru_processor_inherits_environment_proxy_by_default():
    processor = KnowledgeProcessor(api_token="token-demo")

    assert processor.session.trust_env is True
    assert processor.session.proxies == {}


def test_mineru_processor_can_use_dedicated_proxy():
    processor = KnowledgeProcessor(
        api_token="token-demo",
        http_proxy="http://127.0.0.1:7897",
        https_proxy="http://127.0.0.1:7897",
    )

    assert processor.session.trust_env is False
    assert processor.session.proxies["http"] == "http://127.0.0.1:7897"
    assert processor.session.proxies["https"] == "http://127.0.0.1:7897"


def test_mineru_processor_can_force_direct_connection():
    processor = KnowledgeProcessor(
        api_token="token-demo",
        proxy_mode="direct",
        http_proxy="http://127.0.0.1:7897",
        https_proxy="http://127.0.0.1:7897",
    )

    assert processor.session.trust_env is False
    assert processor.session.proxies == {}


def test_mineru_processor_switches_to_direct_after_connect_timeout_budget(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    processor = KnowledgeProcessor(api_token="token-demo")
    attempts = []

    def fake_parse_once(local_path, *, token, file_name):
        attempts.append(processor.active_proxy_mode)
        assert local_path == str(pdf)
        assert token == (os.getenv("MINERU_API_TOKEN") or "token-demo")
        assert file_name == "sample.pdf"
        if processor.active_proxy_mode != "direct":
            raise MinerUConnectTimeoutBudgetExceeded(
                proxy_mode=processor.active_proxy_mode,
                proxy_desc=processor.proxy_desc,
                stage="申请上传链接",
                count=3,
            )
        return "# parsed"

    monkeypatch.setattr(processor, "_parse_pdf_to_md_once", fake_parse_once)

    result = processor.parse_pdf_to_md(str(pdf))

    assert result == "# parsed"
    assert attempts == ["inherit", "direct"]
    assert processor.active_proxy_mode == "direct"
    assert processor.session.trust_env is False


def test_mineru_processor_raises_after_direct_timeout_budget_exhausted(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    processor = KnowledgeProcessor(api_token="token-demo", proxy_mode="direct")

    def fake_parse_once(local_path, *, token, file_name):
        del local_path, token, file_name
        raise MinerUConnectTimeoutBudgetExceeded(
            proxy_mode=processor.active_proxy_mode,
            proxy_desc=processor.proxy_desc,
            stage="申请上传链接",
            count=3,
        )

    monkeypatch.setattr(processor, "_parse_pdf_to_md_once", fake_parse_once)

    with pytest.raises(Exception, match="直连模式下连接超时累计 3 次"):
        processor.parse_pdf_to_md(str(pdf))


def _build_zip_bytes(markdown: str) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("full.md", markdown)
    return buffer.getvalue()


class _FakeResponse:
    def __init__(self, *, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class _FakeMinerUSession:
    def __init__(self, *, processor, mode: str, zip_bytes: bytes, download_failures_before_success: int):
        self.processor = processor
        self.mode = mode
        self.zip_bytes = zip_bytes
        self.download_failures_before_success = download_failures_before_success
        self.download_attempts = 0
        self.trust_env = mode != "direct"
        self.proxies = {}

    def post(self, url, headers=None, json=None, timeout=None):
        del headers, json, timeout
        assert url.endswith("/file-urls/batch")
        return _FakeResponse(
            json_data={
                "code": 0,
                "data": {
                    "batch_id": "batch-123",
                    "file_urls": ["https://upload.example.com/file"],
                },
            }
        )

    def put(self, url, data=None, timeout=None):
        del data, timeout
        assert url == "https://upload.example.com/file"
        return _FakeResponse(status_code=200)

    def get(self, url, headers=None, timeout=None):
        del headers, timeout
        if url.endswith("/extract-results/batch/batch-123"):
            return _FakeResponse(
                json_data={
                    "code": 0,
                    "data": {
                        "extract_result": {
                            "state": "done",
                            "full_zip_url": "https://cdn-mineru.openxlab.org.cn/result.zip",
                        }
                    },
                }
            )

        if url == "https://cdn-mineru.openxlab.org.cn/result.zip":
            self.download_attempts += 1
            if self.download_attempts <= self.download_failures_before_success:
                raise requests.exceptions.SSLError("TLS EOF")
            return _FakeResponse(content=self.zip_bytes)

        raise AssertionError(f"unexpected GET url: {url}")


def test_mineru_processor_step4_switches_to_direct_after_ssl_retry_budget(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    status_file = tmp_path / "mineru_runtime_state.json"
    processor = KnowledgeProcessor(api_token="token-demo", status_file_path=str(status_file))
    zip_bytes = _build_zip_bytes("# parsed-from-mineru")
    sessions: dict[str, _FakeMinerUSession] = {}

    def fake_create_session(mode: str):
        session = sessions.setdefault(
            mode,
            _FakeMinerUSession(
                processor=processor,
                mode=mode,
                zip_bytes=zip_bytes,
                download_failures_before_success=3 if mode != "direct" else 0,
            ),
        )
        proxy_desc = "直连" if mode == "direct" else "继承环境变量 HTTP_PROXY / HTTPS_PROXY"
        return session, proxy_desc

    monkeypatch.setattr(processor, "_create_session", fake_create_session)
    monkeypatch.setattr("ai_tutor_agent.infrastructure.processor.time.sleep", lambda _: None)
    processor.session, processor.proxy_desc = fake_create_session("inherit")
    processor.active_proxy_mode = "inherit"

    result = processor.parse_pdf_to_md(str(pdf))

    assert result == "# parsed-from-mineru"
    assert sessions["inherit"].download_attempts == 3
    assert sessions["direct"].download_attempts == 1
    assert processor.active_proxy_mode == "direct"
    assert not status_file.exists()


def test_mineru_processor_step4_raises_after_direct_ssl_retry_budget_exhausted(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    status_file = tmp_path / "mineru_runtime_state.json"
    processor = KnowledgeProcessor(api_token="token-demo", status_file_path=str(status_file))
    zip_bytes = _build_zip_bytes("# parsed-from-mineru")
    sessions: dict[str, _FakeMinerUSession] = {}

    def fake_create_session(mode: str):
        session = sessions.setdefault(
            mode,
            _FakeMinerUSession(
                processor=processor,
                mode=mode,
                zip_bytes=zip_bytes,
                download_failures_before_success=99,
            ),
        )
        proxy_desc = "直连" if mode == "direct" else "继承环境变量 HTTP_PROXY / HTTPS_PROXY"
        return session, proxy_desc

    monkeypatch.setattr(processor, "_create_session", fake_create_session)
    monkeypatch.setattr("ai_tutor_agent.infrastructure.processor.time.sleep", lambda _: None)
    processor.session, processor.proxy_desc = fake_create_session("inherit")
    processor.active_proxy_mode = "inherit"

    with pytest.raises(MinerUDownloadNetworkBudgetExceeded, match="下载解析结果.*SSL/连接异常.*累计 3 次"):
        processor.parse_pdf_to_md(str(pdf))

    assert sessions["inherit"].download_attempts == 3
    assert sessions["direct"].download_attempts == 3
    assert processor.active_proxy_mode == "direct"
    assert status_file.exists()


def test_mineru_processor_uses_public_dns_bypass_after_direct_ssl_failures(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    status_file = tmp_path / "mineru_runtime_state.json"
    processor = KnowledgeProcessor(
        api_token="token-demo",
        status_file_path=str(status_file),
        public_dns_bypass_enabled=True,
        public_dns_hosts="cdn-mineru.openxlab.org.cn",
    )
    zip_bytes = _build_zip_bytes("# parsed-via-public-dns")
    sessions: dict[str, _FakeMinerUSession] = {}
    bypass_calls: list[str] = []

    def fake_create_session(mode: str):
        session = sessions.setdefault(
            mode,
            _FakeMinerUSession(
                processor=processor,
                mode=mode,
                zip_bytes=zip_bytes,
                download_failures_before_success=99,
            ),
        )
        proxy_desc = "直连" if mode == "direct" else "继承环境变量 HTTP_PROXY / HTTPS_PROXY"
        return session, proxy_desc

    monkeypatch.setattr(processor, "_create_session", fake_create_session)
    monkeypatch.setattr("ai_tutor_agent.infrastructure.processor.time.sleep", lambda _: None)
    monkeypatch.setattr(
        processor,
        "_download_bytes_via_public_dns",
        lambda url: bypass_calls.append(url) or zip_bytes,
    )
    processor.session, processor.proxy_desc = fake_create_session("inherit")
    processor.active_proxy_mode = "inherit"

    result = processor.parse_pdf_to_md(str(pdf))

    assert result == "# parsed-via-public-dns"
    assert sessions["inherit"].download_attempts == 3
    assert sessions["direct"].download_attempts == 3
    assert bypass_calls == ["https://cdn-mineru.openxlab.org.cn/result.zip"]
    assert not status_file.exists()


def test_mineru_processor_public_doh_ignores_fake_ip_answers(monkeypatch):
    processor = KnowledgeProcessor(
        api_token="token-demo",
        public_dns_bypass_enabled=True,
        public_dns_hosts="cdn-mineru.openxlab.org.cn",
    )
    calls: list[str] = []

    def fake_request_public_doh_json(url: str, label: str) -> dict:
        calls.append(label)
        if "223.5.5.5" in url:
            return {
                "Answer": [
                    {"type": 1, "data": "198.18.2.45"},
                    {"type": 1, "data": "58.205.221.44"},
                ]
            }
        return {"Answer": [{"type": 1, "data": "47.251.5.11"}]}

    monkeypatch.setattr(processor, "_request_public_doh_json", fake_request_public_doh_json)

    result = processor._resolve_hostname_via_public_dns("cdn-mineru.openxlab.org.cn")

    assert result == ["58.205.221.44"]
    assert calls == ["AliDNS"]


def test_mineru_processor_skips_cloud_parse_during_cooldown_window(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    status_file = tmp_path / "mineru_runtime_state.json"
    disabled_until = int(time.time()) + 120
    status_file.write_text(
        '{"disabled_until": %d, "reason": "cdn download failed"}' % disabled_until,
        encoding="utf-8",
    )
    processor = KnowledgeProcessor(api_token="token-demo", status_file_path=str(status_file))

    with pytest.raises(MinerUTemporarilyDisabled, match="临时停用"):
        processor.parse_pdf_to_md(str(pdf))
