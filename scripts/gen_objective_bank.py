#!/usr/bin/env python3
"""用 LLM 按 _build_objective_generation_messages 规范为所有节点生成 10 道客观题。"""
import json, sys, time, re
from collections import Counter
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import httpx

BANK_FILE = Path(__file__).resolve().parents[1] / "data/question_bank/a2-control-theory/objective_questions.jsonl"
V2_JSON = Path(__file__).resolve().parents[1] / "data/knowledge_map_outputs/auto_control_knowledge_map_v2.json"
from ai_tutor_agent.config import get_settings

def load_nodes():
    with open(V2_JSON) as f:
        return {n["node_id"]: n for n in json.load(f).get("nodes", [])}

def build_node_context(node):
    """从节点元数据构建 LLM prompt 所需的 context 字符串。"""
    parts = []
    name = node.get("name", "")
    if name: parts.append(f"节点名称：{name}")
    ch = node.get("chapter", "")
    if ch: parts.append(f"所属章节：{ch}")
    summary = node.get("summary", "")
    if summary: parts.append(f"内容概要：{summary}")
    kp = node.get("key_points", [])
    if kp: parts.append("必会要点：" + "；".join(kp[:5]))
    cc = node.get("core_concepts", [])
    if cc: parts.append("核心概念：" + "；".join(cc[:5]))
    defs = node.get("definition_candidates", [])
    if defs: parts.append("关键定义：" + "；".join(defs[:4]))
    kpc = node.get("key_point_candidates", [])
    if kpc: parts.append("考察要点候选：" + "；".join(kpc[:6]))
    fc = node.get("formula_candidates", [])
    if fc: parts.append("公式候选：" + "；".join(fc[:3]))
    ec = node.get("example_candidates", [])
    if ec: parts.append("实例候选：" + "；".join(ec[:3]))
    return "\n".join(parts)

def generate_for_node(llm, node):
    nid = node["node_id"]
    name = node.get("name", nid)
    ctx = build_node_context(node)

    system = SystemMessage(content=(
        "你是严谨的课程测评出题专家。请只输出合法 JSON，不要 Markdown。"
        "你生成的是节点学习后的客观选择题，不是学前自评题。"
        "题目必须紧扣当前节点字段，检验学习者是否理解本节点的具体概念、条件、因果关系和常见误区。"
    ))

    prompt = f"""请为当前知识图谱节点「{name}」生成 10 道四选一客观题。
当前节点内容：
{ctx or '暂无详细信息'}

要求：
1. 每题必须是 A/B/C/D 四选一，选项控制在 80 字以内。
2. 每题必须包含 answer_key，值只能是 A/B/C/D。
3. 题干必须包含本节点的具体对象、条件、判断或应用场景，不要写成泛化模板。
4. 每题包含 assessment_focus（概念辨析/判断依据/常见误区/应用迁移/因果关系之一）。
5. 每题包含 target_objective（本题检验的具体学习目标）。
6. 每题包含 misconception（本题主要针对的常见误区）。
7. 每题包含 difficulty（1-5）。
8. 每题包含 explanation（为什么正确答案成立）和 wrong_option_analysis（每个选项的解释）。
9. 至少覆盖"必会要点"和"核心概念"。干扰项要对应真实误区。
10. answer_key 均匀分布（A/B/C/D 各 2-3 题）。

输出 JSON Schema：
{{
  "questions": [
    {{
      "question_id": "OBJ-{nid}-01",
      "node_id": "{nid}",
      "stem": "题干",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer_key": "A",
      "assessment_focus": "概念辨析",
      "target_objective": "本题检验的学习目标",
      "misconception": "本题针对的常见误区",
      "difficulty": 3,
      "explanation": "正确答案的解析",
      "wrong_option_analysis": {{"A":"...", "B":"...", "C":"...", "D":"..."}}
    }}
  ]
}}"""

    for attempt in range(3):
        try:
            resp = llm.invoke([system, HumanMessage(content=prompt)])
            text = resp.content if hasattr(resp, "content") else str(resp)
            # Extract JSON
            match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', text)
            if match:
                data = json.loads(match.group(0))
                qs = data.get("questions", [])
                if qs:
                    # Normalize QIDs
                    for i, q in enumerate(qs, 1):
                        q["question_id"] = f"OBJ-{nid}-{i:02d}"
                        q["node_id"] = nid
                        q["source"] = "local_question_bank"
                        # Clamp difficulty
                        d = q.get("difficulty", 3)
                        q["difficulty"] = max(1, min(5, int(d) if isinstance(d, (int, float)) else 3))
                    return qs
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return []

def main():
    s = get_settings()
    http_client = httpx.Client(trust_env=False, follow_redirects=True)
    llm = ChatOpenAI(
        model=s.model_name,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=0.7,
        request_timeout=300,
        http_client=http_client,
    )

    nodes = load_nodes()
    all_qs = []
    failed = []

    # Load existing questions to preserve them
    existing = {}
    if BANK_FILE.exists():
        for line in BANK_FILE.read_text().splitlines():
            line = line.strip()
            if not line: continue
            try: q=json.loads(line); existing[q["question_id"]]=q
            except: pass

    nodes_to_do = sorted(nodes.keys())
    done = set()
    for nid, cnt in Counter(q["node_id"] for q in existing.values()).items():
        if cnt >= 10:
            done.add(nid)

    for nid in nodes_to_do:
        if nid in done:
            print(f"{nid}: ⏭ 已有 10 题")
            continue
        node = nodes[nid]
        name = node.get("name", nid)
        print(f"{nid} ({name}): ", end="", flush=True)
        qs = generate_for_node(llm, node)
        if len(qs) >= 8:
            for q in qs[:10]:
                existing[q["question_id"]] = q
            # Write immediately after each node
            with open(BANK_FILE, "w") as f:
                for q in existing.values():
                    f.write(json.dumps(q, ensure_ascii=False) + "\n")
            print(f"✅ {len(qs[:10])}题 (总{len(existing)}题)")
        else:
            print(f"❌ {len(qs)}题")
            failed.append(nid)
        time.sleep(0.5)

    print(f"\n✅ 完成：{len(existing)} 题 ({len(set(q['node_id'] for q in existing.values()))} 节点)")
    if failed:
        print(f"❌ 失败: {failed}")

if __name__ == "__main__":
    main()
