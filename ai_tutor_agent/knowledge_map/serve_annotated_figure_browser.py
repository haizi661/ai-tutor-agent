from __future__ import annotations

import argparse
import json
import mimetypes
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from ai_tutor_agent.knowledge_map.runtime_defaults import DEFAULT_MEDIA_EVIDENCE_INDEX_DIR
from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8011


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a lightweight browser for annotated figure assets.")
    parser.add_argument(
        "--index-root",
        type=str,
        default=DEFAULT_MEDIA_EVIDENCE_INDEX_DIR,
        help="Directory that contains *_annotated_assets.jsonl chapter files, or one chapter jsonl file.",
    )
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind.")
    parser.add_argument("--asset-type", type=str, default="figure", help="Default asset_type filter.")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    index_root, initial_chapter_key = resolve_index_root(args.index_root)
    catalog = discover_catalog(index_root)
    if not catalog:
        raise FileNotFoundError(f"No annotated chapter files found under: {index_root}")

    if not initial_chapter_key or initial_chapter_key not in catalog:
        initial_chapter_key = next(iter(catalog))

    server = ThreadingHTTPServer(
        (args.host, args.port),
        build_handler(index_root, default_asset_type=args.asset_type, initial_chapter_key=initial_chapter_key),
    )
    print(
        json.dumps(
            {
                "status": "serving",
                "url": f"http://{args.host}:{args.port}",
                "index_root": project_relative_path(index_root),
                "initial_chapter_key": initial_chapter_key,
                "chapter_count": len(catalog),
                "asset_type": args.asset_type,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def resolve_index_root(raw_path: str) -> tuple[Path, str]:
    resolved = resolve_project_path(raw_path)
    if resolved.is_file():
        chapter_key = resolved.name.split("_annotated_assets.jsonl", 1)[0]
        return resolved.parent, chapter_key
    if resolved.is_dir():
        return resolved, ""
    raise FileNotFoundError(f"Annotated asset root not found: {resolved}")


def build_handler(index_root: Path, *, default_asset_type: str, initial_chapter_key: str) -> type[BaseHTTPRequestHandler]:
    class AnnotatedFigureBrowserHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_html(render_app_html(default_asset_type=default_asset_type, initial_chapter_key=initial_chapter_key))
                return
            if parsed.path == "/api/catalog":
                self._handle_catalog_api()
                return
            if parsed.path == "/api/asset":
                self._handle_asset_api(parsed.query)
                return
            if parsed.path == "/api/image":
                self._handle_image_api(parsed.query)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _handle_catalog_api(self) -> None:
            try:
                payload = build_catalog_payload(index_root, initial_chapter_key=initial_chapter_key)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json(payload)

        def _handle_asset_api(self, query: str) -> None:
            try:
                params = parse_qs(query)
                chapter_key = first_param(params, "chapter_key", initial_chapter_key).strip()
                asset_type = first_param(params, "asset_type", default_asset_type).strip()
                caption_contains = first_param(params, "caption_contains", "").strip()
                position = max(1, int(first_param(params, "position", "1")))
                payload = build_asset_payload(
                    index_root=index_root,
                    chapter_key=chapter_key,
                    position=position,
                    asset_type=asset_type,
                    caption_contains=caption_contains,
                )
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json(payload)

        def _handle_image_api(self, query: str) -> None:
            try:
                params = parse_qs(query)
                chapter_key = first_param(params, "chapter_key", initial_chapter_key).strip()
                asset_type = first_param(params, "asset_type", default_asset_type).strip()
                caption_contains = first_param(params, "caption_contains", "").strip()
                position = max(1, int(first_param(params, "position", "1")))
                chapter_path = get_chapter_path(index_root, chapter_key)
                record, total = select_record(
                    load_jsonl(chapter_path),
                    position=position,
                    asset_type=asset_type,
                    caption_contains=caption_contains,
                )
                source_path = Path(str(record.get("source_path", "")).strip())
                if not source_path.exists():
                    raise FileNotFoundError(
                        f"Image file not found for {chapter_key} position {position}/{total}: {source_path}"
                    )
            except Exception as exc:
                self._send_text(str(exc), status=HTTPStatus.BAD_REQUEST)
                return

            mime_type = mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"
            data = source_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_html(self, payload: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_text(self, payload: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

    return AnnotatedFigureBrowserHandler


def discover_catalog(index_root: Path) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    summary_path = index_root / "batch_summary.json"
    if summary_path.exists():
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        chapters = payload.get("chapters", []) if isinstance(payload, dict) else []
        if isinstance(chapters, list):
            for item in chapters:
                if not isinstance(item, dict):
                    continue
                chapter_key = str(item.get("chapter_key", "")).strip()
                annotated_path = str(item.get("annotated_path", "")).strip()
                if not chapter_key or not annotated_path:
                    continue
                chapter_path = resolve_project_path(annotated_path)
                if chapter_path.exists():
                    catalog[chapter_key] = build_chapter_catalog_entry(chapter_key, chapter_path)

    if catalog:
        return dict(sorted(catalog.items()))

    for chapter_path in sorted(index_root.glob("*_annotated_assets.jsonl")):
        chapter_key = chapter_path.name.split("_annotated_assets.jsonl", 1)[0]
        catalog[chapter_key] = build_chapter_catalog_entry(chapter_key, chapter_path)
    return dict(sorted(catalog.items()))


def build_chapter_catalog_entry(chapter_key: str, chapter_path: Path) -> dict[str, Any]:
    stats = summarize_chapter_file(chapter_path)
    return {
        "chapter_key": chapter_key,
        "index_file": project_relative_path(chapter_path),
        "label": build_chapter_label(chapter_key, stats["chapter_title"]),
        "chapter_title": stats["chapter_title"],
        "annotated_asset_count": stats["annotated_asset_count"],
        "figure_count": stats["figure_count"],
        "figures_with_visual_summary": stats["figures_with_visual_summary"],
    }


def build_catalog_payload(index_root: Path, *, initial_chapter_key: str) -> dict[str, Any]:
    catalog = discover_catalog(index_root)
    return {
        "index_root": project_relative_path(index_root),
        "initial_chapter_key": initial_chapter_key if initial_chapter_key in catalog else next(iter(catalog), ""),
        "chapters": list(catalog.values()),
    }


def summarize_chapter_file(path: Path) -> dict[str, Any]:
    annotated_asset_count = 0
    figure_count = 0
    figures_with_visual_summary = 0
    chapter_title = ""
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {path}") from exc
            if not isinstance(record, dict):
                continue
            annotated_asset_count += 1
            if not chapter_title:
                chapter_title = str(record.get("chapter_title", "") or "").strip()
            if str(record.get("asset_type", "")).strip() != "figure":
                continue
            figure_count += 1
            if str(record.get("visual_summary", "") or "").strip():
                figures_with_visual_summary += 1
    return {
        "chapter_title": chapter_title,
        "annotated_asset_count": annotated_asset_count,
        "figure_count": figure_count,
        "figures_with_visual_summary": figures_with_visual_summary,
    }


def build_chapter_label(chapter_key: str, chapter_title: str) -> str:
    if chapter_title:
        return f"{chapter_key} | {chapter_title}"
    return chapter_key


def get_chapter_path(index_root: Path, chapter_key: str) -> Path:
    catalog = discover_catalog(index_root)
    if chapter_key and chapter_key in catalog:
        return resolve_project_path(catalog[chapter_key]["index_file"])
    if not catalog:
        raise FileNotFoundError(f"No annotated chapter files found under: {index_root}")
    first_key = next(iter(catalog))
    return resolve_project_path(catalog[first_key]["index_file"])


def first_param(params: dict[str, list[str]], key: str, default: str) -> str:
    values = params.get(key)
    if not values:
        return default
    return values[0]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {path}") from exc
            if isinstance(record, dict):
                records.append(record)
    return records


def select_record(
    records: list[dict[str, Any]],
    *,
    position: int,
    asset_type: str,
    caption_contains: str,
) -> tuple[dict[str, Any], int]:
    filtered: list[dict[str, Any]] = []
    for record in records:
        if asset_type and str(record.get("asset_type", "")).strip() != asset_type:
            continue
        if caption_contains and caption_contains not in str(record.get("caption_text", "")):
            continue
        filtered.append(record)
    if not filtered:
        raise ValueError("No records matched the current filters.")
    safe_position = min(max(position, 1), len(filtered))
    return filtered[safe_position - 1], len(filtered)


def build_asset_payload(
    *,
    index_root: Path,
    chapter_key: str,
    position: int,
    asset_type: str,
    caption_contains: str,
) -> dict[str, Any]:
    catalog = discover_catalog(index_root)
    chapter_path = get_chapter_path(index_root, chapter_key)
    normalized_chapter_key = chapter_path.name.split("_annotated_assets.jsonl", 1)[0]
    chapter_meta = catalog.get(normalized_chapter_key, {})
    records = load_jsonl(chapter_path)
    record, total = select_record(records, position=position, asset_type=asset_type, caption_contains=caption_contains)
    safe_position = min(max(position, 1), total)
    image_url = (
        "/api/image"
        f"?chapter_key={url_quote(normalized_chapter_key)}"
        f"&position={safe_position}"
        f"&asset_type={url_quote(asset_type)}"
        f"&caption_contains={url_quote(caption_contains)}"
    )
    return {
        "index_root": project_relative_path(index_root),
        "chapter_key": normalized_chapter_key,
        "chapter_label": chapter_meta.get("label", normalized_chapter_key),
        "chapter_title": chapter_meta.get("chapter_title", ""),
        "index_file": project_relative_path(chapter_path),
        "asset_type": asset_type,
        "caption_contains": caption_contains,
        "position": safe_position,
        "total": total,
        "has_prev": safe_position > 1,
        "has_next": safe_position < total,
        "image_url": image_url,
        "record": record,
        "chapter_meta": chapter_meta,
    }


def url_quote(value: str) -> str:
    return quote(value, safe="-_.~")


def render_app_html(*, default_asset_type: str, initial_chapter_key: str) -> str:
    default_asset_type = escape(default_asset_type)
    initial_chapter_key = escape(initial_chapter_key)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Annotated Figure Browser</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f1e8;
      --panel: rgba(255, 252, 247, 0.96);
      --ink: #1f2933;
      --muted: #607080;
      --line: #dbc8b0;
      --accent: #b55d39;
      --accent-strong: #8c4226;
      --accent-soft: #f7e0d5;
      --code: #f1ece4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #f3d9c5 0, transparent 24rem),
        linear-gradient(180deg, #fbf7f1 0%, var(--bg) 100%);
    }}
    .page {{
      max-width: 1360px;
      margin: 0 auto;
      padding: 22px 18px 28px;
    }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(12px);
      background: rgba(246, 241, 232, 0.84);
      border-bottom: 1px solid rgba(219, 200, 176, 0.75);
      margin: -22px -18px 18px;
      padding: 14px 18px 12px;
    }}
    .topbar-inner {{
      max-width: 1360px;
      margin: 0 auto;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 24px;
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: end;
    }}
    .field {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 120px;
    }}
    .field label {{
      font-size: 12px;
      color: var(--muted);
    }}
    input, select {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: rgba(255,255,255,0.92);
      color: var(--ink);
      min-width: 0;
    }}
    button {{
      border: 0;
      border-radius: 12px;
      padding: 10px 14px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font-weight: 600;
    }}
    button.secondary {{
      background: #e8ded0;
      color: var(--ink);
    }}
    button:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}
    .status {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(360px, 1.15fr) minmax(400px, 0.95fr);
      gap: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 8px 28px rgba(96, 64, 27, 0.06);
      min-width: 0;
    }}
    .image-wrap {{
      min-height: 320px;
      display: grid;
      place-items: center;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid #eadbc8;
      background: #fff;
    }}
    .image-wrap img {{
      display: block;
      max-width: 100%;
      max-height: calc(100vh - 240px);
      object-fit: contain;
    }}
    .image-missing {{
      color: var(--muted);
      padding: 24px;
    }}
    .caption {{
      margin: 12px 0 0;
      font-size: 18px;
      color: var(--accent-strong);
      line-height: 1.45;
    }}
    .meta {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
      word-break: break-all;
      white-space: pre-wrap;
    }}
    .section {{
      margin-top: 16px;
    }}
    .section h2 {{
      margin: 0 0 10px;
      font-size: 16px;
      color: var(--accent);
    }}
    .text-block {{
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.6;
    }}
    .pill-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .pill {{
      display: inline-block;
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-strong);
      font-size: 13px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin-bottom: 8px;
      line-height: 1.55;
    }}
    dl {{
      margin: 0;
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 8px 12px;
    }}
    dt {{
      font-weight: 700;
      color: #6c482e;
    }}
    dd {{
      margin: 0;
      word-break: break-word;
      white-space: pre-wrap;
    }}
    details {{
      margin-top: 16px;
    }}
    pre {{
      margin: 10px 0 0;
      padding: 14px;
      border-radius: 14px;
      background: var(--code);
      border: 1px solid #e4d7c7;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.5;
    }}
    @media (max-width: 960px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      dl {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <h1>Vision Figure Browser</h1>
      <div class="controls">
        <div class="field" style="min-width: 280px; flex: 1 1 280px;">
          <label for="chapterSelect">chapter</label>
          <select id="chapterSelect"></select>
        </div>
        <div class="field">
          <label for="assetTypeInput">asset_type</label>
          <input id="assetTypeInput" value="{default_asset_type}" />
        </div>
        <div class="field" style="min-width: 260px; flex: 1 1 260px;">
          <label for="captionInput">caption_contains</label>
          <input id="captionInput" placeholder="可留空，按顺序浏览当前章节全部 figure" />
        </div>
        <div class="field">
          <label for="positionInput">position</label>
          <input id="positionInput" type="number" min="1" value="1" />
        </div>
        <button id="applyBtn">应用筛选</button>
        <button id="prevBtn" class="secondary">上一张</button>
        <button id="nextBtn">下一张</button>
        <button id="refreshBtn" class="secondary">重新读取</button>
      </div>
      <div id="statusLine" class="status">准备就绪。支持左右方向键翻页，切换章节后会实时读取对应 JSONL。</div>
    </div>
  </div>

  <main class="page">
    <section class="layout">
      <article class="card">
        <div id="imageWrap" class="image-wrap"><div class="image-missing">加载中...</div></div>
        <p id="captionText" class="caption"></p>
        <p id="imageMeta" class="meta"></p>
      </article>
      <article class="card">
        <section class="section">
          <h2>定位信息</h2>
          <dl id="metaGrid"></dl>
        </section>
        <section class="section">
          <h2>visual_summary</h2>
          <div id="visualSummary" class="text-block"></div>
        </section>
        <section class="section">
          <h2>relation_statement</h2>
          <div id="relationStatement" class="text-block"></div>
        </section>
        <section class="section">
          <h2>visual_key_elements</h2>
          <div id="keyElements" class="pill-row"></div>
        </section>
        <section class="section">
          <h2>visual_relations</h2>
          <ul id="visualRelations"></ul>
        </section>
        <section class="section">
          <h2>teaching_focus</h2>
          <ul id="teachingFocus"></ul>
        </section>
        <section class="section">
          <h2>question_affordances</h2>
          <div id="questionAffordances" class="pill-row"></div>
        </section>
        <section class="section">
          <h2>retrieval_keywords</h2>
          <div id="retrievalKeywords" class="pill-row"></div>
        </section>
        <section class="section">
          <h2>direct_readable_claims</h2>
          <ul id="directClaims"></ul>
        </section>
        <details>
          <summary>查看完整原始 JSON</summary>
          <pre id="rawJson"></pre>
        </details>
      </article>
    </section>
  </main>

  <script>
    const initialChapterKey = "{initial_chapter_key}";
    const state = {{
      position: 1,
      total: 0,
      assetType: "{default_asset_type}",
      captionContains: "",
      chapterKey: initialChapterKey,
      chapters: [],
    }};

    const els = {{
      chapterSelect: document.getElementById("chapterSelect"),
      assetTypeInput: document.getElementById("assetTypeInput"),
      captionInput: document.getElementById("captionInput"),
      positionInput: document.getElementById("positionInput"),
      applyBtn: document.getElementById("applyBtn"),
      prevBtn: document.getElementById("prevBtn"),
      nextBtn: document.getElementById("nextBtn"),
      refreshBtn: document.getElementById("refreshBtn"),
      statusLine: document.getElementById("statusLine"),
      imageWrap: document.getElementById("imageWrap"),
      captionText: document.getElementById("captionText"),
      imageMeta: document.getElementById("imageMeta"),
      metaGrid: document.getElementById("metaGrid"),
      visualSummary: document.getElementById("visualSummary"),
      relationStatement: document.getElementById("relationStatement"),
      keyElements: document.getElementById("keyElements"),
      visualRelations: document.getElementById("visualRelations"),
      teachingFocus: document.getElementById("teachingFocus"),
      questionAffordances: document.getElementById("questionAffordances"),
      retrievalKeywords: document.getElementById("retrievalKeywords"),
      directClaims: document.getElementById("directClaims"),
      rawJson: document.getElementById("rawJson"),
    }};

    function setStatus(text) {{
      els.statusLine.textContent = text;
    }}

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"]/g, (char) => {{
        const map = {{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }};
        return map[char] || char;
      }});
    }}

    function renderPills(container, values) {{
      container.innerHTML = "";
      const items = Array.isArray(values) ? values : [];
      if (!items.length) {{
        container.textContent = "无";
        return;
      }}
      for (const item of items) {{
        const span = document.createElement("span");
        span.className = "pill";
        span.textContent = String(item);
        container.appendChild(span);
      }}
    }}

    function renderList(container, values) {{
      container.innerHTML = "";
      const items = Array.isArray(values) ? values : [];
      if (!items.length) {{
        const li = document.createElement("li");
        li.textContent = "无";
        container.appendChild(li);
        return;
      }}
      for (const item of items) {{
        const li = document.createElement("li");
        li.textContent = typeof item === "string" ? item : JSON.stringify(item, null, 2);
        container.appendChild(li);
      }}
    }}

    function renderMetaGrid(payload, record) {{
      const chapterMeta = payload.chapter_meta || {{}};
      const rows = [
        ["chapter", payload.chapter_key || ""],
        ["position", `${{payload.position}} / ${{payload.total}}`],
        ["asset_id", record.asset_id || ""],
        ["content_hash", record.content_hash || ""],
        ["anchor_node", `${{record.anchor_node_id || ""}} ${{record.anchor_node_name || ""}}`.trim()],
        ["visual_type", record.visual_type || ""],
        ["vision_model", record.vision_model || ""],
        ["vision_confidence", record.vision_confidence ?? ""],
        ["chapter_title", payload.chapter_title || chapterMeta.chapter_title || ""],
        ["chapter_figures", `${{chapterMeta.figures_with_visual_summary ?? ""}} / ${{chapterMeta.figure_count ?? ""}}`],
        ["index_file", payload.index_file || ""],
        ["source_path", record.source_path || ""],
      ];
      els.metaGrid.innerHTML = rows
        .map(([key, value]) => `<dt>${{escapeHtml(key)}}</dt><dd>${{escapeHtml(value)}}</dd>`)
        .join("");
    }}

    function renderImage(payload, record) {{
      els.imageWrap.innerHTML = "";
      const imageUrl = payload.image_url || "";
      if (!imageUrl) {{
        const missing = document.createElement("div");
        missing.className = "image-missing";
        missing.textContent = "当前记录没有可展示图片";
        els.imageWrap.appendChild(missing);
        return;
      }}
      const image = document.createElement("img");
      image.alt = record.asset_id || "annotated figure";
      image.src = `${{imageUrl}}&t=${{Date.now()}}`;
      image.loading = "eager";
      image.onerror = () => {{
        els.imageWrap.innerHTML = '<div class="image-missing">图片读取失败</div>';
      }};
      els.imageWrap.appendChild(image);
    }}

    function currentQuery() {{
      return {{
        chapterKey: els.chapterSelect.value || state.chapterKey || initialChapterKey,
        assetType: els.assetTypeInput.value.trim(),
        captionContains: els.captionInput.value.trim(),
      }};
    }}

    function populateChapterSelect(chapters, preferredKey) {{
      els.chapterSelect.innerHTML = "";
      for (const chapter of chapters) {{
        const option = document.createElement("option");
        option.value = chapter.chapter_key;
        option.textContent = chapter.label || chapter.chapter_key;
        els.chapterSelect.appendChild(option);
      }}
      if (preferredKey && chapters.some((item) => item.chapter_key === preferredKey)) {{
        els.chapterSelect.value = preferredKey;
      }} else if (chapters.length) {{
        els.chapterSelect.value = chapters[0].chapter_key;
      }}
    }}

    async function loadCatalog() {{
      const response = await fetch("/api/catalog", {{ cache: "no-store" }});
      const payload = await response.json();
      if (!response.ok) {{
        throw new Error(payload.error || "章节目录加载失败");
      }}
      state.chapters = Array.isArray(payload.chapters) ? payload.chapters : [];
      populateChapterSelect(state.chapters, payload.initial_chapter_key || initialChapterKey);
      return payload;
    }}

    async function loadAsset(position) {{
      const query = currentQuery();
      const url = `/api/asset?chapter_key=${{encodeURIComponent(query.chapterKey)}}&position=${{encodeURIComponent(position)}}&asset_type=${{encodeURIComponent(query.assetType)}}&caption_contains=${{encodeURIComponent(query.captionContains)}}`;
      setStatus("正在读取当前章节 JSONL 并加载图片...");
      const response = await fetch(url, {{ cache: "no-store" }});
      const payload = await response.json();
      if (!response.ok) {{
        throw new Error(payload.error || "加载失败");
      }}
      const record = payload.record || {{}};
      state.position = payload.position;
      state.total = payload.total;
      state.assetType = query.assetType;
      state.captionContains = query.captionContains;
      state.chapterKey = payload.chapter_key || query.chapterKey;

      els.positionInput.value = String(payload.position);
      els.chapterSelect.value = state.chapterKey;
      els.captionText.textContent = record.caption_text || record.asset_id || "";
      els.imageMeta.textContent = `${{payload.chapter_label || payload.chapter_key || ""}} | asset_type=${{payload.asset_type || ""}} | matched=${{payload.total}} | source=${{record.source_doc_name || ""}}`;
      els.visualSummary.textContent = record.visual_summary || "无";
      els.relationStatement.textContent = record.relation_statement || "无";
      els.rawJson.textContent = JSON.stringify(record, null, 2);
      renderMetaGrid(payload, record);
      renderImage(payload, record);
      renderPills(els.keyElements, record.visual_key_elements);
      renderList(els.visualRelations, record.visual_relations);
      renderList(els.teachingFocus, record.teaching_focus);
      renderPills(els.questionAffordances, record.question_affordances);
      renderPills(els.retrievalKeywords, record.retrieval_keywords);
      renderList(els.directClaims, record.direct_readable_claims);

      els.prevBtn.disabled = !payload.has_prev;
      els.nextBtn.disabled = !payload.has_next;
      setStatus(`已加载 ${{payload.chapter_key}} 第 ${{payload.position}} / ${{payload.total}} 张。切换章节或翻页时都会重新读取对应 JSONL。`);
    }}

    async function guardedLoad(position) {{
      try {{
        await loadAsset(position);
      }} catch (error) {{
        setStatus(`加载失败：${{error.message}}`);
      }}
    }}

    async function bootstrap() {{
      try {{
        const catalog = await loadCatalog();
        const firstKey = els.chapterSelect.value || catalog.initial_chapter_key || initialChapterKey;
        state.chapterKey = firstKey;
        await guardedLoad(1);
      }} catch (error) {{
        setStatus(`初始化失败：${{error.message}}`);
      }}
    }}

    els.applyBtn.addEventListener("click", () => guardedLoad(Number(els.positionInput.value || 1)));
    els.refreshBtn.addEventListener("click", () => guardedLoad(state.position || 1));
    els.prevBtn.addEventListener("click", () => {{
      if (state.position > 1) {{
        guardedLoad(state.position - 1);
      }}
    }});
    els.nextBtn.addEventListener("click", () => guardedLoad((state.position || 1) + 1));
    els.positionInput.addEventListener("change", () => guardedLoad(Number(els.positionInput.value || 1)));
    els.chapterSelect.addEventListener("change", () => guardedLoad(1));
    els.captionInput.addEventListener("keydown", (event) => {{
      if (event.key === "Enter") {{
        guardedLoad(1);
      }}
    }});
    els.assetTypeInput.addEventListener("keydown", (event) => {{
      if (event.key === "Enter") {{
        guardedLoad(1);
      }}
    }});
    document.addEventListener("keydown", (event) => {{
      if (event.target && ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {{
        return;
      }}
      if (event.key === "ArrowLeft" && state.position > 1) {{
        guardedLoad(state.position - 1);
      }}
      if (event.key === "ArrowRight") {{
        guardedLoad((state.position || 1) + 1);
      }}
      if (event.key.toLowerCase() === "r") {{
        guardedLoad(state.position || 1);
      }}
    }});

    bootstrap();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
