import os
import shutil
import tempfile
import time
import zipfile

import requests
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class KnowledgeProcessor:
    """Optional MinerU-based PDF parser for higher quality markdown extraction."""

    def __init__(self, api_token: str | None):
        self.api_token = api_token
        self.session = requests.Session()
        # Keep this client independent from shell proxy by default.
        self.session.trust_env = False

    def parse_pdf_to_md(self, local_path: str) -> str:
        token = self.api_token or os.getenv("MINERU_API_TOKEN", "").strip()
        if not token:
            raise ValueError("MINERU_API_TOKEN is required for MinerU parsing.")
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        base_url = "https://mineru.net/api/v4"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        file_name = os.path.basename(local_path)
        data_id = f"local_{int(time.time())}_{file_name}"

        apply_resp = self.session.post(
            f"{base_url}/file-urls/batch",
            headers=headers,
            json={"files": [{"name": file_name, "data_id": data_id}], "model_version": "vlm"},
            timeout=30,
        )
        apply_resp.raise_for_status()
        apply_data = apply_resp.json()
        if apply_data.get("code") != 0:
            raise RuntimeError(f"MinerU apply upload URL failed: {apply_data.get('msg', 'unknown')}")

        payload = apply_data.get("data") or {}
        batch_id = payload.get("batch_id")
        file_urls = payload.get("file_urls") or []
        if not batch_id or not file_urls:
            raise RuntimeError("MinerU response missing batch_id or file_urls.")

        with open(local_path, "rb") as src:
            upload_resp = self.session.put(file_urls[0], data=src, timeout=300)
            upload_resp.raise_for_status()

        result_url = self._poll_extract_result(base_url=base_url, headers=headers, batch_id=batch_id, file_name=file_name)
        return self._download_and_extract_markdown(result_url)

    def _poll_extract_result(self, *, base_url: str, headers: dict[str, str], batch_id: str, file_name: str) -> str:
        started = time.time()
        timeout_seconds = 600

        while True:
            if time.time() - started > timeout_seconds:
                raise TimeoutError(f"MinerU extraction timed out for batch: {batch_id}")

            resp = self.session.get(f"{base_url}/extract-results/batch/{batch_id}", headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                time.sleep(10)
                continue

            task = self._normalize_extract_result(data.get("data") or {}, file_name)
            state = task.get("state")

            if state == "done":
                full_zip_url = task.get("full_zip_url")
                if not full_zip_url:
                    raise RuntimeError("MinerU extraction completed but full_zip_url missing.")
                return full_zip_url

            if state == "failed":
                raise RuntimeError(f"MinerU extraction failed: {task.get('err_msg', 'unknown')}")

            time.sleep(10)

    @staticmethod
    def _normalize_extract_result(data_obj: dict, expected_file_name: str) -> dict:
        extract_result = data_obj.get("extract_result", {})

        if isinstance(extract_result, dict):
            return extract_result

        if isinstance(extract_result, list):
            for item in extract_result:
                if isinstance(item, dict) and item.get("file_name") == expected_file_name:
                    return item
            for item in extract_result:
                if isinstance(item, dict):
                    return item

        return {}

    def _download_and_extract_markdown(self, full_zip_url: str) -> str:
        temp_dir = tempfile.mkdtemp(prefix="mineru_")
        zip_path = os.path.join(temp_dir, "result.zip")

        try:
            resp = self.session.get(full_zip_url, timeout=120)
            resp.raise_for_status()
            with open(zip_path, "wb") as dst:
                dst.write(resp.content)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            for root, _, files in os.walk(temp_dir):
                for name in files:
                    if name == "full.md":
                        with open(os.path.join(root, name), "r", encoding="utf-8") as md_file:
                            return md_file.read()

            raise FileNotFoundError("full.md not found in MinerU archive.")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def split_by_semantics(self, md_content: str) -> list[Document]:
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
        )
        header_docs = header_splitter.split_text(md_content)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )

        docs: list[Document] = []
        chunk_id = 0
        for section_doc in header_docs:
            content = (section_doc.page_content or "").strip()
            if not content:
                continue

            base_meta = dict(section_doc.metadata or {})
            section = base_meta.get("H3") or base_meta.get("H2") or base_meta.get("H1") or "UNKNOWN"

            for chunk in text_splitter.split_text(content):
                chunk = chunk.strip()
                if not chunk:
                    continue
                meta = dict(base_meta)
                meta["chunk_id"] = chunk_id
                meta["section"] = section
                meta["char_length"] = len(chunk)
                docs.append(Document(page_content=chunk, metadata=meta))
                chunk_id += 1

        return docs
