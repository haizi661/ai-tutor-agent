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

MAX_LEARNING_RELATED_MEDIA_CARDS = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug graph-based RAG over the knowledge map.")
    parser.add_argument("--mode", choices=["focused", "balanced", "exploratory"], default="balanced")
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--disable-llm", action="store_true")
    parser.add_argument("--enable-vision", action="store_true")
    parser.add_argument("--llm-profile", choices=["qwen", "default"], default="qwen")
    parser.add_argument("--once", type=str, default="")
    parser.add_argument("--html-report", type=str, default="")
    parser.add_argument(
        "--learning-html",
        type=str,
        default="",
        help="Write the main learning-flow HTML fragment separately from the full debug report.",
    )
    return parser.parse_args(argv)


def _normalize_latex_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"^```(?:latex|math|tex)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()
    wrappers = [
        ("$$", "$$"),
        (r"\[", r"\]"),
        (r"\(", r"\)"),
    ]
    changed = True
    while changed and text:
        changed = False
        for left, right in wrappers:
            if text.startswith(left) and text.endswith(right) and len(text) >= len(left) + len(right):
                text = text[len(left) : len(text) - len(right)].strip()
                changed = True
    return text


def _canonical_latex_text(value: str) -> str:
    return re.sub(r"\s+", "", _normalize_latex_text(value))


def _canonical_plain_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def _build_learning_media_metadata(media_items: list[dict]) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]]]:
    media_types_by_ref: dict[str, str] = {}
    formula_refs_by_latex: dict[str, list[str]] = {}
    table_refs_by_text: dict[str, list[str]] = {}

    for item in media_items:
        ref = str(item.get("reference", "") or "").strip()
        if not ref:
            continue
        asset_type = str(item.get("asset_type", "") or "").strip()
        media_types_by_ref[ref] = asset_type
        if asset_type == "formula":
            key = _canonical_latex_text(str(item.get("text", "") or item.get("raw_text", "")))
            if key:
                formula_refs_by_latex.setdefault(key, []).append(ref)
        elif asset_type == "table":
            for value in [item.get("text", ""), item.get("raw_text", ""), item.get("caption", ""), item.get("title", "")]:
                key = _canonical_plain_text(str(value or ""))
                if key:
                    table_refs_by_text.setdefault(key, []).append(ref)

    return media_types_by_ref, formula_refs_by_latex, table_refs_by_text


def _build_learning_table_raw_by_ref(media_items: list[dict]) -> dict[str, str]:
    table_raw_by_ref: dict[str, str] = {}
    for item in media_items:
        if str(item.get("asset_type", "") or "").strip() != "table":
            continue
        ref = str(item.get("reference", "") or "").strip()
        raw = str(item.get("text", "") or item.get("raw_text", "") or "").strip()
        if ref and raw:
            table_raw_by_ref[ref] = raw
    return table_raw_by_ref


def _display_label_for_learning_item(asset_type: str, fallback_label: str, ordinal: int) -> str:
    if asset_type == "formula":
        return f"式{_to_chinese_numeral(ordinal)}"
    if asset_type == "table":
        return f"表{_to_chinese_numeral(ordinal)}"
    if asset_type == "figure":
        return f"图{_to_chinese_numeral(ordinal)}"
    return fallback_label or f"媒体{ordinal}"


def _renumber_table_caption(caption: str, display_label: str) -> str:
    text = str(caption or "").strip()
    if not text:
        return ""
    return re.sub(r"^表\s*[一二三四五六七八九十百千万零〇两\d]+", display_label, text, count=1)


def _to_chinese_numeral(number: int) -> str:
    numerals = {
        0: "零",
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九",
        10: "十",
    }
    if number in numerals:
        return numerals[number]
    if number < 20:
        return "十" + numerals[number - 10]
    tens, ones = divmod(number, 10)
    if ones == 0:
        return numerals.get(tens, str(tens)) + "十"
    return numerals.get(tens, str(tens)) + "十" + numerals.get(ones, str(ones))


def _media_hint(item: dict) -> str:
    candidates = [
        item.get("analysis_hint", ""),
        item.get("formula_meaning", ""),
        item.get("visual_summary", ""),
        item.get("relation_statement", ""),
    ]
    caption = str(item.get("caption", "") or item.get("title", "") or "").strip()
    for value in candidates:
        text = str(value or "").strip()
        if text and text != caption:
            return text
    return ""


def _learning_source_label(item: dict) -> str:
    node_name = str(item.get("node_name", "") or "").strip()
    if node_name:
        return f"来源：{node_name}"
    caption = str(item.get("caption", "") or item.get("title", "") or "").strip()
    if caption:
        return f"来源：{caption}"
    return "来源：知识图谱检索结果"


def _learning_debug_details(raw_ref: str, *, latex: str = "") -> str:
    ref_text = html.escape(str(raw_ref or ""))
    details = (
        '<details class="learning-debug-details">'
        '<summary>查看来源详情</summary>'
        f'<code>{ref_text}</code>'
        '</details>'
    )
    if latex:
        latex_text = html.escape(latex)
        details += (
            '<details class="learning-latex-details">'
            '<summary>查看 LaTeX</summary>'
            f'<pre>{latex_text}</pre>'
            '</details>'
        )
    return details


def _build_learning_media_render_parts(media_items: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    media_cards_by_ref: dict[str, str] = {}
    media_labels_by_ref: dict[str, str] = {}

    ordinals_by_type = {"formula": 0, "figure": 0, "table": 0}
    for idx, item in enumerate(media_items, start=1):
        raw_ref = str(item.get("reference", "") or "").strip()
        if not raw_ref:
            continue
        asset_type = str(item.get("asset_type") or "").strip()
        if asset_type in ordinals_by_type:
            ordinals_by_type[asset_type] += 1
            ordinal = ordinals_by_type[asset_type]
        else:
            ordinal = idx
        fallback_label = str(item.get("display_label", f"媒体{idx}") or f"媒体{idx}").strip()
        display_label_raw = _display_label_for_learning_item(asset_type, fallback_label, ordinal)
        display_label = html.escape(display_label_raw)
        node_name_raw = str(item.get("node_name", "") or "").strip()
        node_name = html.escape(node_name_raw)
        source_line = html.escape(_learning_source_label(item))
        hint = html.escape(_media_hint(item))
        hint_html = f'<div class="learning-evidence-summary">{hint}</div>' if hint else ""
        media_labels_by_ref[raw_ref] = display_label_raw
        title = node_name or display_label

        if asset_type == "formula":
            formula_raw = _normalize_latex_text(str(item.get("text", "") or ""))
            formula_text = html.escape(formula_raw)
            formula_attr = html.escape(formula_raw, quote=True)
            media_cards_by_ref[raw_ref] = f"""
            <section class="learning-evidence-card learning-evidence-card--formula learning-formula-card">
              <div class="learning-block-header learning-evidence-header">
                <div>
                  <span class="learning-evidence-type">公式</span>
                  <div class="learning-block-title learning-evidence-title">{display_label} · {title}</div>
                </div>
                <div class="learning-block-actions"><button type="button" data-learning-action="open">放大</button><button type="button" data-learning-action="copy">复制公式</button></div>
              </div>
              {hint_html}
              <div class="learning-formula-viewport"><div class="formula-math formula-render" data-latex="{formula_attr}">{formula_text}</div></div>
              <div class="learning-source-line">{source_line}</div>
              {_learning_debug_details(raw_ref, latex=formula_raw)}
            </section>
            """
        elif asset_type == "table":
            caption_raw = _renumber_table_caption(str(item.get("caption", "") or item.get("title", "")), display_label_raw)
            caption = html.escape(caption_raw)
            table_html = _sanitize_table_html(str(item.get("text", "") or item.get("raw_text", "")))
            caption_html = f'<div class="learning-block-caption">{caption}</div>' if caption else ""
            media_cards_by_ref[raw_ref] = f"""
            <section class="learning-evidence-card learning-evidence-card--table learning-table-card">
              <div class="learning-block-header learning-evidence-header">
                <div>
                  <span class="learning-evidence-type">表格</span>
                  <div class="learning-block-title learning-evidence-title">{display_label} · {title}</div>
                </div>
                <div class="learning-block-actions"><button type="button" data-learning-action="open">放大</button><button type="button" data-learning-action="copy">复制表格</button></div>
              </div>
              {caption_html}
              {hint_html}
              <div class="learning-table-viewport">{table_html}</div>
              <div class="learning-source-line">{source_line}</div>
              {_learning_debug_details(raw_ref)}
            </section>
            """
        else:
            caption_raw = str(item.get("caption", "") or "").strip()
            caption = html.escape(caption_raw)
            figure_title = caption or title
            paths = item.get("image_paths_abs", []) or []
            image_sources = [_image_path_to_data_uri(path) for path in paths]
            image_sources = [src for src in image_sources if src]
            caption_html = f'<div class="learning-block-caption">{caption}</div>' if caption else ""
            if image_sources:
                preview_img = f"<img src='{image_sources[0]}' alt='{caption}' loading='lazy' />"
                figure_body = f'<div class="learning-figure-viewport">{preview_img}</div>'
                actions = '<button type="button" data-learning-action="open">放大</button><button type="button" data-learning-action="copy">复制引用</button>'
            else:
                figure_body = (
                    '<div class="learning-figure-viewport learning-figure-unavailable" role="note">'
                    '<strong>图表暂时无法预览</strong>'
                    '<span>已检索到图表引用，但本地图片资产暂不可用。</span>'
                    '</div>'
                )
                actions = '<span>图表暂不可用</span>'
            media_cards_by_ref[raw_ref] = f"""
            <section class="learning-evidence-card learning-evidence-card--figure learning-figure-card">
              <div class="learning-block-header learning-evidence-header">
                <div>
                  <span class="learning-evidence-type">图表</span>
                  <div class="learning-block-title learning-evidence-title">{display_label} · {figure_title}</div>
                </div>
                <div class="learning-block-actions">{actions}</div>
              </div>
              {figure_body}
              {caption_html}
              {hint_html}
              <div class="learning-source-line">{source_line}</div>
              {_learning_debug_details(raw_ref)}
            </section>
            """

    return media_cards_by_ref, media_labels_by_ref

def _build_media_render_parts(media_items: list[dict]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    media_cards_by_ref: dict[str, str] = {}
    media_labels_by_ref: dict[str, str] = {}
    modal_cards: list[str] = []

    for idx, item in enumerate(media_items, start=1):
        raw_ref = str(item.get("reference", "") or "").strip()
        ref = html.escape(raw_ref)
        display_label = html.escape(item.get("display_label", f"媒体{idx}"))
        node_name = html.escape(item.get("node_name", ""))
        hint = html.escape(_media_hint(item))
        hint_html = f'<div class="media-caption media-hint">{hint}</div>' if hint else ""
        ref_slug = re.sub(r"[^A-Za-z0-9_-]+", "-", raw_ref).strip("-")[:42] or str(idx)
        modal_id = f"media-modal-{idx}-{ref_slug}"
        media_labels_by_ref[raw_ref] = item.get("display_label", f"媒体{idx}")

        asset_type = item.get("asset_type")
        if asset_type == "formula":
            formula_raw = _normalize_latex_text(str(item.get("text", "") or ""))
            formula_text = html.escape(formula_raw)
            formula_attr = html.escape(formula_raw, quote=True)
            preview = f"""
            <button type="button" class="media-card formula-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              {hint_html}
              <div class="formula-scroll formula-viewport"><div class="formula-math formula-render" data-latex="{formula_attr}">{formula_text}</div></div>
            </button>
            """
            modal_body = (
                f"{hint_html}"
                f"<div class='formula-scroll formula-viewport formula-full'><div class='formula-math formula-render' data-latex=\"{formula_attr}\">{formula_text}</div></div>"
                f"<details class='formula-raw'><summary>查看原始 LaTeX</summary><pre>{formula_text}</pre></details>"
            )
        elif asset_type == "table":
            caption = html.escape(item.get("caption", "") or item.get("title", ""))
            table_html = _sanitize_table_html(str(item.get("text", "") or item.get("raw_text", "")))
            preview = f"""
            <button type="button" class="media-card table-card" onclick="openModal('{modal_id}')">
              <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
              <div class="media-node">{node_name}</div>
              <div class="media-caption">{caption}</div>
              {hint_html}
              <div class="table-preview table-viewport">{table_html}</div>
            </button>
            """
            modal_body = f"<div class='table-full table-viewport'>{table_html}</div><p>{caption}</p>{hint_html}"
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
                <button type="button" class="media-card figure-card" onclick="openModal('{modal_id}')">
                  <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
                  <div class="media-node">{node_name}</div>
                  <div class="media-caption">{caption}</div>
                  {hint_html}
                  <div class="figure-viewport">{preview_img}</div>
                </button>
                """
                modal_body = f"<div class='figure-gallery figure-viewport'>{''.join(gallery)}</div><p>{caption}</p>{hint_html}"
            else:
                preview = f"""
                <div class="media-card media-unavailable-card" role="note">
                  <div class="media-ref">{display_label} <span class="raw-ref">[{ref}]</span></div>
                  <div class="media-node">{node_name}</div>
                  <div class="media-caption">{caption}</div>
                  {hint_html}
                  <div class="media-unavailable-copy">图像文件暂不可用；已保留图表引用，等待上游素材路径修复后会自动显示真实图。</div>
                </div>
                """
                modal_body = f"<p class='media-unavailable-copy'>图像文件暂不可用：{caption}</p>"

        media_cards_by_ref[raw_ref] = preview
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
    return media_cards_by_ref, media_labels_by_ref, modal_cards


def _build_learning_evidence_card(evidence_items: list[dict]) -> str:
    rows = "".join(
        "<li>"
        f"<span>{html.escape(str(item.get('text', '')))}</span>"
        f"<details class=\"learning-debug-details\"><summary>查看来源详情</summary><code>{html.escape(str(item.get('reference', '')))}</code></details>"
        "</li>"
        for item in evidence_items[:4]
        if str(item.get("reference", "") or item.get("text", "")).strip()
    )
    if not rows:
        return ""
    return (
        '<section class="learning-evidence-card learning-evidence-card--source">'
        '<div class="learning-block-header"><div class="learning-block-title">参考依据</div></div>'
        f'<ol>{rows}</ol>'
        '</section>'
    )


def build_learning_answer_html(result: dict) -> str:
    media_items = list(result.get("media_items", []) or [])
    media_cards_by_ref, media_labels_by_ref = _build_learning_media_render_parts(media_items)
    media_types_by_ref, formula_refs_by_latex, table_refs_by_text = _build_learning_media_metadata(media_items)
    table_raw_by_ref = _build_learning_table_raw_by_ref(media_items)
    used_media_refs: set[str] = set()
    answer_html = _render_answer_html(
        str(result.get("answer", "")),
        media_cards_by_ref,
        media_labels_by_ref,
        media_types_by_ref=media_types_by_ref,
        formula_refs_by_latex=formula_refs_by_latex,
        table_refs_by_text=table_refs_by_text,
        table_raw_by_ref=table_raw_by_ref,
        media_block_renderer=_build_learning_reference_media_block,
        formula_block_renderer=_build_learning_answer_formula_block,
        linked_block_renderer=_build_learning_linked_block,
        used_media_refs=used_media_refs,
    )
    remaining_cards = _select_learning_related_media_cards(media_cards_by_ref, used_media_refs)
    if remaining_cards:
        answer_html += _build_learning_related_overview_block(remaining_cards)
    evidence_html = _build_learning_evidence_card(list(result.get("evidence_items", []) or []))
    return f'<div class="learning-answer-content">{answer_html}{evidence_html}</div>'


def _select_learning_related_media_cards(
    media_cards_by_ref: dict[str, str],
    used_media_refs: set[str],
) -> list[str]:
    cards: list[str] = []
    seen_cards: set[str] = set()
    for ref, card in media_cards_by_ref.items():
        if ref in used_media_refs or not card or card in seen_cards:
            continue
        seen_cards.add(card)
        cards.append(card)
        if len(cards) >= MAX_LEARNING_RELATED_MEDIA_CARDS:
            break
    return cards


def build_answer_media_html(result: dict) -> str:
    media_cards_by_ref, media_labels_by_ref, modal_cards = _build_media_render_parts(result.get("media_items", []))
    answer_html = _render_answer_html(str(result.get("answer", "")), media_cards_by_ref, media_labels_by_ref)
    evidence_rows = "".join(
        f"<li><strong>{html.escape(str(item.get('reference', '')))}</strong> {html.escape(str(item.get('text', '')))}</li>"
        for item in result.get("evidence_items", [])[:4]
        if str(item.get("reference", "") or item.get("text", "")).strip()
    )
    evidence_html = (
        f"""
        <section class="graph-rag-evidence-panel">
          <h2>依据</h2>
          <ol>{evidence_rows}</ol>
        </section>
        """
        if evidence_rows
        else ""
    )
    return f"""
    <section class="graph-rag-answer-panel">
      <div class="answer">{answer_html}</div>
    </section>
    {evidence_html}
    {''.join(modal_cards)}
    """


def build_html_report(result: dict) -> str:
    media_cards_by_ref, media_labels_by_ref, modal_cards = _build_media_render_parts(result.get("media_items", []))

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
    .media-card {{ width: 100%; min-width: 0; min-height: 230px; height: 100%; text-align: left; border: 1px solid #cbd5e1; background: #fff; border-radius: 10px; padding: 12px; cursor: pointer; display: flex; flex-direction: column; gap: 6px; box-sizing: border-box; }}
    .media-card img {{ display: block; width: auto; max-width: 100%; height: auto; max-height: 360px; object-fit: contain; margin: 10px auto 0; border-radius: 6px; background: #f8fafc; }}
    .media-card pre {{ white-space: pre-wrap; word-break: break-word; font-size: 13px; margin: 10px 0 0; }}
    .media-ref {{ font-size: 12px; color: #475569; }}
    .raw-ref {{ color: #94a3b8; }}
    .media-node {{ font-weight: 600; margin-top: 4px; }}
    .media-caption {{ margin-top: 8px; }}
    .media-hint {{ color: #334155; font-size: 13px; line-height: 1.6; }}
    .modal {{ display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.68); padding: 24px; overflow: auto; }}
    .modal-content {{ width: min(100%, 1040px); max-width: calc(100vw - 48px); margin: 0 auto; background: white; border-radius: 8px; padding: 16px; }}
    .modal-content--wide {{ max-width: min(1280px, 96vw); }}
    .figure-gallery {{ display: grid; gap: 12px; grid-template-columns: 1fr; margin-top: 12px; }}
    .figure-gallery img {{ display: block; width: auto; max-width: 100%; height: auto; max-height: 70vh; object-fit: contain; background: #f8fafc; border-radius: 6px; margin: 0 auto; }}
    .formula-scroll, .formula-viewport {{ margin-top: 10px; padding: 12px; border-radius: 6px; background: #f8fafc; overflow: auto; max-width: 100%; max-height: 420px; display: flex; justify-content: center; align-items: flex-start; box-sizing: border-box; }}
    .figure-viewport {{ margin-top: 10px; overflow: auto; max-width: 100%; max-height: 70vh; border-radius: 6px; background: #f8fafc; }}
    .formula-scroll.is-overflowing, .formula-viewport.is-overflowing {{ justify-content: flex-start; }}
    .formula-math {{ min-width: max-content; max-width: none; line-height: 1.8; text-align: center; white-space: nowrap; }}
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

    escaped = html.escape(
        re.sub(
            r"<\s*(/?)\s*([a-zA-Z0-9]+)([^>]*)>",
            lambda m: _escape_or_placeholder_table_tag(m, escaped_placeholders, allowed_tags),
            raw,
        )
    )
    for idx, tag in enumerate(escaped_placeholders):
        escaped = escaped.replace(html.escape(f"\u0000{idx}\u0000"), tag)
    return escaped


def _escape_or_placeholder_table_tag(match: re.Match[str], placeholders: list[str], allowed_tags: set[str]) -> str:
    tag_name = match.group(2).lower()
    if tag_name not in allowed_tags:
        return match.group(0)
    closing = "/" if match.group(1) else ""
    attrs = ""
    if not closing and tag_name in {"td", "th"}:
        attrs = _sanitize_table_cell_attrs(match.group(3) or "")
    placeholders.append(f"<{closing}{tag_name}{attrs}>")
    return f"\u0000{len(placeholders) - 1}\u0000"


def _sanitize_table_cell_attrs(raw_attrs: str) -> str:
    safe_attrs: list[str] = []
    for attr_name, _, attr_value in re.findall(r"\b(rowspan|colspan)\s*=\s*(['\"]?)(\d{1,2})\2", raw_attrs, flags=re.IGNORECASE):
        value = max(1, min(int(attr_value), 20))
        safe_attrs.append(f'{attr_name.lower()}="{value}"')
    return (" " + " ".join(safe_attrs)) if safe_attrs else ""

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


def _is_formula_line(line: str) -> bool:
    stripped = line.strip()
    return bool(
        (stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4)
        or (stripped.startswith("\\[") and stripped.endswith("\\]"))
    )


def _collect_markdown_table(lines: list[str], index: int) -> tuple[list[str], int]:
    if index >= len(lines) or "|" not in lines[index]:
        return [], index
    table_lines: list[str] = []
    cursor = index
    while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
        table_lines.append(lines[cursor].strip())
        cursor += 1
    if len(table_lines) < 2:
        return [], index
    return table_lines, cursor


def _render_markdown_table(table_lines: list[str]) -> str:
    return _markdown_table_to_html("\n".join(table_lines))


def _render_answer_html(
    answer_text: str,
    media_cards_by_ref: dict[str, str],
    media_labels_by_ref: dict[str, str],
    *,
    media_types_by_ref: dict[str, str] | None = None,
    formula_refs_by_latex: dict[str, list[str]] | None = None,
    table_refs_by_text: dict[str, list[str]] | None = None,
    table_raw_by_ref: dict[str, str] | None = None,
    media_block_renderer: callable = None,
    formula_block_renderer: callable = None,
    linked_block_renderer: callable = None,
    used_media_refs: set[str] | None = None,
) -> str:
    if media_block_renderer is None:
        media_block_renderer = _build_media_block
    if formula_block_renderer is None:
        formula_block_renderer = _build_answer_formula_block
    is_learning_flow = linked_block_renderer is not None
    media_types_by_ref = media_types_by_ref or {}
    formula_refs_by_latex = formula_refs_by_latex or {}
    table_refs_by_text = table_refs_by_text or {}
    table_raw_by_ref = table_raw_by_ref or {}
    lines = [line.rstrip() for line in answer_text.splitlines()]
    raw_blocks: list[tuple[str, str, list[str], bool]] = []
    used_refs: set[str] = used_media_refs if used_media_refs is not None else set()
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
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
            if is_learning_flow:
                raw_blocks.append(("media_ref", "", plain_refs, True))
            else:
                media_block = _build_media_block_for_refs(
                    plain_refs,
                    media_cards_by_ref,
                    used_refs,
                    title="相关公式与图表",
                    media_block_renderer=media_block_renderer,
                )
                if media_block:
                    raw_blocks.append(("media", media_block, [], False))
            index = next_index
            continue
        if stripped == "$$":
            math_lines: list[str] = ["$$"]
            index += 1
            while index < len(lines):
                math_lines.append(lines[index].rstrip())
                if lines[index].strip() == "$$":
                    break
                index += 1
            math_block = "\n".join(math_lines)
            latex = _normalize_latex_text(math_block)
            formula_ref = _find_media_ref_for_formula(latex, formula_refs_by_latex, used_refs)
            if formula_ref:
                raw_blocks.append(("media_ref", "", [formula_ref], True))
            else:
                raw_blocks.append(("formula", formula_block_renderer(latex), [], False))
            index += 1
            continue
        table_lines, next_index = _collect_markdown_table(lines, index)
        if table_lines:
            table_ref = _find_media_ref_for_table(table_lines, table_refs_by_text, used_refs)
            if table_ref:
                raw_blocks.append(("media_ref", "", [table_ref], True))
            else:
                raw_blocks.append(("table", f'<div class="answer-table">{_render_markdown_table(table_lines)}</div>', [], False))
            index = next_index
            continue
        clean_line, refs = _extract_media_refs(stripped, media_cards_by_ref)
        line_block = ""
        if clean_line:
            if _is_formula_line(clean_line):
                latex = _normalize_latex_text(clean_line)
                formula_ref = _find_media_ref_for_formula(latex, formula_refs_by_latex, used_refs)
                if formula_ref:
                    refs.append(formula_ref)
                else:
                    line_block = formula_block_renderer(latex)
            else:
                if is_learning_flow and _is_redundant_table_reference_line(clean_line, refs, media_types_by_ref):
                    line_block = ""
                else:
                    rendered_line = _render_answer_line(clean_line, media_labels_by_ref, refs)
                    if _is_section_line(clean_line):
                        line_block = f"<p class=\"section-title\">{rendered_line}</p>"
                    else:
                        line_block = f"<p>{rendered_line}</p>"
                refs.extend(_refs_mentioned_by_label(clean_line, media_cards_by_ref, media_labels_by_ref))
        next_index_after_payload = _skip_media_payload_after_refs(
            lines,
            index + 1,
            refs,
            media_labels_by_ref,
            media_types_by_ref,
            table_raw_by_ref,
        ) if refs else index + 1
        if line_block:
            raw_blocks.append(("text", line_block, refs, False))
        elif refs:
            raw_blocks.append(("media_ref", "", refs, True))
        index = next_index_after_payload

    if not is_learning_flow:
        planned_refs = {
            ref
            for _, _, refs, _ in raw_blocks
            for ref in refs
            if ref
        }
        remaining_refs = [ref for ref in media_cards_by_ref if ref not in used_refs and ref not in planned_refs]
        if remaining_refs:
            insert_at = _find_primary_media_insert_index([block_html for _, block_html, _, _ in raw_blocks])
            media_block = _build_media_block_for_refs(
                remaining_refs,
                media_cards_by_ref,
                used_refs,
                title="图谱检索到的相关公式与图表",
                media_block_renderer=media_block_renderer,
            )
            if media_block:
                raw_blocks.insert(insert_at, ("media", media_block, [], False))

    merged_blocks: list[str] = []
    pending_refs: list[str] = []
    for block_kind, block_html, refs, standalone_media_ref in raw_blocks:
        block_refs = list(pending_refs)
        pending_refs = []
        block_refs.extend(refs)
        if block_kind == "media_ref" and block_refs:
            pending_refs.extend(block_refs)
            continue
        media_block = ""
        if block_refs:
            media_block = _build_media_block_for_refs(
                block_refs,
                media_cards_by_ref,
                used_refs,
                title="相关公式与图表" if (standalone_media_ref or is_learning_flow) else "正文引用的相关公式与图表",
                media_block_renderer=media_block_renderer,
            )
        if media_block and linked_block_renderer:
            merged_blocks.append(linked_block_renderer(block_html, media_block))
        else:
            if block_html:
                merged_blocks.append(block_html)
            if media_block:
                merged_blocks.append(media_block)
    if pending_refs:
        media_block = _build_media_block_for_refs(
            pending_refs,
            media_cards_by_ref,
            used_refs,
            title="相关公式与图表",
            media_block_renderer=media_block_renderer,
        )
        if media_block:
            if linked_block_renderer:
                merged_blocks.append(linked_block_renderer("", media_block))
            else:
                merged_blocks.append(media_block)
    return "".join(merged_blocks)


def _find_media_ref_for_formula(
    latex: str,
    formula_refs_by_latex: dict[str, list[str]],
    used_refs: set[str],
) -> str:
    key = _canonical_latex_text(latex)
    if not key:
        return ""
    for ref in formula_refs_by_latex.get(key, []):
        if ref not in used_refs:
            return ref
    return ""


def _find_media_ref_for_table(
    table_lines: list[str],
    table_refs_by_text: dict[str, list[str]],
    used_refs: set[str],
) -> str:
    rendered = _render_markdown_table(table_lines)
    candidates = [
        _canonical_plain_text(rendered),
        _canonical_plain_text("\n".join(table_lines)),
    ]
    for key in candidates:
        if not key:
            continue
        for ref in table_refs_by_text.get(key, []):
            if ref not in used_refs:
                return ref
    return ""


def _build_answer_formula_block(latex: str) -> str:
    formula_raw = _normalize_latex_text(latex)
    formula_text = html.escape(formula_raw)
    formula_attr = html.escape(formula_raw, quote=True)
    return (
        '<div class="formula-scroll formula-viewport answer-formula">'
        f'<div class="formula-math formula-render" data-latex="{formula_attr}">{formula_text}</div>'
        '</div>'
    )


def _build_learning_answer_formula_block(latex: str) -> str:
    formula_raw = _normalize_latex_text(latex)
    formula_text = html.escape(formula_raw)
    formula_attr = html.escape(formula_raw, quote=True)
    return f"""
    <section class="learning-formula-card learning-inline-formula-card">
      <div class="learning-block-header">
        <div class="learning-block-title">公式</div>
        <div class="learning-block-actions"><button type="button" data-learning-action="open">放大</button><button type="button" data-learning-action="copy">复制</button></div>
      </div>
      <div class="learning-formula-viewport"><div class="formula-math formula-render" data-latex="{formula_attr}">{formula_text}</div></div>
    </section>
    """


def _build_learning_linked_block(text_html: str, media_html: str) -> str:
    text_part = f'<div class="learning-reference-text">{text_html}</div>' if text_html else ""
    return (
        '<section class="learning-reference-block">'
        f'{text_part}'
        f'<div class="learning-reference-media">{media_html}</div>'
        '</section>'
    )


def _is_learning_reference_media_block(block_html: str) -> bool:
    return "learning-reference-media-grid" in block_html


def _build_learning_reference_media_block(cards: list[str], *, title: str = "相关公式与图表") -> str:
    title_html = f'<div class="learning-reference-media-title">{html.escape(title)}</div>' if title else ""
    return f'{title_html}<div class="learning-reference-media-grid learning-media-group">{"".join(cards)}</div>'


def _build_learning_related_overview_block(cards: list[str]) -> str:
    return _build_learning_media_block(cards, title="更多可参考的公式与图表", extra_class="learning-related-overview")


def _build_media_block_for_refs(
    refs: list[str],
    media_cards_by_ref: dict[str, str],
    used_refs: set[str],
    *,
    title: str,
    media_block_renderer: callable = None,
) -> str:
    if media_block_renderer is None:
        media_block_renderer = _build_media_block
    cards: list[str] = []
    ordered_refs = [ref for ref in media_cards_by_ref if ref in refs]
    for ref in ordered_refs:
        if not ref or ref in used_refs:
            continue
        card = media_cards_by_ref.get(ref)
        if not card:
            continue
        used_refs.add(ref)
        cards.append(card)
    if not cards:
        return ""
    return media_block_renderer(cards, title=title)


def _find_primary_media_insert_index(blocks: list[str]) -> int:
    for idx, block in enumerate(blocks):
        if 'class="section-title">分析：' in block:
            return idx + 1
    for idx, block in enumerate(blocks):
        if "<p>" in block or 'class="section-title">结论：' in block:
            return idx + 1
    return len(blocks)


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


def _skip_media_payload_after_refs(
    lines: list[str],
    index: int,
    refs: list[str],
    media_labels_by_ref: dict[str, str],
    media_types_by_ref: dict[str, str],
    table_raw_by_ref: dict[str, str] | None = None,
) -> int:
    ref_types = {
        str(media_types_by_ref.get(ref, "") or "").strip()
        for ref in refs
        if str(media_types_by_ref.get(ref, "") or "").strip()
    }
    if not ref_types:
        return index
    table_raw_by_ref = table_raw_by_ref or {}

    if "table" in ref_types:
        raw_table_end = _skip_raw_html_table_payload(lines, index, refs, table_raw_by_ref)
        if raw_table_end > index:
            index = raw_table_end

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if _plain_media_reference_line(stripped, media_labels_by_ref):
            return index
        if "formula" in ref_types and stripped == "$$":
            index += 1
            while index < len(lines):
                if lines[index].strip() == "$$":
                    index += 1
                    break
                index += 1
            continue
        if "formula" in ref_types and _is_formula_line(stripped):
            index += 1
            continue
        if "table" in ref_types:
            table_lines, next_index = _collect_markdown_table(lines, index)
            if table_lines:
                index = next_index
                continue
        if _is_plain_media_payload_line(stripped):
            index += 1
            continue
        break
    return index


def _is_redundant_table_reference_line(line: str, refs: list[str], media_types_by_ref: dict[str, str]) -> bool:
    if not refs:
        return False
    if not all(str(media_types_by_ref.get(ref, "") or "").strip() == "table" for ref in refs):
        return False
    stripped = line.strip()
    if not stripped.startswith(("分析：", "依据：", "结论：")):
        return False
    return bool(re.search(r"表\s*[一二三四五六七八九十百千万零〇两\d]+", stripped)) and any(
        phrase in stripped for phrase in ["总结", "列出", "如下", "见表", "如表"]
    )


def _skip_raw_html_table_payload(
    lines: list[str],
    index: int,
    refs: list[str],
    table_raw_by_ref: dict[str, str],
) -> int:
    if index >= len(lines):
        return index
    raw_candidates = [_canonical_plain_text(table_raw_by_ref.get(ref, "")) for ref in refs]
    raw_candidates = [candidate for candidate in raw_candidates if candidate]
    if not raw_candidates:
        return index
    buffer: list[str] = []
    for cursor in range(index, min(len(lines), index + 200)):
        stripped = lines[cursor].strip()
        if not stripped and not buffer:
            continue
        buffer.append(stripped)
        joined = "\n".join(buffer)
        joined_key = _canonical_plain_text(joined)
        if any(joined_key == candidate or joined_key in candidate or candidate in joined_key for candidate in raw_candidates):
            return cursor + 1
        if "</table>" in stripped.lower():
            return cursor + 1
        if buffer and len(joined_key) > max(len(candidate) for candidate in raw_candidates) * 2:
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


def _render_answer_line(line: str, media_labels_by_ref: dict[str, str], refs: list[str] | None = None) -> str:
    cleaned = _strip_stray_brackets(line)
    scoped_refs = refs if refs else list(media_labels_by_ref.keys())
    for ref in scoped_refs:
        if not ref:
            continue
        ref_text = str(ref)
        label_text = str(media_labels_by_ref.get(ref, "") or "").strip()
        if label_text:
            if label_text.startswith("表"):
                cleaned = re.sub(
                    r"表\s*[一二三四五六七八九十百千万零〇两\d]+",
                    label_text,
                    cleaned,
                    count=1,
                )
            cleaned = re.sub(
                rf"{re.escape(label_text)}\s*\[\[MEDIA:{re.escape(ref_text)}\]\]",
                label_text,
                cleaned,
            )
            cleaned = re.sub(
                rf"{re.escape(label_text)}\s*\[{re.escape(ref_text)}\]",
                label_text,
                cleaned,
            )
            cleaned = cleaned.replace(f"[[MEDIA:{ref_text}]]", label_text)
            cleaned = cleaned.replace(f"[{ref_text}]", label_text)
    return html.escape(cleaned)


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


def _refs_mentioned_by_label(
    line: str,
    media_cards_by_ref: dict[str, str],
    media_labels_by_ref: dict[str, str],
) -> list[str]:
    deduped_refs: list[str] = []
    for ref, label in sorted(media_labels_by_ref.items(), key=lambda item: len(str(item[1] or "")), reverse=True):
        ref_text = str(ref or "").strip()
        label_text = str(label or "").strip()
        if not ref_text or ref_text not in media_cards_by_ref or not label_text:
            continue
        if label_text not in line:
            continue
        if ref_text not in deduped_refs:
            deduped_refs.append(ref_text)
    return deduped_refs


def _extract_media_refs(line: str, media_cards_by_ref: dict[str, str] | None = None) -> tuple[str, list[str]]:
    deduped_refs: list[str] = []
    clean_line = line
    if media_cards_by_ref:
        for ref in sorted(media_cards_by_ref, key=lambda value: len(str(value or "")), reverse=True):
            ref_text = str(ref or "").strip()
            if not ref_text:
                continue
            media_token = f"[[MEDIA:{ref_text}]]"
            if media_token in clean_line:
                clean_line = clean_line.replace(media_token, "")
                if ref_text not in deduped_refs:
                    deduped_refs.append(ref_text)
    for ref in re.findall(r"\[\[MEDIA:(.+?)\]\]", clean_line):
        ref = ref.strip()
        if ref and ref not in deduped_refs:
            deduped_refs.append(ref)
    clean_line = re.sub(r"\[\[MEDIA:.+?\]\]", "", clean_line).strip()
    if media_cards_by_ref:
        for ref in media_cards_by_ref:
            ref_text = str(ref or "").strip()
            if not ref_text:
                continue
            if f"[{ref_text}]" in clean_line and ref_text not in deduped_refs:
                deduped_refs.append(ref_text)
    return clean_line, deduped_refs


def _build_learning_media_block(cards: list[str], *, title: str = "相关公式与图表", extra_class: str = "") -> str:
    title_html = html.escape(title)
    class_attr = "learning-media-group" + (f" {html.escape(extra_class)}" if extra_class else "")
    return f"""
    <section class="{class_attr}">
      <div class="learning-block-header">
        <div class="learning-block-title">{title_html}</div>
        <div class="learning-block-actions">参考材料</div>
      </div>
      {''.join(cards)}
    </section>
    """


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


def write_learning_html(result: dict, output_path: str) -> Path:
    target = resolve_project_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_learning_answer_html(result), encoding="utf-8")
    return target.resolve()


def print_result(result: dict, html_report_path: Path | None = None, learning_html_path: Path | None = None) -> None:
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

    if learning_html_path is not None:
        print("\n=== learning_html ===")
        print(str(learning_html_path))

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
        learning_html_path = None
        if result.get("media_items"):
            output_path = args.html_report or "data/debug_graph_rag/report_latest.html"
            html_report_path = write_html_report(result, output_path)
            if args.learning_html:
                learning_html_path = write_learning_html(result, args.learning_html)
        elif args.learning_html:
            learning_html_path = write_learning_html(result, args.learning_html)
        print_result(result, html_report_path=html_report_path, learning_html_path=learning_html_path)
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
        learning_html_path = None
        if result.get("media_items"):
            output_path = args.html_report or "data/debug_graph_rag/report_latest.html"
            html_report_path = write_html_report(result, output_path)
            if args.learning_html:
                learning_html_path = write_learning_html(result, args.learning_html)
        elif args.learning_html:
            learning_html_path = write_learning_html(result, args.learning_html)
        print_result(result, html_report_path=html_report_path, learning_html_path=learning_html_path)


if __name__ == "__main__":
    main()
