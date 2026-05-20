import os
import csv
import json
import time
import argparse
from typing import Dict, List, Any, Tuple

import requests

from .config import (
    AI_NODES_CSV,
    AI_EDGES_CSV,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL,
)

EDGE_FIELDS = [
    "edge_id",
    "source",
    "target",
    "relation",
    "relation_type",
    "relation_label",
    "relation_strength",
    "direction_type",
    "keep",
    "weight",
    "source_type",
    "evidence",
    "relation_note",
    "extra",
]


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


def read_nodes(path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到节点文件: {path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    return rows


def load_existing_edges(path) -> Tuple[List[Dict[str, Any]], set]:
    if not path.exists():
        return [], set()

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    seen = set()
    for row in rows:
        seen.add((row.get("source"), row.get("target"), row.get("relation")))

    return rows, seen


def write_all_edges(path, edges: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EDGE_FIELDS)
        writer.writeheader()
        writer.writerows(edges)


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
                "content": "你是人工智能课程知识图谱关系构建助手。你必须只输出合法 JSON，不要输出 Markdown，不要解释。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.35,
        "stream": False,
    }

    last_error = None

    for i in range(max_retries):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=100,
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


def node_brief(n: Dict[str, Any]) -> str:
    return (
        f'{n.get("node_id", "")}: {n.get("name", "")} | '
        f'summary={n.get("summary", "")[:120]} | '
        f'tags={n.get("tags", "")} | '
        f'prerequisite_nodes={n.get("prerequisite_nodes", "")} | '
        f'next_nodes={n.get("next_nodes", "")} | '
        f'related_nodes={n.get("related_nodes", "")}'
    )


def chunk_nodes(nodes: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
    return [nodes[i:i + batch_size] for i in range(0, len(nodes), batch_size)]


def build_edges_prompt(batch_nodes: List[Dict[str, Any]], all_nodes: List[Dict[str, Any]]) -> str:
    batch_text = "\n".join(node_brief(n) for n in batch_nodes)

    all_text = "\n".join(
        f'{n.get("node_id", "")}: {n.get("name", "")}'
        for n in all_nodes
    )

    return f"""
请为人工智能学习路径知识图谱生成边关系。

目标：
这些边用于根据学生目标知识点反向寻找前置知识，并生成定制化学习路径。因此 prerequisite_of 是最重要的关系。

本批次重点节点如下：
{batch_text}

全图可选节点如下：
{all_text}

只输出 JSON，不要 Markdown，不要解释。

关系类型只能使用：
1. prerequisite_of：前置关系，source 是 target 的前置知识，必须 directed。
2. related_to：相关关系，可 directed 或 undirected。
3. parallel_to：并列关系，通常 undirected。
4. weak_related_to：弱相关关系。

输出格式必须是：

{{
  "edges": [
    {{
      "source": "AI001",
      "target": "AI002",
      "relation": "prerequisite_of",
      "relation_type": "prerequisite_of",
      "relation_label": "前置知识",
      "relation_strength": 0.85,
      "direction_type": "directed",
      "keep": true,
      "weight": 0.85,
      "source_type": "ai_edge_llm_generated",
      "evidence": "",
      "relation_note": "",
      "extra": ""
    }}
  ]
}}

字段要求：
1. source 和 target 必须来自全图可选节点，不能编造 ID。
2. 不要自环。
3. 不要重复边。
4. 每个本批次节点尽量生成 2 到 5 条边。
5. prerequisite_of 的 evidence 不要写固定模板，要具体说明为什么 source 是 target 的前置知识。
6. relation_note 要具体说明这条边在学习路径规划中的作用。
7. extra 输出 JSON 字符串，包含 relation_reason、path_planning_role、confidence，例如：
{{"relation_reason":"xxx","path_planning_role":"xxx","confidence":"high"}}
8. relation_strength 和 weight 使用 0.1 到 1.0 的数值。
9. 如果 source 是 target 的必要基础，relation_strength 建议大于 0.8。
10. 如果只是相关，relation_strength 建议 0.4 到 0.7。

注意：
- evidence 必须根据具体节点写，不要统一写“根据人工智能课程知识依赖关系生成”。
- relation_note 不要统一写“学习 target 前建议先掌握 source”。
- 重点生成能支持学习路径排序的边。
"""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("\n", " ").strip()


def normalize_float(value: Any, default: float = 0.7) -> str:
    try:
        v = float(value)
        if v < 0:
            v = default
        if v > 1:
            v = 1.0
        return f"{v:.2f}"
    except Exception:
        return f"{default:.2f}"


def normalize_edges(
    raw: Dict[str, Any],
    valid_ids: set,
    existing_seen: set,
    start_index: int,
) -> List[Dict[str, Any]]:
    raw_edges = raw.get("edges", [])
    edges = []
    seen = set(existing_seen)

    for item in raw_edges:
        source = normalize_text(item.get("source", ""))
        target = normalize_text(item.get("target", ""))
        relation = normalize_text(item.get("relation", ""))

        if not source or not target or not relation:
            continue

        if source == target:
            continue

        if source not in valid_ids or target not in valid_ids:
            continue

        if relation not in {
            "prerequisite_of",
            "related_to",
            "parallel_to",
            "weak_related_to",
        }:
            continue

        key = (source, target, relation)
        if key in seen:
            continue

        seen.add(key)

        relation_strength = normalize_float(item.get("relation_strength", 0.7))
        weight = normalize_float(item.get("weight", relation_strength))

        direction_type = normalize_text(item.get("direction_type", ""))
        if not direction_type:
            direction_type = "directed" if relation == "prerequisite_of" else "undirected"

        if relation == "prerequisite_of":
            relation_label = item.get("relation_label", "前置知识")
        elif relation == "parallel_to":
            relation_label = item.get("relation_label", "并列知识")
        elif relation == "related_to":
            relation_label = item.get("relation_label", "相关知识")
        else:
            relation_label = item.get("relation_label", "弱相关知识")

        edge = {
            "edge_id": f"E{start_index + len(edges):04d}",
            "source": source,
            "target": target,
            "relation": relation,
            "relation_type": normalize_text(item.get("relation_type", relation)),
            "relation_label": normalize_text(relation_label),
            "relation_strength": relation_strength,
            "direction_type": direction_type,
            "keep": "true",
            "weight": weight,
            "source_type": normalize_text(item.get("source_type", "ai_edge_llm_generated")),
            "evidence": normalize_text(item.get("evidence", "")),
            "relation_note": normalize_text(item.get("relation_note", "")),
            "extra": normalize_text(item.get("extra", "")),
        }

        if not edge["evidence"]:
            edge["evidence"] = f"{source} 与 {target} 在学习依赖上存在明确关系。"

        if not edge["relation_note"]:
            edge["relation_note"] = "该关系用于辅助学习路径排序和前置知识回溯。"

        if not edge["extra"]:
            edge["extra"] = json.dumps(
                {
                    "relation_reason": edge["evidence"],
                    "path_planning_role": "learning_path_dependency",
                    "confidence": "medium",
                },
                ensure_ascii=False,
            )

        edges.append(edge)

    return edges


def build_rule_edges(nodes: List[Dict[str, Any]], existing_seen: set, start_index: int) -> List[Dict[str, Any]]:
    """
    用节点中的 prerequisite_nodes、next_nodes、related_nodes 生成一批规则边。
    这一步不依赖大模型，可以补足路径规划最需要的 prerequisite_of。
    """
    name_to_id = {n.get("name", ""): n.get("node_id", "") for n in nodes}
    id_to_name = {n.get("node_id", ""): n.get("name", "") for n in nodes}
    seen = set(existing_seen)
    edges = []

    def split_names(text: str) -> List[str]:
        if not text:
            return []
        text = text.replace("，", ",").replace("；", ",").replace(";", ",")
        return [x.strip() for x in text.split(",") if x.strip()]

    def add_edge(source_id: str, target_id: str, relation: str, reason: str):
        if not source_id or not target_id or source_id == target_id:
            return

        key = (source_id, target_id, relation)
        if key in seen:
            return

        seen.add(key)

        source_name = id_to_name.get(source_id, source_id)
        target_name = id_to_name.get(target_id, target_id)

        if relation == "prerequisite_of":
            label = "前置知识"
            direction = "directed"
            strength = "0.82"
        elif relation == "related_to":
            label = "相关知识"
            direction = "undirected"
            strength = "0.62"
        else:
            label = "弱相关知识"
            direction = "undirected"
            strength = "0.45"

        edges.append(
            {
                "edge_id": f"E{start_index + len(edges):04d}",
                "source": source_id,
                "target": target_id,
                "relation": relation,
                "relation_type": relation,
                "relation_label": label,
                "relation_strength": strength,
                "direction_type": direction,
                "keep": "true",
                "weight": strength,
                "source_type": "ai_node_field_rule_generated",
                "evidence": reason,
                "relation_note": f"在路径规划中，{source_name} 可作为理解 {target_name} 的结构性支撑节点。",
                "extra": json.dumps(
                    {
                        "relation_reason": reason,
                        "path_planning_role": "generated_from_node_candidates",
                        "confidence": "medium",
                    },
                    ensure_ascii=False,
                ),
            }
        )

    for node in nodes:
        current_id = node.get("node_id", "")
        current_name = node.get("name", "")

        for pre_name in split_names(node.get("prerequisite_nodes", ""))[:3]:
            pre_id = name_to_id.get(pre_name)
            if pre_id:
                add_edge(
                    pre_id,
                    current_id,
                    "prerequisite_of",
                    f"节点字段中将“{pre_name}”列为“{current_name}”的前置知识，说明学习当前节点前需要先理解该基础内容。",
                )

        for next_name in split_names(node.get("next_nodes", ""))[:3]:
            next_id = name_to_id.get(next_name)
            if next_id:
                add_edge(
                    current_id,
                    next_id,
                    "prerequisite_of",
                    f"节点字段中将“{next_name}”列为“{current_name}”的后续学习内容，说明当前节点可支撑后续节点学习。",
                )

        for rel_name in split_names(node.get("related_nodes", ""))[:2]:
            rel_id = name_to_id.get(rel_name)
            if rel_id:
                add_edge(
                    current_id,
                    rel_id,
                    "related_to",
                    f"节点字段中将“{rel_name}”列为“{current_name}”的相关知识，二者在概念、方法或应用场景上存在联系。",
                )

    return edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="只根据 nodes 中的 prerequisite_nodes/next_nodes/related_nodes 生成规则边，不调用 DeepSeek",
    )
    args = parser.parse_args()

    nodes = read_nodes(AI_NODES_CSV)
    valid_ids = {n.get("node_id", "") for n in nodes if n.get("node_id")}

    if args.overwrite and AI_EDGES_CSV.exists():
        AI_EDGES_CSV.unlink()
        print(f"已删除旧文件: {AI_EDGES_CSV}")

    existing_edges, existing_seen = load_existing_edges(AI_EDGES_CSV)

    print(f"读取节点数量: {len(nodes)}")
    print(f"已有边数量: {len(existing_edges)}")
    print(f"节点文件: {AI_NODES_CSV}")
    print(f"边输出: {AI_EDGES_CSV}")

    all_edges = list(existing_edges)
    seen = set(existing_seen)

    print("先根据节点字段生成规则边...")
    rule_edges = build_rule_edges(nodes, seen, start_index=len(all_edges) + 1)
    for e in rule_edges:
        seen.add((e["source"], e["target"], e["relation"]))
    all_edges.extend(rule_edges)
    write_all_edges(AI_EDGES_CSV, all_edges)
    print(f"规则边新增数量: {len(rule_edges)}")

    if args.skip_llm:
        print("已跳过 LLM 补边。")
        print(f"最终边数量: {len(all_edges)}")
        return

    batches = chunk_nodes(nodes, args.batch_size)

    for batch_idx, batch_nodes in enumerate(batches, start=1):
        print(f"[批次 {batch_idx}/{len(batches)}] 调用 DeepSeek 生成补充边，批次节点数: {len(batch_nodes)}")

        prompt = build_edges_prompt(batch_nodes, nodes)
        raw = call_deepseek(prompt)

        new_edges = normalize_edges(
            raw=raw,
            valid_ids=valid_ids,
            existing_seen=seen,
            start_index=len(all_edges) + 1,
        )

        for e in new_edges:
            seen.add((e["source"], e["target"], e["relation"]))

        all_edges.extend(new_edges)
        write_all_edges(AI_EDGES_CSV, all_edges)

        print(f"本批新增边: {len(new_edges)}，当前总边数: {len(all_edges)}")
        time.sleep(0.5)

    print("=" * 80)
    print("边关系生成完成")
    print(f"最终边数量: {len(all_edges)}")
    print(f"输出文件: {AI_EDGES_CSV}")
    print("=" * 80)


if __name__ == "__main__":
    main()