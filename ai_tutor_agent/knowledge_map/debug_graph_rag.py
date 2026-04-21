from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from dotenv import load_dotenv

from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline

load_dotenv()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug graph-based RAG over the knowledge map.")
    parser.add_argument("--mode", choices=["focused", "balanced", "exploratory"], default="balanced")
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--disable-llm", action="store_true")
    parser.add_argument("--enable-vision", action="store_true")
    parser.add_argument("--llm-profile", choices=["qwen", "default"], default="qwen")
    parser.add_argument("--once", type=str, default="")
    parser.add_argument("--html-report", type=str, default="")
    return parser.parse_args(argv)


def build_html_report(result: dict) -> str:
    media_items = result.get("media_items", [])
    media_cards_by_ref: dict[str, str] = {}
    media_labels_by_ref: dict[str, str] = {}
    modal_cards: list[str] = []

    for idx, item in enumerate(media_items, start=1):
        ref = html.escape(item.get("reference", ""))
        display_label = html.escape(item.get("display_label", f"媒体{idx}"))
        node_name = html.escape(item.get("node_name", ""))
        modal_id = f"media-modal-{idx}"
        media_labels_by_ref[item.get("reference", "")] = item.get("display_label", f"媒体{idx}")

        if item.get("asset_type") == "formula":
            formula_text = html.escape(item.get("text", ""))
            preview = f"""
            <button class="media-card formula-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              <div class="formula-math">\\[{formula_text}\\]</div>
            </button>
            """
            modal_body = (
                f"<div class='formula-full formula-math'>\\[{formula_text}\\]</div>"
                f"<details class='formula-raw'><summary>查看原始 LaTeX</summary><pre>{formula_text}</pre></details>"
            )
        else:
            caption = html.escape(item.get("caption", ""))
            paths = item.get("image_paths_abs", []) or []
            preview_img = ""
            gallery = []
            if paths:
                preview_src = Path(paths[0]).resolve().as_uri()
                preview_img = f"<img src='{preview_src}' alt='{caption}' loading='lazy' />"
            for path in paths:
                uri = Path(path).resolve().as_uri()
                gallery.append(f"<img src='{uri}' alt='{caption}' loading='lazy' />")
            preview = f"""
            <button class="media-card figure-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              <div class="media-caption">{caption}</div>
              {preview_img}
            </button>
            """
            modal_body = f"<div class='figure-gallery'>{''.join(gallery)}</div><p>{caption}</p>"

        media_cards_by_ref[item.get("reference", "")] = preview
        modal_cards.append(
            f"""
            <div id="{modal_id}" class="modal" onclick="closeModal('{modal_id}')">
              <div class="modal-content" onclick="event.stopPropagation()">
                <button class="close-btn" onclick="closeModal('{modal_id}')">关闭</button>
                <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
                <div class="media-node">{node_name}</div>
                {modal_body}
              </div>
            </div>
            """
        )

    evidence_rows = "".join(
        f"<li><strong>{html.escape(item['reference'])}</strong> {html.escape(item['text'])}</li>"
        for item in result.get("evidence_items", [])[:8]
    )

    answer_html = _render_answer_html(str(result.get("answer", "")), media_cards_by_ref, media_labels_by_ref)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GraphRAG Debug Report</title>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']]
      }},
      svg: {{ fontCache: 'global' }},
      startup: {{ typeset: false }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    h1, h2 {{ margin: 0 0 12px; }}
    section {{ background: white; padding: 16px 18px; margin: 0 0 16px; border: 1px solid #dbe3ea; border-radius: 8px; }}
    .answer {{ white-space: normal; line-height: 1.7; }}
    .answer p {{ margin: 0 0 10px; }}
    .answer .section-title {{ font-weight: 700; margin-top: 14px; }}
    .answer .answer-media-block {{ margin: 14px 0 18px; padding-top: 8px; border-top: 1px solid #e2e8f0; }}
    .answer .answer-media-title {{ font-size: 14px; color: #475569; margin-bottom: 10px; font-weight: 600; }}
    .media-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    .media-card {{ width: 100%; text-align: left; border: 1px solid #cbd5e1; background: #fff; border-radius: 8px; padding: 12px; cursor: pointer; }}
    .media-card img {{ width: 100%; max-height: 220px; object-fit: contain; margin-top: 10px; border-radius: 6px; background: #f8fafc; }}
    .media-card pre {{ white-space: pre-wrap; word-break: break-word; font-size: 13px; margin: 10px 0 0; }}
    .media-ref {{ font-size: 12px; color: #475569; }}
    .raw-ref {{ color: #94a3b8; }}
    .media-node {{ font-weight: 600; margin-top: 4px; }}
    .media-caption {{ margin-top: 8px; }}
    .modal {{ display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.68); padding: 24px; overflow: auto; }}
    .modal-content {{ max-width: 960px; margin: 0 auto; background: white; border-radius: 8px; padding: 16px; }}
    .figure-gallery {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); margin-top: 12px; }}
    .figure-gallery img {{ width: 100%; max-height: 70vh; object-fit: contain; background: #f8fafc; border-radius: 6px; }}
    .formula-math {{ margin-top: 10px; padding: 12px; border-radius: 6px; background: #f8fafc; overflow-x: auto; }}
    .formula-full {{ font-size: 18px; line-height: 1.8; background: #f8fafc; padding: 12px; border-radius: 6px; overflow-x: auto; }}
    .formula-raw {{ margin-top: 12px; }}
    .formula-raw summary {{ cursor: pointer; color: #475569; }}
    .close-btn {{ border: 1px solid #cbd5e1; background: white; border-radius: 6px; padding: 6px 10px; cursor: pointer; float: right; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>GraphRAG 调试报告</h1>
      <p><strong>问题：</strong>{html.escape(result.get("question", ""))}</p>
    </section>
    <section>
      <h2>回答</h2>
      <div class="answer">{answer_html}</div>
    </section>
    <section>
      <h2>证据</h2>
      <ol>{evidence_rows}</ol>
    </section>
    {''.join(modal_cards)}
  </main>
  <script>
    function typesetMath(scope) {{
      if (!window.MathJax || !MathJax.typesetPromise) {{
        return;
      }}
      const targets = [];
      if (!scope || scope === document) {{
        targets.push(document.body);
      }} else {{
        targets.push(scope);
      }}
      MathJax.typesetPromise(targets).catch(function(err) {{
        console.error(err);
      }});
    }}

    function openModal(id) {{
      const modal = document.getElementById(id);
      modal.style.display = 'block';
      typesetMath(modal);
    }}
    function closeModal(id) {{
      document.getElementById(id).style.display = 'none';
    }}

    window.addEventListener('load', function() {{
      typesetMath(document);
    }});
  </script>
</body>
</html>
"""


def _render_answer_html(
    answer_text: str,
    media_cards_by_ref: dict[str, str],
    media_labels_by_ref: dict[str, str],
) -> str:
    lines = [line.rstrip() for line in answer_text.splitlines()]
    blocks: list[str] = []
    used_refs: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped == "$$":
            math_lines: list[str] = ["$$"]
            index += 1
            while index < len(lines):
                current = lines[index].rstrip()
                math_lines.append(current)
                if current.strip() == "$$":
                    break
                index += 1
            math_block = "\n".join(part for part in math_lines if part is not None).strip()
            blocks.append(f"<div class=\"formula-math answer-formula\">{html.escape(math_block)}</div>")
            index += 1
            continue
        clean_line, refs = _extract_media_refs(stripped)
        if clean_line:
            if _is_block_math_line(clean_line):
                blocks.append(
                    f"<div class=\"formula-math answer-formula\">{html.escape(clean_line)}</div>"
                )
            else:
                rendered_line = _render_answer_line(clean_line, media_labels_by_ref)
                if not rendered_line:
                    index += 1
                    continue
                if _is_section_line(clean_line):
                    blocks.append(f"<p class=\"section-title\">{rendered_line}</p>")
                else:
                    blocks.append(f"<p>{rendered_line}</p>")
        if refs:
            cards = []
            for ref in refs:
                card = media_cards_by_ref.get(ref)
                if not card:
                    continue
                used_refs.add(ref)
                cards.append(card)
            if cards:
                blocks.append(_build_media_block(cards))
        index += 1

    remaining_cards = [
        card for ref, card in media_cards_by_ref.items()
        if ref and ref not in used_refs
    ]
    if remaining_cards:
        title = "相关公式与图表" if not used_refs else "补充公式与图表"
        blocks.append(
            _build_media_block(remaining_cards, title=title)
        )

    return "".join(blocks)


def _render_answer_line(line: str, media_labels_by_ref: dict[str, str]) -> str:
    rendered = html.escape(_strip_stray_brackets(line))
    for ref, label in media_labels_by_ref.items():
        if not ref:
            continue
        rendered = rendered.replace(
            html.escape(f"[{ref}]"),
            f"{html.escape(label)}",
        )
    return rendered


def _strip_stray_brackets(line: str) -> str:
    stripped = line.strip()
    if stripped in {"]", "[", "```", "```latex", "```math"}:
        return ""
    return line


def _is_section_line(line: str) -> bool:
    return any(line.startswith(prefix) for prefix in ["结论：", "分析：", "举例：", "拓展：", "依据："])


def _is_block_math_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) >= 4


def _extract_media_refs(line: str) -> tuple[str, list[str]]:
    refs = re.findall(r"\[\[MEDIA:(.*?)\]\]", line)
    clean_line = re.sub(r"\[\[MEDIA:.*?\]\]", "", line).strip()
    deduped_refs: list[str] = []
    for ref in refs:
        ref = ref.strip()
        if ref and ref not in deduped_refs:
            deduped_refs.append(ref)
    return clean_line, deduped_refs


def _build_media_block(cards: list[str], *, title: str = "相关公式与图表") -> str:
    return f"""
    <div class="answer-media-block">
      <div class="answer-media-title">{html.escape(title)}</div>
      <div class="media-grid">{''.join(cards)}</div>
    </div>
    """


def write_html_report(result: dict, output_path: str) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_html_report(result), encoding="utf-8")
    return target.resolve()


def print_result(result: dict, html_report_path: Path | None = None) -> None:
    print("\n=== plan ===")
    print(json.dumps(result["plan"], ensure_ascii=False, indent=2))

    print("\n=== anchor_nodes ===")
    print(json.dumps(result["anchor_nodes"], ensure_ascii=False, indent=2))

    print("\n=== traversed_nodes ===")
    print(json.dumps(result["traversed_nodes"], ensure_ascii=False, indent=2))

    print("\n=== evidence_items ===")
    print(json.dumps(result["evidence_items"][:10], ensure_ascii=False, indent=2))

    if html_report_path is not None:
        print("\n=== html_report ===")
        print(str(html_report_path))

    print("\n=== answer ===")
    print(result["answer"])


def main() -> None:
    args = parse_args()
    llm_profile = None if args.llm_profile == "default" else args.llm_profile
    pipeline = GraphRAGPipeline(
        enable_llm=not args.disable_llm,
        enable_visual_llm=args.enable_vision,
        llm_profile=llm_profile,
    )

    if args.once:
        result = pipeline.ask(
            args.once,
            traversal_mode=args.mode,
            max_depth_override=args.max_depth,
        )
        html_report_path = None
        if result.get("media_items"):
            output_path = args.html_report or "data/debug_graph_rag/report_latest.html"
            html_report_path = write_html_report(result, output_path)
        print_result(result, html_report_path=html_report_path)
        return

    while True:
        question = input("\n请输入问题（exit 退出）: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break
        result = pipeline.ask(
            question,
            traversal_mode=args.mode,
            max_depth_override=args.max_depth,
        )
        html_report_path = None
        if result.get("media_items"):
            output_path = args.html_report or "data/debug_graph_rag/report_latest.html"
            html_report_path = write_html_report(result, output_path)
        print_result(result, html_report_path=html_report_path)


if __name__ == "__main__":
    main()
