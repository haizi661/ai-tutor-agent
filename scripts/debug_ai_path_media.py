from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

from ai_tutor_agent.ai_learning_path.ai_path_service import AILearningPathService


def _as_bool_label(value: bool) -> str:
    return "yes" if value else "no"


def _summarize_media_item(item: dict[str, Any]) -> dict[str, Any]:
    paths = item.get("image_paths_abs") or []
    if not isinstance(paths, list):
        paths = [paths]
    return {
        "asset_type": item.get("asset_type"),
        "display_label": item.get("display_label"),
        "reference": item.get("reference"),
        "source_doc_id": item.get("source_doc_id"),
        "is_primary": item.get("is_primary"),
        "has_image_paths_abs": bool(paths),
        "existing_image_paths": [
            str(path)
            for path in paths
            if path and Path(str(path)).exists()
        ],
        "caption": item.get("caption"),
    }


def _build_debug_page(summary: dict[str, Any], rendered: str) -> str:
    media_rows = []
    for item in summary.get("media_items", []):
        existing_paths = item.get("existing_image_paths") or []
        path_text = "<br>".join(html.escape(str(path)) for path in existing_paths) or "-"
        media_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('asset_type') or ''))}</td>"
            f"<td>{html.escape(str(item.get('display_label') or ''))}</td>"
            f"<td><code>{html.escape(str(item.get('reference') or ''))}</code></td>"
            f"<td>{html.escape(_as_bool_label(bool(existing_paths)))}</td>"
            f"<td>{path_text}</td>"
            "</tr>"
        )

    checks = [
        ("media_enricher_loaded", summary.get("media_enricher_loaded")),
        ("render_has_learning_answer_content", summary.get("render_has_learning_answer_content")),
        ("render_has_figure_card", summary.get("render_has_figure_card")),
        ("render_has_formula_card", summary.get("render_has_formula_card")),
        ("render_has_img_tag", summary.get("render_has_img_tag")),
        ("render_has_reference_section", summary.get("render_has_reference_section")),
    ]
    check_items = "\n".join(
        f"<li><strong>{html.escape(name)}</strong>: {html.escape(_as_bool_label(bool(value)))}</li>"
        for name, value in checks
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Path Media Debug - {html.escape(str(summary.get("node_id") or ""))}</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f9;
      color: #1f2933;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      line-height: 1.25;
    }}
    .panel {{
      background: #fff;
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 18px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }}
    .metric {{
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px;
      background: #fafafa;
    }}
    .metric span {{
      display: block;
      color: #64748b;
      font-size: 12px;
      margin-bottom: 3px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #d8dee8;
      padding: 8px;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #edf2f7;
    }}
    code {{
      word-break: break-all;
      white-space: normal;
    }}
    .learning-answer-content {{
      background: #fff;
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 18px;
    }}
    .learning-reference-block,
    .learning-related-overview {{
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 14px;
      margin: 14px 0;
      background: #fbfcfe;
    }}
    .learning-reference-media-title,
    .learning-block-title {{
      font-weight: 700;
      margin-bottom: 10px;
    }}
    .learning-reference-media-grid,
    .learning-related-media-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}
    .learning-evidence-card {{
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 12px;
      background: #fff;
      overflow: hidden;
    }}
    .learning-figure-viewport {{
      overflow: auto;
      max-height: 520px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #fff;
      margin-top: 8px;
    }}
    .learning-figure-viewport img {{
      display: block;
      max-width: 100%;
      height: auto;
      margin: 0 auto;
    }}
    .learning-formula-viewport {{
      overflow-x: auto;
      padding: 10px;
      background: #f8fafc;
      border-radius: 6px;
      font-family: "Times New Roman", serif;
    }}
  </style>
</head>
<body>
<main>
  <section class="panel">
    <h1>AI Path Media Debug</h1>
    <div class="grid">
      <div class="metric"><span>node</span>{html.escape(str(summary.get("node_id") or ""))} / {html.escape(str(summary.get("node_name") or ""))}</div>
      <div class="metric"><span>source doc</span><code>{html.escape(str(summary.get("retrieval_source_pdf") or ""))}</code></div>
      <div class="metric"><span>media count</span>{summary.get("media_count")} total, {summary.get("figure_count")} figures, {summary.get("formula_count")} formulas</div>
      <div class="metric"><span>html output</span><code>{html.escape(str(summary.get("html_output") or ""))}</code></div>
    </div>
    <ul>{check_items}</ul>
  </section>

  <section class="panel">
    <h2>Mapped Media</h2>
    <table>
      <thead><tr><th>type</th><th>label</th><th>reference</th><th>image exists</th><th>resolved image path</th></tr></thead>
      <tbody>{''.join(media_rows)}</tbody>
    </table>
  </section>

  <section class="panel">
    <h2>Rendered Lesson HTML</h2>
    {rendered}
  </section>
</main>
</body>
</html>
"""


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Debug AI learning path media lookup and rendered lesson HTML."
    )
    parser.add_argument("--node-id", default="AI001")
    parser.add_argument(
        "--out",
        default="data/debug_outputs/ai_path_media_debug.html",
        help="Where to write the rendered HTML snippet.",
    )
    args = parser.parse_args()

    service = AILearningPathService()
    node = service._format_node(args.node_id)
    if args.node_id not in service.node_by_id:
        raise SystemExit(f"Unknown node id: {args.node_id}")

    sample_answer = (
        f"### {node.get('name')}\n\n"
        "这里用当前节点的图表来辅助说明。"
        "如果媒体链路正常，下面应该出现真实图片卡片。"
    )
    media_items = service._collect_node_media_items(
        node,
        question=str(node.get("name", "")),
    )
    rendered = service._render_learning_message(
        content=sample_answer,
        node=node,
        question=str(node.get("name", "")),
    )
    out_path = Path(args.out)

    summary = {
        "node_id": node.get("node_id"),
        "node_name": node.get("name"),
        "retrieval_source_pdf": (node.get("extra") or {}).get("retrieval_source_pdf"),
        "figures_refs": node.get("figures_refs", []),
        "formulas": node.get("formulas", []),
        "media_enricher_loaded": service.media_enricher is not None,
        "media_count": len(media_items),
        "figure_count": sum(1 for item in media_items if item.get("asset_type") == "figure"),
        "formula_count": sum(1 for item in media_items if item.get("asset_type") == "formula"),
        "table_count": sum(1 for item in media_items if item.get("asset_type") == "table"),
        "render_has_learning_answer_content": "learning-answer-content" in rendered,
        "render_has_figure_card": "learning-figure-card" in rendered,
        "render_has_formula_card": "learning-formula-card" in rendered,
        "render_has_img_tag": "<img" in rendered,
        "render_has_reference_section": "参考资料" in rendered or "鍙傝€冭祫鏂" in rendered,
        "html_output": str(out_path),
        "media_items": [_summarize_media_item(item) for item in media_items[:10]],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_build_debug_page(summary, rendered), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
