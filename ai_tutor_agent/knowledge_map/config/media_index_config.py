from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MediaIndexConfig:
    mineru_cache_root: Path = Path("data/mineru_cache")
    output_dir: Path = Path("data/media_evidence_index")
    raw_candidates_filename: str = "raw_media_candidates.jsonl"
    linked_candidates_filename: str = "linked_media_candidates.jsonl"
    annotated_assets_filename: str = "annotated_media_assets.jsonl"
    min_caption_length: int = 2
    nearby_text_chars: int = 280
    max_formula_chars: int = 400
    max_table_chars: int = 3000
    min_image_bytes: int = 2500
    min_nearby_text_chars: int = 12
    max_candidates_per_dedup_group: int = 1
    include_tables: bool = True
    include_formulas: bool = True
    include_figures: bool = True
    supported_asset_types: tuple[str, ...] = ("figure", "formula", "table")
    discipline_name: str = ""
    discipline_hints: dict[str, list[str]] = field(default_factory=dict)

    @property
    def raw_candidates_path(self) -> Path:
        return self.output_dir / self.raw_candidates_filename
