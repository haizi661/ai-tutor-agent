import csv
import ast
import json
from typing import List, Dict, Any

from .config import AI_NODES_CSV


NODE_FIELDS = [
    "node_id",
    "name",
    "chapter",
    "summary",
    "tags",
    "requirement_level",
    "mastery_threshold",
    "importance_level",
    "assessment_focus",
    "explanation_raw",
    "explanation_teacher_style",
    "core_concepts",
    "key_points",
    "formulas",
    "examples",
    "figures_refs",
    "page_refs",
    "definition_candidates",
    "key_point_candidates",
    "formula_candidates",
    "example_candidates",
    "prerequisite_nodes",
    "next_nodes",
    "related_nodes",
    "application_nodes",
    "recommended_next_nodes",
    "keep",
    "source_type",
    "extra",
]

LIST_FIELDS = [
    "tags",
    "core_concepts",
    "key_points",
    "formulas",
    "examples",
    "figures_refs",
    "page_refs",
    "definition_candidates",
    "key_point_candidates",
    "formula_candidates",
    "example_candidates",
    "prerequisite_nodes",
    "next_nodes",
    "related_nodes",
    "application_nodes",
    "recommended_next_nodes",
]

RELATION_NODE_FIELDS = [
    "prerequisite_nodes",
    "next_nodes",
    "related_nodes",
    "application_nodes",
    "recommended_next_nodes",
]


def parse_to_list(value: Any) -> List[str]:
    if value is None:
        return []

    text = str(value).strip()

    if not text or text in {"无", "None", "none", "null", "[]"}:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            data = ast.literal_eval(text)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            pass

    if "||" in text:
        parts = text.split("||")
    else:
        text = (
            text.replace("，", ",")
            .replace("；", ",")
            .replace(";", ",")
            .replace("、", ",")
        )
        parts = text.split(",")

    return [p.strip().strip('"').strip("'") for p in parts if p.strip()]


def to_py_list_string(items: List[Any]) -> str:
    clean = []
    for item in items:
        item = str(item).strip()
        if item and item not in clean:
            clean.append(item)
    return repr(clean)


def normalize_bool(value: Any) -> str:
    text = str(value).strip()
    if text.lower() in {"true", "1", "yes", "y"}:
        return "True"
    if text.lower() in {"false", "0", "no", "n"}:
        return "False"
    return "True"


def normalize_extra(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return repr({
            "node_category": "unknown",
            "learning_stage": "unknown",
            "path_role": "unknown",
        })

    text = str(value).strip()

    try:
        data = json.loads(text)
        return repr(data)
    except Exception:
        pass

    try:
        data = ast.literal_eval(text)
        if isinstance(data, dict):
            return repr(data)
    except Exception:
        pass

    return repr({"raw_extra": text})


def main():
    with open(AI_NODES_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("ai_nodes.csv 为空")
        return

    name_to_id = {
        row.get("name", "").strip(): row.get("node_id", "").strip()
        for row in rows
        if row.get("name") and row.get("node_id")
    }

    normalized_rows = []

    for row in rows:
        new_row: Dict[str, Any] = {}

        for field in NODE_FIELDS:
            new_row[field] = row.get(field, "")

        for field in LIST_FIELDS:
            raw_items = parse_to_list(new_row.get(field, ""))

            if field in RELATION_NODE_FIELDS:
                converted = []
                for item in raw_items:
                    if item.startswith("AI") and item[2:].isdigit():
                        converted.append(item)
                    elif item in name_to_id:
                        converted.append(name_to_id[item])
                new_row[field] = to_py_list_string(converted)
            else:
                new_row[field] = to_py_list_string(raw_items)

        new_row["chapter"] = new_row.get("chapter", "") or ""
        new_row["keep"] = normalize_bool(new_row.get("keep", "True"))
        new_row["source_type"] = new_row.get("source_type", "") or "ai_seed_llm_generated"
        new_row["extra"] = normalize_extra(new_row.get("extra", ""))

        if not new_row.get("mastery_threshold"):
            new_row["mastery_threshold"] = "0.75"

        normalized_rows.append(new_row)

    backup_path = AI_NODES_CSV.with_suffix(".before_normalize.csv")
    if not backup_path.exists():
        AI_NODES_CSV.replace(backup_path)
    else:
        AI_NODES_CSV.unlink()

    with open(AI_NODES_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=NODE_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_rows)

    print(f"已备份原文件: {backup_path}")
    print(f"已规范化输出: {AI_NODES_CSV}")
    print(f"节点数量: {len(normalized_rows)}")


if __name__ == "__main__":
    main()