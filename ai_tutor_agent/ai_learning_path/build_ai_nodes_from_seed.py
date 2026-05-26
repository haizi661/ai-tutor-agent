import os
import csv
import json
import time
import argparse
from typing import Dict, List, Any

import requests

from .config import (
    AI_CONCEPTS_20,
    AI_CONCEPTS_200,
    AI_NODES_CSV,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL,
)

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


def read_concepts(path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"找不到知识点文件: {path}")

    concepts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and name not in concepts:
                concepts.append(name)
    return concepts


def load_existing_nodes(path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    return {row["name"]: row for row in rows if row.get("name")}


def append_node(path, node: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()

    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=NODE_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(node)


def load_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    if not api_key:
        raise RuntimeError("未设置环境变量 DEEPSEEK_API_KEY，也没有在项目根目录找到 .env")

    return api_key


def call_deepseek(prompt: str, max_retries: int = 3) -> Dict[str, Any]:
    api_key = load_api_key()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是人工智能课程知识图谱构建助手。你必须只输出合法 JSON，不要输出 Markdown，不要解释。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.45,
        "stream": False,
    }

    last_error = None

    for i in range(max_retries):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=90,
            )
            resp.raise_for_status()

            text = resp.json()["choices"][0]["message"]["content"].strip()

            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)

        except Exception as e:
            last_error = e
            print(f"调用 DeepSeek 失败，正在重试 {i + 1}/{max_retries}: {e}")
            time.sleep(2)

    raise RuntimeError(f"DeepSeek 调用失败: {last_error}")


def build_node_prompt(node_id: str, name: str, all_concepts: List[str]) -> str:
    concept_text = "、".join(all_concepts[:260])

    return f"""
请为人工智能学习路径知识图谱中的知识点“{name}”生成一个高质量节点。

该图谱用于“根据学生状态和知识图谱自动规划定制化学习路径”，结构要参考自动控制原理知识图谱，但本次人工智能方向不按固定章节组织，因此 chapter 留空。

当前图谱候选知识点包括：
{concept_text}

只输出 JSON，不要 Markdown，不要解释。

必须输出以下字段，字段名不能改，字段不能缺：

{{
  "node_id": "{node_id}",
  "name": "{name}",
  "chapter": "",
  "summary": "",
  "tags": "",
  "requirement_level": "",
  "mastery_threshold": 0.75,
  "importance_level": "",
  "assessment_focus": "",
  "explanation_raw": "",
  "explanation_teacher_style": "",
  "core_concepts": "",
  "key_points": "",
  "formulas": "",
  "examples": "",
  "figures_refs": "",
  "page_refs": "",
  "definition_candidates": "",
  "key_point_candidates": "",
  "formula_candidates": "",
  "example_candidates": "",
  "prerequisite_nodes": "",
  "next_nodes": "",
  "related_nodes": "",
  "application_nodes": "",
  "recommended_next_nodes": "",
  "keep": true,
  "source_type": "ai_seed_llm_generated",
  "extra": ""
}}

填写要求：

1. chapter：固定为空字符串。
2. summary：200 到 300 字，解释该知识点是什么、解决什么问题、在 AI 学习路径中的位置。
3. tags：3 到 8 个标签，用中文逗号分隔。
4. requirement_level：从 basic、intermediate、advanced 中选一个。
5. mastery_threshold：0.50 到 0.90 之间，越重要越高。
6. importance_level：从 low、medium、high、core 中选一个。
7. assessment_focus：写这个节点适合考察什么，比如概念理解、公式推导、算法流程、应用分析、代码实现、实验判断等。
8. explanation_raw：300 到 600 字，偏正式解释，说明定义、作用、典型方法和应用场景。
9. explanation_teacher_style：200 到 350 字，像老师讲课一样说明为什么要学、学之前要懂什么、学完后能接什么内容。
10. core_concepts：写 4 到 8 个核心概念，用中文分号分隔。
11. key_points：写 5 到 8 个学习要点，用中文分号分隔。
12. formulas：有公式就写 1 到 10 个公式或公式名称；没有公式写“无”。
13. examples：写 2 到 4 个具体例子，尽量贴近机器学习、强化学习、自动驾驶、机器人、智能制造、数据分析。
14. figures_refs：固定为空字符串。
15. page_refs：固定为空字符串。
16. definition_candidates：写 3 到 8 条可用于生成定义讲解的候选支撑句，用“ || ”分隔。
17. key_point_candidates：写 3 到 8 条可用于提炼重点的候选支撑句，用“ || ”分隔。
18. formula_candidates：写 0 到 5 条公式或公式解释候选；如果没有，写“无”。
19. example_candidates：写 2 到 4 条例子候选，用“ || ”分隔。
20. prerequisite_nodes：从当前候选知识点中选 0 到 10 个最可能的前置知识点名称，用中文逗号分隔；如果没有写空字符串。
21. next_nodes：从当前候选知识点中选 0 到 10 个后续知识点名称，用中文逗号分隔。
22. related_nodes：从当前候选知识点中选 0 到 20 个相关知识点名称，用中文逗号分隔。
23. application_nodes：从当前候选知识点中选 0 到 10 个应用类知识点名称，用中文逗号分隔。
24. recommended_next_nodes：从当前候选知识点中选 1 到 5 个推荐下一步学习节点名称，用中文逗号分隔。
25. keep：true。
26. source_type：固定为 ai_seed_llm_generated。
27. extra：输出 JSON 字符串，内容包含 node_category、learning_stage、path_role，例如：
{{"node_category":"machine_learning","learning_stage":"basic","path_role":"prerequisite"}}

注意：
- 每个节点内容必须针对“{name}”具体展开，不能套模板。
- 不要把所有节点都写成一样。
- 不要输出不在字段里的内容。
"""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("\n", " ").strip()


def normalize_node(raw: Dict[str, Any], node_id: str, name: str) -> Dict[str, Any]:
    node = {}

    for field in NODE_FIELDS:
        node[field] = normalize_text(raw.get(field, ""))

    node["node_id"] = node_id
    node["name"] = name
    node["chapter"] = ""
    node["figures_refs"] = normalize_text(raw.get("figures_refs", ""))
    node["page_refs"] = normalize_text(raw.get("page_refs", ""))
    node["keep"] = "true"
    node["source_type"] = "ai_seed_llm_generated"

    if not node["mastery_threshold"]:
        node["mastery_threshold"] = "0.75"

    if not node["extra"]:
        node["extra"] = json.dumps(
            {
                "node_category": "unknown",
                "learning_stage": "unknown",
                "path_role": "unknown",
            },
            ensure_ascii=False,
        )

    return node


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["20", "200"], default="20")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    input_path = AI_CONCEPTS_20 if args.size == "20" else AI_CONCEPTS_200

    if args.overwrite and AI_NODES_CSV.exists():
        AI_NODES_CSV.unlink()
        print(f"已删除旧文件: {AI_NODES_CSV}")

    concepts = read_concepts(input_path)
    existing_nodes = load_existing_nodes(AI_NODES_CSV)

    print(f"读取知识点数量: {len(concepts)}")
    print(f"已有节点数量: {len(existing_nodes)}")
    print(f"输入文件: {input_path}")
    print(f"输出文件: {AI_NODES_CSV}")

    for idx, name in enumerate(concepts, start=1):
        node_id = f"AI{idx:03d}"

        if name in existing_nodes:
            print(f"[跳过] 已存在节点: {node_id} {name}")
            continue

        print(f"[{idx}/{len(concepts)}] 生成节点: {node_id} {name}")

        prompt = build_node_prompt(node_id, name, concepts)
        raw = call_deepseek(prompt)
        node = normalize_node(raw, node_id, name)

        append_node(AI_NODES_CSV, node)

        print(f"已写入 CSV: {node_id} {name}")
        time.sleep(0.4)

    print("=" * 80)
    print("节点生成完成")
    print(f"输出文件: {AI_NODES_CSV}")
    print("=" * 80)


if __name__ == "__main__":
    main()