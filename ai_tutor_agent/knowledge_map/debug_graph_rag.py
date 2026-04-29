from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
from pathlib import Path

from dotenv import load_dotenv

from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline
from ai_tutor_agent.platform_paths import resolve_existing_path, resolve_project_path

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

        asset_type = item.get("asset_type")
        if asset_type == "formula":
            formula_raw = str(item.get("text", "") or "").strip()
            formula_text = html.escape(formula_raw)
            formula_attr = html.escape(formula_raw, quote=True)
            preview = f"""
            <button class="media-card formula-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              <div class="formula-scroll formula-viewport"><div class="formula-math formula-render" data-latex="{formula_attr}">{formula_text}</div></div>
            </button>
            """
            modal_body = (
                f"<div class='formula-scroll formula-viewport formula-full'><div class='formula-math formula-render' data-latex=\"{formula_attr}\">{formula_text}</div></div>"
                f"<details class='formula-raw'><summary>查看原始 LaTeX</summary><pre>{formula_text}</pre></details>"
            )
        elif asset_type == "table":
            caption = html.escape(item.get("caption", "") or item.get("title", ""))
            table_html = _sanitize_table_html(str(item.get("text", "") or item.get("raw_text", "")))
            preview = f"""
            <button class="media-card table-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              <div class="media-caption">{caption}</div>
              <div class="table-preview table-viewport">{table_html}</div>
            </button>
            """
            modal_body = f"<div class='table-full table-viewport'>{table_html}</div><p>{caption}</p>"
        else:
            caption = html.escape(item.get("caption", ""))
            paths = item.get("image_paths_abs", []) or []
            preview_img = ""
            gallery = []
            image_sources = [_image_path_to_data_uri(path) for path in paths]
            image_sources = [src for src in image_sources if src]
            if image_sources:
                preview_src = image_sources[0]
                preview_img = f"<img src='{preview_src}' alt='{caption}' loading='lazy' />"
            for uri in image_sources:
                gallery.append(f"<img src='{uri}' alt='{caption}' loading='lazy' />")
            if preview_img:
                preview = f"""
                <button class="media-card figure-card" onclick="openModal('{modal_id}')">
                  <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
                  <div class="media-node">{node_name}</div>
                  <div class="media-caption">{caption}</div>
                  <div class="figure-viewport">{preview_img}</div>
                </button>
                """
                modal_body = f"<div class='figure-gallery figure-viewport'>{''.join(gallery)}</div><p>{caption}</p>"
            else:
                preview = f"""
                <div class="media-card media-unavailable-card" role="note">
                  <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
                  <div class="media-node">{node_name}</div>
                  <div class="media-caption">{caption}</div>
                  <div class="media-unavailable-copy">图像文件暂不可用；已保留图表引用，等待上游素材路径修复后会自动显示真实图。</div>
                </div>
                """
                modal_body = f"<p class='media-unavailable-copy'>图像文件暂不可用：{caption}</p>"

        media_cards_by_ref[item.get("reference", "")] = preview
        modal_cards.append(
            f"""
            <div id="{modal_id}" class="modal" onclick="closeModal('{modal_id}')">
              <div class="modal-content{' modal-content--wide' if asset_type == 'table' else ''}" onclick="event.stopPropagation()">
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
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
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
    .media-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); align-items: stretch; }}
    .media-card {{ width: 100%; min-height: 230px; height: 100%; text-align: left; border: 1px solid #cbd5e1; background: #fff; border-radius: 10px; padding: 12px; cursor: pointer; display: flex; flex-direction: column; gap: 6px; box-sizing: border-box; }}
    .media-card img {{ display: block; width: auto; max-width: 100%; height: auto; max-height: 360px; object-fit: contain; margin: 10px auto 0; border-radius: 6px; background: #f8fafc; }}
    .media-card pre {{ white-space: pre-wrap; word-break: break-word; font-size: 13px; margin: 10px 0 0; }}
    .media-ref {{ font-size: 12px; color: #475569; }}
    .raw-ref {{ color: #94a3b8; }}
    .media-node {{ font-weight: 600; margin-top: 4px; }}
    .media-caption {{ margin-top: 8px; }}
    .modal {{ display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.68); padding: 24px; overflow: auto; }}
    .modal-content {{ max-width: 960px; margin: 0 auto; background: white; border-radius: 8px; padding: 16px; }}
    .modal-content--wide {{ max-width: min(1280px, 96vw); }}
    .figure-gallery {{ display: grid; gap: 12px; grid-template-columns: 1fr; margin-top: 12px; }}
    .figure-gallery img {{ display: block; width: auto; max-width: 100%; height: auto; max-height: 70vh; object-fit: contain; background: #f8fafc; border-radius: 6px; margin: 0 auto; }}
    .formula-scroll, .formula-viewport {{ margin-top: 10px; padding: 12px; border-radius: 6px; background: #f8fafc; overflow: auto; max-width: 100%; max-height: 420px; display: flex; justify-content: center; align-items: flex-start; }}
    .figure-viewport {{ margin-top: 10px; overflow: auto; max-width: 100%; max-height: 70vh; border-radius: 6px; background: #f8fafc; }}
    .formula-scroll.is-overflowing, .formula-viewport.is-overflowing {{ justify-content: flex-start; }}
    .formula-math {{ min-width: max-content; line-height: 1.8; text-align: center; white-space: nowrap; }}
    .formula-math .katex {{ white-space: nowrap; }}
    .formula-full {{ font-size: 18px; }}
    .formula-raw {{ margin-top: 12px; }}
    .formula-raw summary {{ cursor: pointer; color: #475569; }}
    .table-preview, .table-full, .table-viewport {{ margin-top: 10px; overflow: auto; border-radius: 6px; background: #f8fafc; max-width: 100%; max-height: 70vh; }}
    .table-preview table, .table-full table {{ width: max-content; min-width: 100%; border-collapse: collapse; font-size: 13px; }}
    .table-preview th, .table-preview td, .table-full th, .table-full td {{ border: 1px solid #cbd5e1; padding: 6px 8px; vertical-align: top; }}
    .table-preview th, .table-full th {{ background: #eef2ff; font-weight: 700; }}
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
      if (!window.katex) return;
      const root = (!scope || scope === document) ? document : scope;
      root.querySelectorAll('.formula-render').forEach(function(el) {{
        const latex = el.getAttribute('data-latex') || el.textContent || '';
        if (!latex.trim()) return;
        try {{
          katex.render(latex, el, {{ displayMode: true, throwOnError: false, strict: 'ignore' }});
          const scroller = el.closest('.formula-scroll');
          if (scroller && el.scrollWidth > scroller.clientWidth) {{
            scroller.classList.add('is-overflowing');
          }}
        }} catch (err) {{
          console.error(err);
        }}
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


def _image_path_to_data_uri(path: str) -> str:
    try:
        image_path = resolve_existing_path(path) or resolve_project_path(path)
        if not image_path.exists() or not image_path.is_file():
            return ""
        media_type, _ = mimetypes.guess_type(str(image_path))
        if not media_type or not media_type.startswith("image/"):
            media_type = "image/png"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{media_type};base64,{encoded}"
    except OSError:
        return ""


def _sanitize_table_html(table_text: str) -> str:
    raw = str(table_text or "").strip()
    if not raw:
        return "<div class=\"table-empty\">表格内容为空</div>"
    if re.search(r"<\s*table\b", raw, flags=re.IGNORECASE) and re.search(r"<\s*/\s*table\s*>", raw, flags=re.IGNORECASE):
        return _sanitize_basic_table_html(raw)
    markdown_table = _markdown_table_to_html(raw)
    if markdown_table:
        return markdown_table
    return f"<pre>{html.escape(raw)}</pre>"


def _sanitize_basic_table_html(raw: str) -> str:
    allowed_tags = {"table", "thead", "tbody", "tr", "th", "td", "caption"}
    escaped_placeholders: list[str] = []

    def keep_allowed_tag(match: re.Match[str]) -> str:
        token = match.group(0)
        tag_name = match.group(1).lower().lstrip("/")
        if tag_name not in allowed_tags:
            return html.escape(token)
        closing = "/" if token.startswith("</") else ""
        return f"\u0000{len(escaped_placeholders)}\u0000" if _store_placeholder(f"<{closing}{tag_name}>", escaped_placeholders) else ""

    escaped = html.escape(re.sub(r"<\s*(/?)\s*([a-zA-Z0-9]+)(?:\s+[^>]*)?>", lambda m: _escape_or_placeholder_table_tag(m, escaped_placeholders, allowed_tags), raw))
    for idx, tag in enumerate(escaped_placeholders):
        escaped = escaped.replace(html.escape(f"\u0000{idx}\u0000"), tag)
    return escaped


def _escape_or_placeholder_table_tag(match: re.Match[str], placeholders: list[str], allowed_tags: set[str]) -> str:
    tag_name = match.group(2).lower()
    if tag_name not in allowed_tags:
        return match.group(0)
    closing = "/" if match.group(1) else ""
    placeholders.append(f"<{closing}{tag_name}>")
    return f"\u0000{len(placeholders) - 1}\u0000"


def _markdown_table_to_html(raw: str) -> str:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    table_lines = [line for line in lines if "|" in line]
    if len(table_lines) < 2:
        return ""
    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    header, *body = rows
    header_html = "".join(f"<th>{html.escape(cell)}</th>" for cell in header)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in body
    )
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>"


def _store_placeholder(value: str, placeholders: list[str]) -> bool:
    placeholders.append(value)
    return True


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
        plain_refs, next_index = _collect_plain_media_reference_group(
            lines,
            index,
            media_cards_by_ref,
            media_labels_by_ref,
        )
        if plain_refs:
            cards = []
            for ref in plain_refs:
                card = media_cards_by_ref.get(ref)
                if not card:
                    continue
                used_refs.add(ref)
                cards.append(card)
            if cards:
                blocks.append(_build_media_block(cards))
            index = next_index
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
            latex = math_block.strip().removeprefix("$$").removesuffix("$$").strip()
            latex_attr = html.escape(latex, quote=True)
            blocks.append(f"<div class=\"formula-scroll formula-viewport answer-formula\"><div class=\"formula-math formula-render\" data-latex=\"{latex_attr}\">{html.escape(latex)}</div></div>")
            index += 1
            continue
        clean_line, refs = _extract_media_refs(stripped)
        if clean_line:
            if _is_block_math_line(clean_line):
                latex = clean_line.strip().removeprefix("$$").removesuffix("$$").strip()
                latex_attr = html.escape(latex, quote=True)
                blocks.append(
                    f"<div class=\"formula-scroll formula-viewport answer-formula\"><div class=\"formula-math formula-render\" data-latex=\"{latex_attr}\">{html.escape(latex)}</div></div>"
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


def _collect_plain_media_reference_group(
    lines: list[str],
    start_index: int,
    media_cards_by_ref: dict[str, str],
    media_labels_by_ref: dict[str, str],
) -> tuple[list[str], int]:
    first_line = lines[start_index].strip()
    first_ref = _plain_media_reference_line(first_line, media_labels_by_ref)
    if not first_ref or first_ref not in media_cards_by_ref:
        return [], start_index

    refs: list[str] = []
    index = start_index
    while index < len(lines):
        current = lines[index].strip()
        current_ref = _plain_media_reference_line(current, media_labels_by_ref)
        if not current_ref or current_ref not in media_cards_by_ref:
            break
        if current_ref not in refs:
            refs.append(current_ref)
        index += 1
        index = _skip_plain_media_inline_payload(lines, index, media_labels_by_ref)
    return refs, index


def _plain_media_reference_line(line: str, media_labels_by_ref: dict[str, str]) -> str:
    stripped = line.strip()
    for ref, label in sorted(media_labels_by_ref.items(), key=lambda item: len(item[0]), reverse=True):
        ref_text = str(ref or "").strip()
        label_text = str(label or "").strip()
        if not ref_text:
            continue
        bare_ref = f"[{ref_text}]"
        labeled_ref = f"{label_text} {bare_ref}" if label_text else bare_ref
        if stripped == bare_ref or stripped == labeled_ref:
            return ref_text
    match = re.fullmatch(r"([^\[]*)\[(.+)\]\s*", stripped)
    if not match:
        return ""
    label_text = match.group(1).strip()
    ref = match.group(2).strip()
    expected_label = str(media_labels_by_ref.get(ref, "")).strip()
    if expected_label and label_text and label_text != expected_label:
        return ""
    return ref


def _skip_plain_media_inline_payload(
    lines: list[str],
    index: int,
    media_labels_by_ref: dict[str, str],
) -> int:
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if _plain_media_reference_line(stripped, media_labels_by_ref):
            return index
        if stripped == "$$":
            index += 1
            while index < len(lines):
                if lines[index].strip() == "$$":
                    index += 1
                    break
                index += 1
            continue
        if _is_plain_media_payload_line(stripped):
            index += 1
            continue
        break
    return index


def _is_plain_media_payload_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _is_section_line(stripped):
        return False
    if stripped.startswith(("结论：", "分析：", "举例：", "拓展：", "依据：")):
        return False
    if re.match(r"^(图|表)\s*\d", stripped):
        return True
    if stripped.endswith(("概念", "分类", "方式", "原理", "分析", "指标", "框图", "示意图", "曲线", "表")):
        return True
    return False


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
    target = resolve_project_path(output_path)
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
