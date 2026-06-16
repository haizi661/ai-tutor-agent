from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from html import escape
from pathlib import Path
from typing import Any

from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


DEFAULT_INDEX = "data/media_evidence_index_vision_pilot/chapter_01_annotated_assets.jsonl"
DEFAULT_OUTPUT = "data/media_evidence_index_vision_pilot/inspect_annotated_figure.html"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render one annotated figure asset into an inspection HTML page.")
    parser.add_argument(
        "--index",
        type=str,
        default=DEFAULT_INDEX,
        help="Annotated asset jsonl path.",
    )
    parser.add_argument(
        "--output-html",
        type=str,
        default=DEFAULT_OUTPUT,
        help="Output HTML path.",
    )
    parser.add_argument(
        "--asset-id",
        type=str,
        default="",
        help="Exact asset_id match.",
    )
    parser.add_argument(
        "--content-hash",
        type=str,
        default="",
        help="Exact content_hash match.",
    )
    parser.add_argument(
        "--caption-contains",
        type=str,
        default="",
        help="Substring match against caption_text.",
    )
    parser.add_argument(
        "--source-path-contains",
        type=str,
        default="",
        help="Substring match against source_path.",
    )
    parser.add_argument(
        "--asset-type",
        type=str,
        default="figure",
        help="Optional asset_type filter. Default: figure.",
    )
    parser.add_argument(
        "--match-index",
        type=int,
        default=1,
        help="1-based index among matched items.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    index_path = resolve_project_path(args.index)
    output_path = resolve_project_path(args.output_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_jsonl(index_path)
    selected, matched_count = select_record(
        records,
        asset_type=args.asset_type.strip(),
        asset_id=args.asset_id.strip(),
        content_hash=args.content_hash.strip(),
        caption_contains=args.caption_contains.strip(),
        source_path_contains=args.source_path_contains.strip(),
        match_index=args.match_index,
    )
    html_text = render_html(selected, index_path=index_path, matched_count=matched_count)
    output_path.write_text(html_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "output_html": project_relative_path(output_path),
                "index": project_relative_path(index_path),
                "asset_id": selected.get("asset_id", ""),
                "content_hash": selected.get("content_hash", ""),
                "matched_count": matched_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Annotated asset index not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {path}") from exc
            if isinstance(item, dict):
                records.append(item)
    return records


def select_record(
    records: list[dict[str, Any]],
    *,
    asset_type: str,
    asset_id: str,
    content_hash: str,
    caption_contains: str,
    source_path_contains: str,
    match_index: int,
) -> tuple[dict[str, Any], int]:
    matched: list[dict[str, Any]] = []
    for item in records:
        if asset_type and str(item.get("asset_type", "")).strip() != asset_type:
            continue
        if asset_id and str(item.get("asset_id", "")).strip() != asset_id:
            continue
        if content_hash and str(item.get("content_hash", "")).strip() != content_hash:
            continue
        if caption_contains and caption_contains not in str(item.get("caption_text", "")):
            continue
        if source_path_contains and source_path_contains not in str(item.get("source_path", "")):
            continue
        matched.append(item)

    if not matched:
        raise ValueError("No annotated asset matched the provided filters.")
    if match_index < 1 or match_index > len(matched):
        raise ValueError(f"--match-index must be between 1 and {len(matched)}.")
    return matched[match_index - 1], len(matched)


def render_html(record: dict[str, Any], *, index_path: Path, matched_count: int) -> str:
    asset_id = str(record.get("asset_id", ""))
    content_hash = str(record.get("content_hash", ""))
    image_src, image_note = build_image_src(record.get("source_path", ""))

    sections = [
        render_kv_section(
            "定位信息",
            {
                "asset_id": asset_id,
                "content_hash": content_hash,
                "asset_type": record.get("asset_type", ""),
                "anchor_node_id": record.get("anchor_node_id", ""),
                "anchor_node_name": record.get("anchor_node_name", ""),
                "source_path": record.get("source_path", ""),
                "source_doc_name": record.get("source_doc_name", ""),
                "index_file": project_relative_path(index_path),
                "matched_count": matched_count,
            },
        ),
        render_kv_section(
            "图像理解摘要",
            {
                "caption_text": record.get("caption_text", ""),
                "visual_summary": record.get("visual_summary", ""),
                "relation_statement": record.get("relation_statement", ""),
                "visual_type": record.get("visual_type", ""),
                "evidence_role": record.get("evidence_role", ""),
                "vision_model": record.get("vision_model", ""),
                "vision_confidence": record.get("vision_confidence", ""),
                "confidence": record.get("confidence", ""),
                "needs_review": record.get("needs_review", ""),
            },
        ),
        render_list_section("visual_key_elements", record.get("visual_key_elements", [])),
        render_list_section("visual_relations", record.get("visual_relations", [])),
        render_list_section("teaching_focus", record.get("teaching_focus", [])),
        render_list_section("question_affordances", record.get("question_affordances", [])),
        render_list_section("retrieval_keywords", record.get("retrieval_keywords", [])),
        render_list_section("direct_readable_claims", record.get("direct_readable_claims", [])),
        render_kv_section(
            "其他原始字段",
            {
                "chapter_title": record.get("chapter_title", ""),
                "title_text": record.get("title_text", ""),
                "nearby_text": record.get("nearby_text", ""),
                "raw_text": record.get("raw_text", ""),
                "page_range": record.get("page_range", []),
                "linked_node_ids": record.get("linked_node_ids", []),
                "linked_node_names": record.get("linked_node_names", []),
                "link_scores": record.get("link_scores", []),
                "domain_terms": record.get("domain_terms", []),
                "variables": record.get("variables", []),
                "layout_features": record.get("layout_features", []),
                "formula_meaning": record.get("formula_meaning", ""),
                "llm_generated_fields": record.get("llm_generated_fields", []),
                "extra": record.get("extra", {}),
            },
        ),
    ]

    raw_json = escape(json.dumps(record, ensure_ascii=False, indent=2))
    image_block = (
        f'<img src="{image_src}" alt="{escape(asset_id or "annotated figure")}" class="preview-image" />'
        if image_src
        else '<div class="image-missing">Image unavailable</div>'
    )
    if image_note:
        image_block += f'<p class="image-note">{escape(image_note)}</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Annotated Figure Inspect</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f1e8;
      --panel: #fffdfa;
      --ink: #1f2933;
      --muted: #5b6b7b;
      --line: #d9cdb7;
      --accent: #b85c38;
      --accent-soft: #f6dfd2;
      --code: #f2eee6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, #f4d6bf 0, transparent 24rem),
        linear-gradient(180deg, #f9f5ef 0%, var(--bg) 100%);
    }}
    .page {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 20px 40px;
    }}
    .hero {{
      background: rgba(255, 253, 250, 0.88);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 12px 40px rgba(96, 64, 27, 0.08);
    }}
    h1, h2, h3 {{
      margin: 0;
      line-height: 1.3;
    }}
    h1 {{
      font-size: 28px;
      margin-bottom: 10px;
    }}
    .subtle {{
      color: var(--muted);
      font-size: 14px;
      margin-top: 6px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(320px, 1.05fr) minmax(360px, 1fr);
      gap: 20px;
      margin-top: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(96, 64, 27, 0.06);
    }}
    .preview-image {{
      width: 100%;
      max-height: 78vh;
      object-fit: contain;
      border-radius: 14px;
      background: #fff;
      border: 1px solid #e7dcc9;
    }}
    .image-missing {{
      min-height: 240px;
      display: grid;
      place-items: center;
      border-radius: 14px;
      border: 1px dashed var(--line);
      color: var(--muted);
      background: #fbf8f3;
    }}
    .image-note {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
      word-break: break-all;
    }}
    .section {{
      margin-top: 16px;
    }}
    .section h2 {{
      font-size: 18px;
      margin-bottom: 12px;
      color: var(--accent);
    }}
    dl {{
      margin: 0;
      display: grid;
      grid-template-columns: minmax(120px, 180px) 1fr;
      gap: 8px 14px;
    }}
    dt {{
      font-weight: 700;
      color: #6a442d;
    }}
    dd {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin: 0 0 8px;
      line-height: 1.55;
    }}
    .pill {{
      display: inline-block;
      margin: 0 6px 6px 0;
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: #7e3e22;
      font-size: 13px;
    }}
    details {{
      margin-top: 18px;
    }}
    summary {{
      cursor: pointer;
      font-weight: 700;
      color: var(--accent);
    }}
    pre {{
      margin: 12px 0 0;
      padding: 14px;
      border-radius: 14px;
      background: var(--code);
      border: 1px solid #e4d8c6;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.5;
    }}
    @media (max-width: 900px) {{
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
  <main class="page">
    <section class="hero">
      <h1>{escape(str(record.get("caption_text", "") or asset_id or "Annotated Figure"))}</h1>
      <p class="subtle">用于快速核查单张图片的视觉标注、检索字段与原始 JSON 是否一致。</p>
      <p class="subtle">asset_id: {escape(asset_id)}</p>
    </section>
    <section class="layout">
      <article class="card">
        <h2>图片预览</h2>
        {image_block}
      </article>
      <article class="card">
        {''.join(sections)}
        <details>
          <summary>查看完整原始 JSON</summary>
          <pre>{raw_json}</pre>
        </details>
      </article>
    </section>
  </main>
</body>
</html>
"""


def build_image_src(source_path_value: Any) -> tuple[str, str]:
    source_path_text = str(source_path_value or "").strip()
    if not source_path_text:
        return "", "source_path is empty."
    source_path = Path(source_path_text)
    if not source_path.exists():
        return "", f"Image file not found: {source_path_text}"
    mime_type = mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(source_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}", project_relative_path(source_path)


def render_kv_section(title: str, values: dict[str, Any]) -> str:
    rows: list[str] = []
    for key, value in values.items():
        rows.append(f"<dt>{escape(key)}</dt><dd>{render_value(value)}</dd>")
    return f'<section class="section"><h2>{escape(title)}</h2><dl>{"".join(rows)}</dl></section>'


def render_list_section(title: str, values: Any) -> str:
    if not isinstance(values, list):
        values = [values] if values else []
    if not values:
        return f'<section class="section"><h2>{escape(title)}</h2><p class="subtle">无</p></section>'
    if all(isinstance(item, str) and len(item) <= 40 for item in values):
        items = "".join(f'<span class="pill">{escape(item)}</span>' for item in values if str(item).strip())
        return f'<section class="section"><h2>{escape(title)}</h2><div>{items}</div></section>'
    items = "".join(f"<li>{render_value(item)}</li>" for item in values)
    return f'<section class="section"><h2>{escape(title)}</h2><ul>{items}</ul></section>'


def render_value(value: Any) -> str:
    if isinstance(value, dict):
        return f"<pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre>"
    if isinstance(value, list):
        if not value:
            return "[]"
        return f"<pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre>"
    return escape(str(value))


if __name__ == "__main__":
    main()
