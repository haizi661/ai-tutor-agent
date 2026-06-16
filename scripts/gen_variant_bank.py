#!/usr/bin/env python3
"""用 LLM 为所有节点生成 5 道变式题。变式题针对原错题的概念点，换个问法或场景。"""
import json, sys, time, re
from pathlib import Path
from collections import Counter
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import httpx

BANK_FILE = Path(__file__).resolve().parents[1] / "data/question_bank/a2-control-theory/variant_questions.jsonl"
from ai_tutor_agent.config import get_settings

def generate_variants(llm, node_name, count=5):
    system = SystemMessage(content="你是自动控制原理教学专家。请生成变式训练题，只输出合法JSON。")
    prompt = f"""为节点「{node_name}」生成 {count} 道变式训练题。
变式题的要求：
1. 每题是针对该节点常见错因的变式题（换个条件/问法/场景）
2. A/B/C/D 四选一，选项不超过80字
3. 每题包含 answer_key, explanation, wrong_option_analysis
4. 输出JSON：{{"questions": [{{"stem":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"answer_key":"A","explanation":"...","wrong_option_analysis":{{"A":"...","B":"...","C":"...","D":"..."}}}}]}}"""
    for attempt in range(3):
        try:
            resp = llm.invoke([system, HumanMessage(content=prompt)])
            text = resp.content if hasattr(resp,"content") else str(resp)
            m = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', text)
            if m:
                data = json.loads(m.group(0))
                return data.get("questions", [])
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}"); time.sleep(2)
    return []

def main():
    s = get_settings()
    llm = ChatOpenAI(model=s.model_name, api_key=s.openai_api_key, base_url=s.openai_api_base,
                      temperature=0.7, request_timeout=300,
                      http_client=httpx.Client(trust_env=False, follow_redirects=True))

    # Load node names
    with open("data/knowledge_map_outputs/auto_control_knowledge_map_v2.json") as f:
        nodes = {n["node_id"]: n.get("name", n["node_id"]) for n in json.load(f).get("nodes", [])}

    existing = {}
    if BANK_FILE.exists():
        for line in BANK_FILE.read_text().splitlines():
            line = line.strip()
            if not line: continue
            try: q=json.loads(line); existing[q["question_id"]]=q
            except: pass

    done = set()
    for q in existing.values():
        if Counter(q2["node_id"] for q2 in existing.values()).get(q["node_id"],0) >= 5:
            done.add(q["node_id"])

    for nid in sorted(nodes.keys()):
        if nid in done:
            print(f"{nid}: ⏭ 已有 5 题"); continue
        name = nodes[nid]
        print(f"{nid} ({name}): ", end="", flush=True)
        qs = generate_variants(llm, name, 5)
        if qs:
            for i, q in enumerate(qs[:5], 1):
                q["question_id"] = f"VAR-{nid}-{i:02d}"
                q["node_id"] = nid
                q["source"] = "local_question_bank"
                existing[q["question_id"]] = q
            with open(BANK_FILE, "w") as f:
                for q in existing.values():
                    f.write(json.dumps(q, ensure_ascii=False) + "\n")
            print(f"✅ {len(qs[:5])}题 (总{len(existing)})")
        else:
            print("❌ 0题")
        time.sleep(0.5)
    print(f"\n✅ {len(existing)} 变式题 ({len(set(q['node_id'] for q in existing.values()))} 节点)")

if __name__ == "__main__":
    main()
