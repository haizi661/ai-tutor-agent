from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.schema.media_asset_schema import normalize_raw_media_candidate
from ai_tutor_agent.platform_paths import resolve_project_path


class MediaCandidateFilter:
    def __init__(self, config: MediaIndexConfig | None = None) -> None:
        self.config = config or MediaIndexConfig()

    def filter_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        kept: list[dict[str, Any]] = []
        seen_groups: set[str] = set()

        for raw in candidates:
            candidate = normalize_raw_media_candidate(raw)
            if not self._passes_basic_quality(candidate):
                continue

            dedup_group = self._build_dedup_group(candidate)
            if dedup_group in seen_groups:
                continue
            seen_groups.add(dedup_group)

            candidate["extra"]["dedup_group"] = dedup_group
            candidate["extra"]["quality_score"] = self.score_candidate_quality(candidate)
            kept.append(candidate)

        kept.sort(
            key=lambda item: (
                item["asset_type"],
                -float(item.get("extra", {}).get("quality_score", 0.0)),
                item["asset_id"],
            )
        )
        return kept

    def write_jsonl(self, candidates: list[dict[str, Any]], output_path: str | Path) -> Path:
        target = resolve_project_path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for item in candidates:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return target.resolve()

    def score_candidate_quality(self, candidate: dict[str, Any]) -> float:
        score = 0.0
        asset_type = candidate.get("asset_type", "")
        if asset_type == "figure":
            score += 1.0
            if candidate.get("caption_text"):
                score += 2.0
            nearby = str(candidate.get("nearby_text", "") or "")
            score += min(len(nearby) / 80.0, 2.0)
            source_path = str(candidate.get("source_path", "") or "").strip()
            if source_path:
                try:
                    score += min(Path(source_path).stat().st_size / 15000.0, 2.0)
                except OSError:
                    pass
        elif asset_type == "formula":
            score += 1.5
            raw_text = str(candidate.get("raw_text", "") or "")
            if "\\tag" in raw_text:
                score += 1.0
            if any(token in raw_text for token in ["=", "\\frac", "\\sum", "\\omega", "\\sigma", "\\Phi"]):
                score += 1.0
        elif asset_type == "table":
            score += 1.2
            if "<tr>" in str(candidate.get("raw_text", "") or ""):
                score += 1.0
        return round(score, 4)

    def _passes_basic_quality(self, candidate: dict[str, Any]) -> bool:
        asset_type = candidate.get("asset_type", "")
        if asset_type == "figure":
            return self._passes_figure_quality(candidate)
        if asset_type == "formula":
            return self._passes_formula_quality(candidate)
        if asset_type == "table":
            return self._passes_table_quality(candidate)
        return False

    def _passes_figure_quality(self, candidate: dict[str, Any]) -> bool:
        source_path = str(candidate.get("source_path", "") or "").strip()
        if not source_path:
            return False

        path = Path(source_path)
        if not path.exists():
            return False

        try:
            if path.stat().st_size < self.config.min_image_bytes:
                return False
        except OSError:
            return False

        caption = str(candidate.get("caption_text", "") or "").strip()
        nearby = str(candidate.get("nearby_text", "") or "").strip()
        return len(caption) >= self.config.min_caption_length or len(nearby) >= self.config.min_nearby_text_chars

    def _passes_formula_quality(self, candidate: dict[str, Any]) -> bool:
        raw_text = str(candidate.get("raw_text", "") or "").strip()
        if not raw_text or len(raw_text) < 6:
            return False
        if len(re.findall(r"[\u4e00-\u9fff]", raw_text)) > 20 and "\\tag" not in raw_text:
            return False
        return any(token in raw_text for token in ["=", "\\frac", "\\sum", "\\omega", "\\sigma", "\\Phi"])

    def _passes_table_quality(self, candidate: dict[str, Any]) -> bool:
        raw_text = str(candidate.get("raw_text", "") or "").strip()
        return raw_text.startswith("<table>") and "</table>" in raw_text and "<tr>" in raw_text

    def _build_dedup_group(self, candidate: dict[str, Any]) -> str:
        asset_type = candidate.get("asset_type", "")
        if asset_type == "figure":
            caption = self._normalize_text(candidate.get("caption_text", ""))
            if caption:
                return f"figure:{caption}"
            return f"figure:path:{candidate.get('source_path', '')}"
        if asset_type == "formula":
            return f"formula:{self._normalize_formula(candidate.get('raw_text', ''))}"
        if asset_type == "table":
            return f"table:{self._normalize_text(candidate.get('raw_text', ''))[:240]}"
        return f"other:{candidate.get('asset_id', '')}"

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip()).lower()

    def _normalize_formula(self, text: str) -> str:
        compact = self._normalize_text(text)
        compact = compact.replace("\\left", "").replace("\\right", "")
        compact = compact.replace("{", "").replace("}", "")
        return compact[:300]
