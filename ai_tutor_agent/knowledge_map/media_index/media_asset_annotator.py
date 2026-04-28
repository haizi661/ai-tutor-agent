from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.schema.media_asset_schema import normalize_annotated_media_asset


LATEX_VARIABLE_STOPWORDS = {
    "\\left",
    "\\right",
    "\\begin",
    "\\end",
    "\\mathrm",
    "\\mathbf",
    "\\boldsymbol",
    "\\bar",
    "\\hat",
    "\\tilde",
    "\\tag",
    "\\quad",
    "\\qquad",
    "\\cdots",
    "\\dots",
    "\\displaystyle",
    "\\scriptstyle",
    "\\textstyle",
    "\\array",
    "\\bmatrix",
    "\\pmatrix",
    "\\matrix",
    "\\to",
    "\\rightarrow",
    "\\longrightarrow",
    "\\infty",
    "\\limits",
}

LATEX_VARIABLE_ALLOWLIST = {
    "\\sigma",
    "\\zeta",
    "\\omega",
    "\\phi",
    "\\Phi",
    "\\lambda",
    "\\theta",
    "\\tau",
    "\\mu",
    "\\nu",
    "\\rho",
    "\\eta",
    "\\alpha",
    "\\beta",
    "\\gamma",
    "\\delta",
    "\\psi",
    "\\xi",
    "\\dot",
    "\\frac",
    "\\sum",
    "\\prod",
    "\\int",
    "\\angle",
    "\\sin",
    "\\cos",
    "\\tan",
    "\\lg",
    "\\sqrt",
    "\\approx",
    "\\partial",
}


class MediaAssetAnnotator:
    def __init__(
        self,
        *,
        config: MediaIndexConfig | None = None,
        visual_analyzer: Any | None = None,
    ) -> None:
        self.config = config or MediaIndexConfig()
        self.visual_analyzer = visual_analyzer
        self._visual_cache: dict[str, str] = {}

    def annotate_assets(
        self,
        assets: list[dict[str, Any]],
        *,
        enable_visual: bool = False,
    ) -> list[dict[str, Any]]:
        annotated: list[dict[str, Any]] = []
        for raw in assets:
            asset = normalize_annotated_media_asset(raw)
            self._annotate_single(asset, enable_visual=enable_visual)
            annotated.append(asset)
        return annotated

    def write_jsonl(self, assets: list[dict[str, Any]], output_path: str | Path | None = None) -> Path:
        target = Path(output_path) if output_path is not None else self.config.output_dir / self.config.annotated_assets_filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for item in assets:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return target.resolve()

    def _annotate_single(self, asset: dict[str, Any], *, enable_visual: bool) -> None:
        title_text = self._infer_title_text(asset)
        base_text = self._build_text_blob(asset, title_text=title_text)
        variables = self._extract_variables(base_text)
        domain_terms = self._extract_domain_terms(asset, base_text)
        direct_claims = self._extract_direct_claims(base_text)

        visual_type = self._infer_visual_type(asset, base_text)
        evidence_role = self._infer_evidence_role(asset, base_text, visual_type)
        affordances = self._infer_question_affordances(asset, visual_type, direct_claims, variables)
        formula_meaning = self._infer_formula_meaning(asset, base_text, variables)
        relation_statement = self._infer_relation_statement(asset, direct_claims, formula_meaning)
        retrieval_keywords = self._build_retrieval_keywords(asset, title_text, domain_terms, variables, direct_claims)
        layout_features = self._infer_layout_features(asset, title_text, base_text)

        asset["title_text"] = title_text
        asset["visual_type"] = visual_type
        asset["layout_features"] = layout_features
        asset["evidence_role"] = evidence_role
        asset["question_affordances"] = affordances
        asset["domain_terms"] = domain_terms
        asset["variables"] = variables
        asset["direct_readable_claims"] = direct_claims
        asset["relation_statement"] = relation_statement
        asset["formula_meaning"] = formula_meaning
        asset["retrieval_keywords"] = retrieval_keywords
        asset["dedup_group"] = str((asset.get("extra", {}) or {}).get("dedup_group", "") or "")

        if enable_visual:
            visual_summary = self._describe_figure(asset)
            if visual_summary:
                asset["extra"]["visual_summary"] = visual_summary
                if "visual_summary" not in asset["llm_generated_fields"]:
                    asset["llm_generated_fields"].append("visual_summary")
                if visual_summary not in asset["direct_readable_claims"]:
                    asset["direct_readable_claims"].append(visual_summary)
                if not asset["relation_statement"]:
                    asset["relation_statement"] = visual_summary

        confidence = self._estimate_confidence(asset)
        asset["confidence"] = confidence
        asset["needs_review"] = confidence < 0.45 or (asset["asset_type"] == "figure" and not title_text)

    def _infer_title_text(self, asset: dict[str, Any]) -> str:
        if asset.get("asset_type") == "figure":
            return str(asset.get("caption_text", "") or "").strip()
        if asset.get("asset_type") == "table":
            text = str(asset.get("nearby_text", "") or "").strip()
            return text[:80]

        raw_text = str(asset.get("raw_text", "") or "").strip()
        nearby_text = str(asset.get("nearby_text", "") or "").strip()
        tag_match = re.search(r"\\tag\s*\{([^}]{1,20})\}", raw_text)
        if tag_match:
            return f"式 {tag_match.group(1).strip()}"
        if nearby_text:
            sentence = re.split(r"[。；\n]", nearby_text)[0].strip()
            if sentence:
                return sentence[:80]
        return raw_text[:80]

    def _build_text_blob(self, asset: dict[str, Any], *, title_text: str) -> str:
        return " ".join(
            [
                title_text,
                str(asset.get("caption_text", "") or ""),
                str(asset.get("nearby_text", "") or ""),
                str(asset.get("raw_text", "") or ""),
                str(asset.get("anchor_node_name", "") or ""),
                " ".join(str(x) for x in (asset.get("linked_node_names", []) or [])),
            ]
        ).strip()

    def _infer_visual_type(self, asset: dict[str, Any], text: str) -> str:
        asset_type = str(asset.get("asset_type", "") or "")
        if asset_type == "formula":
            return "equation"
        if asset_type == "table":
            return "data_table"

        title = str(asset.get("caption_text", "") or "")
        if any(keyword in title for keyword in ["响应曲线", "关系曲线", "波形图", "特性曲线"]):
            return "trend_curve"
        if any(keyword in title for keyword in ["结构图", "原理图", "框图", "方框图", "状态变量图"]):
            return "structure_diagram"
        if any(keyword in text for keyword in ["横坐标", "纵坐标", "曲线", "随", "关系"]):
            return "trend_curve"
        return "general_figure"

    def _infer_layout_features(self, asset: dict[str, Any], title_text: str, text: str) -> list[str]:
        features: list[str] = []
        if asset.get("asset_type") == "formula":
            if "\\frac" in text:
                features.append("fraction")
            if "=" in text:
                features.append("equation")
            if "\\tag" in text:
                features.append("equation_tag")
            return features

        if any(keyword in text for keyword in ["横坐标", "纵坐标", "关系曲线", "响应曲线"]):
            features.append("axes_or_curve")
        if any(token in text for token in ["ζ", "\\zeta", "σ", "\\sigma", "ω", "\\omega"]):
            features.append("parameter_symbols")
        if any(keyword in title_text for keyword in ["结构图", "原理图", "框图", "方框图", "状态变量图"]):
            features.append("block_or_structure")
        return features

    def _infer_evidence_role(self, asset: dict[str, Any], text: str, visual_type: str) -> str:
        if asset.get("asset_type") == "formula":
            if any(token in text for token in ["仅是", "无关", "关系", "函数", "取决于", "满足"]):
                return "quantitative_relation"
            return "formula_definition"
        if visual_type == "trend_curve":
            return "trend_evidence"
        if visual_type == "structure_diagram":
            return "structure_evidence"
        if asset.get("asset_type") == "table":
            return "data_evidence"
        return "supporting_evidence"

    def _infer_question_affordances(
        self,
        asset: dict[str, Any],
        visual_type: str,
        direct_claims: list[str],
        variables: list[str],
    ) -> list[str]:
        affordances: list[str] = []
        if visual_type == "trend_curve":
            affordances.extend(["explain_trend", "compare_parameters"])
        if asset.get("asset_type") == "formula":
            affordances.extend(["derive_relation", "interpret_variables"])
        if visual_type == "structure_diagram":
            affordances.extend(["identify_structure", "explain_signal_flow"])
        if direct_claims:
            affordances.append("cite_readable_claim")
        if len(variables) >= 2:
            affordances.append("connect_variables")
        return self._dedup_list(affordances)

    def _infer_formula_meaning(self, asset: dict[str, Any], text: str, variables: list[str]) -> str:
        if asset.get("asset_type") != "formula":
            return ""
        if any(token in text for token in ["\\sigma", "σ", "超调量"]) and any(token in text for token in ["\\zeta", "ζ", "阻尼比"]):
            return "给出超调量与阻尼比之间的定量关系。"
        if any(token in text for token in ["t _ {s}", "t_s", "调节时间"]) and any(token in text for token in ["\\zeta", "ζ", "\\omega", "自然频率"]):
            return "给出调节时间与阻尼比、自然频率之间的近似关系。"
        if any(token in text for token in ["z变换", "Z变换", "\\Phi", "脉冲传递函数"]):
            return "给出离散系统变换域中的定量表达关系。"
        if any(token in text for token in ["哈密顿", "最优", "\\lambda", "性能指标"]):
            return "给出最优控制问题中的性能指标或协态变量关系。"
        if variables:
            return f"给出变量 {'、'.join(variables[:4])} 之间的定量关系。"
        return "给出相关物理量之间的定量关系。"

    def _infer_relation_statement(
        self,
        asset: dict[str, Any],
        direct_claims: list[str],
        formula_meaning: str,
    ) -> str:
        if direct_claims:
            return direct_claims[0]
        if formula_meaning:
            return formula_meaning
        if asset.get("asset_type") == "figure" and asset.get("title_text"):
            return f"该图主要用于说明“{asset['title_text']}”相关关系。"
        return ""

    def _build_retrieval_keywords(
        self,
        asset: dict[str, Any],
        title_text: str,
        domain_terms: list[str],
        variables: list[str],
        direct_claims: list[str],
    ) -> list[str]:
        keywords: list[str] = []
        for source in [
            title_text,
            str(asset.get("anchor_node_name", "") or ""),
            " ".join(str(x) for x in (asset.get("linked_node_names", []) or [])),
        ]:
            keywords.extend(self._extract_keywords_from_text(source, max_count=8))
        keywords.extend(domain_terms[:10])
        keywords.extend(variables[:8])
        for claim in direct_claims[:2]:
            keywords.extend(self._extract_keywords_from_text(claim, max_count=6))
        return self._dedup_list([item for item in keywords if len(item.strip()) >= 1])[:20]

    def _extract_domain_terms(self, asset: dict[str, Any], text: str) -> list[str]:
        terms: list[str] = []
        for candidate in re.findall(r"[\u4e00-\u9fff]{2,12}", text):
            if candidate in {"图表", "公式", "可见", "一般", "所示", "关系", "系统", "函数", "曲线"}:
                continue
            terms.append(candidate)
        anchor = str(asset.get("anchor_node_name", "") or "").strip()
        if anchor:
            terms.append(anchor)
        return self._dedup_list(terms)[:16]

    def _extract_variables(self, text: str) -> list[str]:
        patterns = [
            r"\\[a-zA-Z]+(?:_\s*\{[^}]+\})?",
            r"[ζσωξηλφθτμνρβαγδψ]",
            r"[A-Za-z]+_\s*\{[^}]+\}",
            r"\b[A-Za-z](?:_[A-Za-z0-9]+)?\b",
        ]
        variables: list[str] = []
        for pattern in patterns:
            for match in re.findall(pattern, text):
                cleaned = re.sub(r"\s+", "", str(match))
                cleaned = self._normalize_variable(cleaned)
                if not cleaned or cleaned in variables:
                    continue
                variables.append(cleaned)

        keep: list[str] = []
        for item in variables:
            if item in {"e", "t", "s", "k"} and len(variables) > 6:
                continue
            keep.append(item)
        return keep[:12]

    def _normalize_variable(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""
        if cleaned in LATEX_VARIABLE_STOPWORDS:
            return ""
        if cleaned.startswith("\\") and cleaned not in LATEX_VARIABLE_ALLOWLIST and not re.match(r"\\[A-Za-z]+_\{[^}]+\}$", cleaned):
            return ""
        if re.fullmatch(r"[A-Za-z]", cleaned) and cleaned.lower() in {"d", "j", "i"}:
            return ""
        return cleaned

    def _extract_direct_claims(self, text: str) -> list[str]:
        claims: list[str] = []
        sentences = re.split(r"[。；!！?\n]", text)
        for sentence in sentences:
            cleaned = re.sub(r"\s+", " ", sentence).strip()
            if len(cleaned) < 6:
                continue
            if any(
                marker in cleaned
                for marker in [
                    "越大",
                    "越小",
                    "无关",
                    "有关",
                    "仅是",
                    "反之亦然",
                    "介于",
                    "增加",
                    "减小",
                    "增大",
                    "下降",
                    "上升",
                    "趋于",
                    "接近",
                    "满足",
                    "取决于",
                ]
            ):
                claims.append(cleaned)
        return self._dedup_list(claims)[:4]

    def _describe_figure(self, asset: dict[str, Any]) -> str:
        if asset.get("asset_type") != "figure" or self.visual_analyzer is None:
            return ""
        path = str(asset.get("source_path", "") or "").strip()
        if not path:
            return ""
        cache_key = str(Path(path).resolve())
        if cache_key in self._visual_cache:
            return self._visual_cache[cache_key]
        summary = self.visual_analyzer.describe_image(
            path,
            node_name=str(asset.get("anchor_node_name", "") or asset.get("anchor_node_id", "")),
            caption=str(asset.get("caption_text", "") or ""),
            question="请提取图中可直接支持教学解释的视觉信息。",
        )
        summary = str(summary or "").strip()
        if summary:
            self._visual_cache[cache_key] = summary
        return summary

    def _estimate_confidence(self, asset: dict[str, Any]) -> float:
        score = 0.2
        if asset.get("title_text"):
            score += 0.15
        if asset.get("anchor_node_id"):
            score += 0.2
        if asset.get("direct_readable_claims"):
            score += 0.2
        if asset.get("variables"):
            score += 0.1
        if asset.get("retrieval_keywords"):
            score += 0.1
        if asset.get("asset_type") == "formula" and asset.get("formula_meaning"):
            score += 0.15
        if asset.get("extra", {}).get("visual_summary"):
            score += 0.1
        return min(round(score, 4), 1.0)

    def _extract_keywords_from_text(self, text: str, *, max_count: int) -> list[str]:
        items = re.findall(r"[\u4e00-\u9fff]{2,12}|\\[a-zA-Z]+|[ζσωξηλφθτμνρβαγδψ]|[A-Za-z]{2,12}", str(text or ""))
        filtered: list[str] = []
        for item in items:
            if item.startswith("\\") and item in LATEX_VARIABLE_STOPWORDS:
                continue
            filtered.append(item)
        return self._dedup_list(filtered)[:max_count]

    def _dedup_list(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = str(value or "").strip()
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            result.append(cleaned)
        return result
