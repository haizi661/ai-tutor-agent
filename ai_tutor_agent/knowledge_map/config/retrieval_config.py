from __future__ import annotations

from pathlib import Path


VECTOR_DB_DIR = Path("data/knowledge_map_vector_db")
COLLECTION_NAME = "knowledge_map_text_candidates"


CANDIDATE_FIELD_WEIGHTS = {
    "definition_candidates": 1.0,
    "key_point_candidates": 0.9,
    "formula_candidates": 0.8,
    "example_candidates": 0.7,
}