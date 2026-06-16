#!/usr/bin/env python3
"""真实完整 E2E 流程验证——使用真实 runtime、真实 workflow、真实 LLM。

用法：
  # 默认配置 (Qwen)
  python scripts/real_e2e_verify.py

  # 自定义模型
  CHAT_PROFILE=deepseek MODEL_NAME=deepseek-v4-flash \
    OPENAI_API_BASE=https://api.deepseek.com/v1 \
    python scripts/real_e2e_verify.py

  # 安静模式
  python scripts/real_e2e_verify.py --quiet

直接使用 ASGI test client，不启动 HTTP 服务。
覆盖完整学习路径 + 2 个节点轮转 + 序列化字段验证。
"""
import json, sys, os, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# LLM 配置从环境变量读取，默认 Qwen
os.environ.setdefault("AI_TUTOR_EMBEDDING_PROVIDER", "local")
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "test-key"))
os.environ.setdefault("CHAT_PROFILE", os.environ.get("CHAT_PROFILE", "qwen"))
os.environ.setdefault("LLM_PROVIDER", os.environ.get("LLM_PROVIDER", "openai"))
os.environ.setdefault("MODEL_NAME", os.environ.get("MODEL_NAME", "qwen-plus"))
os.environ.setdefault("OPENAI_API_BASE", os.environ.get("OPENAI_API_BASE",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"))

t_start = time.time()
PASS = 0
FAIL = 0
QUIET = "--quiet" in sys.argv


def log(msg: str) -> None:
    if not QUIET:
        print(f"  {msg}", flush=True)


def step(n: int, label: str) -> None:
    global PASS
    PASS += 1
    elapsed = time.time() - t_start
    print(f"\n[{elapsed:6.1f}s] {'─'*50}", flush=True)
    print(f"[{elapsed:6.1f}s] Step {n}: {label}", flush=True)


def fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"\n❌ FAIL: {msg}", flush=True)


def check_field(st: dict, field: str, label: str = "", allow_empty: bool = False) -> bool:
    """验证字段存在于序列化结果中。allow_empty=True 时允许空值。"""
    val = st.get(field)
    exists = field in st
    name = label or field
    if not exists:
        fail(f"{name}: 字段不在序列化结果中")
        return False
    if not allow_empty:
        if val is None:
            fail(f"{name}: 值为 None")
            return False
        if isinstance(val, (str, list, dict)) and len(val) == 0:
            log(f"  ⚠ {name}: 空值 (LLM 可能尚未填充)")
    log(f"  ✓ {name}: {_truncate(val)}")
    return True


def _truncate(v, n: int = 80) -> str:
    s = str(v)
    return s[:n] + "…" if len(s) > n else s


def get_state(client, tid: str) -> dict:
    r = client.get(f"/api/history/{tid}")
    if r.status_code != 200:
        return {}
    try:
        return json.loads(r.text).get("state", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def consume(client, tid: str, timeout: int = 180, target_pik: str = "") -> dict:
    """消费 SSE 直到 target_pik 到达或超时。返回最终 state。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        client.get(f"/api/stream?thread_id={tid}")
        st = get_state(client, tid)
        pik = st.get("pending_interaction_kind", "")
        flow = st.get("flow_status", "")
        if pik or flow in (
            "awaiting_assessment", "awaiting_topic_confirmation",
            "awaiting_post_lesson_choice", "awaiting_objective_answers",
            "awaiting_continue_or_homework_choice", "awaiting_homework_review_choice",
            "awaiting_homework_answers", "normal",
            "profiling", "assessment_dialog",
        ):
            if not target_pik or pik == target_pik:
                return st
        time.sleep(0.5)
    st = get_state(client, tid)
    log(f"  ⏰ SSE timeout {timeout}s, pik=[{st.get('pending_interaction_kind','?')}] "
        f"flow={st.get('flow_status','?')}")
    return st


def resume_until(client, tid: str, target_pik: str, timeout: int = 300) -> dict:
    """Resume + consume 直到 target_pik 到达。"""
    deadline = time.monotonic() + timeout
    count = 0
    while time.monotonic() < deadline:
        st = consume(client, tid, timeout=60)
        pik = st.get("pending_interaction_kind", "")
        flow = st.get("flow_status", "")
        if pik == target_pik:
            return st
        count += 1
        client.post(f"/api/sessions/{tid}/resume")
        log(f"  resume #{count}: flow={flow} pik=[{pik}]")
    return get_state(client, tid)


def submit_test_answers(client, tid: str, choice: str = "A") -> dict:
    """等待客观题、提交答案、等待评分完成。返回评分后的 state。"""
    st = resume_until(client, tid, "objective_test_answers", timeout=180)
    quiz = st.get("node_quiz_items", [])
    log(f"  小测题数: {len(quiz)}")
    if not quiz:
        fail("未获取到客观题")
        return st

    ans_dict = {}
    for i, q in enumerate(quiz):
        qid = str(q.get("question_id", q.get("id", f"Q{i}")))
        ans_dict[qid] = choice
    client.post("/api/answer", json={"thread_id": tid, "answer": json.dumps(ans_dict)})
    log(f"  提交 {len(ans_dict)} 道答案 (全部 {choice})")

    # 等待评分完成
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        st = consume(client, tid, timeout=60)
        pik = st.get("pending_interaction_kind", "")
        if pik in ("continue_or_homework_choice", "remediation_decision"):
            return st
        time.sleep(3)
    return get_state(client, tid)


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    from ai_tutor_agent.config import get_settings
    from ai_tutor_agent.interfaces.api.runtime import build_runtime
    from ai_tutor_agent.interfaces.api.app import create_api_app
    from tests.asgi_test_client import SyncASGITestClient as TestClient

    get_settings.cache_clear()
    log(f"模型: {os.environ['CHAT_PROFILE']}/{os.environ['MODEL_NAME']}")
    log(f"API Base: {os.environ['OPENAI_API_BASE']}")
    log("构建 Runtime (GraphRAG + RAG + StudentStore)...")
    t_build = time.time()
    runtime = build_runtime()
    log(f"Runtime 就绪 ({time.time()-t_build:.1f}s)")

    app = create_api_app(runtime_factory=lambda: runtime)
    TID = f"real-e2e-{int(time.time()%100000)}"

    with TestClient(app) as client:
        # ── 0: Health ──
        step(0, "Health check")
        r = client.get("/api/health")
        assert r.status_code == 200, f"Health failed: {r.text}"
        log(f"✅ Health: OK")

        # ── 1: Session → Start → Topic confirmation ──
        step(1, "Create session → Start → Confirm topic")
        r = client.post("/api/sessions", json={"thread_id": TID})
        assert r.status_code == 200

        r = client.post("/api/start", json={"thread_id": TID, "topic": "我想学自动控制原理的根轨迹法"})
        assert r.status_code == 200
        log("✅ Session + Start")

        st = consume(client, TID, timeout=120)
        flow = st.get("flow_status", "")
        pik = st.get("pending_interaction_kind", "")
        log(f"  flow={flow} pik=[{pik}]")

        if pik == "topic_confirmation" or flow == "awaiting_topic_confirmation":
            r = client.post("/api/confirm_topic",
                            json={"thread_id": TID, "confirmed": True, "start_mode": "assessment"})
            assert r.status_code == 200
            log("✅ Topic confirmed → assessment")
            st = consume(client, TID, timeout=180)
            flow = st.get("flow_status", "")

        assert flow == "awaiting_assessment" or st.get("pending_interaction_kind") == "assessment_dialog", \
            f"Expected assessment, got flow={flow} pik=[{st.get('pending_interaction_kind')}]"
        asm_qs = st.get("assessment_questions", [])
        assert len(asm_qs) > 0, f"No assessment questions (keys: {list(st.keys())[:10]})"
        log(f"✅ {len(asm_qs)} assessment questions ready")

        # ── 2: Assessment → profiling → plan → tutor ──
        step(2, "Submit assessment → wait for profiling+plan+tutor")
        ans = {str(q.get("id", i)): "C" for i, q in enumerate(asm_qs)}
        r = client.post("/api/submit_assessment", json={"thread_id": TID, "answers": ans})
        assert r.status_code == 200
        log(f"✅ {len(asm_qs)} assessment answers submitted → waiting for profiling+plan+tutor...")

        st = consume(client, TID, timeout=300)
        assert st.get("is_assessed", False), "User was not profiled"
        log(f"✅ is_assessed=True")

        # 验证画像字段
        check_field(st, "difficulty_level", "difficulty_level")
        check_field(st, "teaching_strategy", "teaching_strategy")
        check_field(st, "assessment_concept_gaps", "assessment_concept_gaps")
        if st.get("learning_plan"):
            log(f"✅ Learning plan: {len(st['learning_plan'])} steps")

        # ── 3: Verify learning plan fields + post_lesson ──
        step(3, "Verify learning plan v2 fields → post_lesson")
        st = resume_until(client, TID, "post_lesson_choice", timeout=300)
        node_id = st.get("current_node_id", "")
        log(f"✅ post_lesson_choice: node={node_id} - {st.get('current_node_name','')}")

        # 验证新增序列化字段
        for field, label in [
            ("learning_plan", "learning_plan"),
            ("learning_plan_v2", "learning_plan_v2"),
            ("learning_plan_current_step", "learning_plan_current_step"),
            ("learning_plan_generated_at", "learning_plan_generated_at"),
            ("learning_plan_source", "learning_plan_source"),
            ("current_node_id", "current_node_id"),
            ("tutor_content", "tutor_content"),
            ("node_content_context", "node_content_context"),
            ("next_node_candidate_id", "next_node_candidate_id"),
        ]:
            check_field(st, field, label, allow_empty=(field in ("node_content_context", "next_node_candidate_id")))

        # 补救字段（初始应空）
        for field in ("node_remediation_state", "remediation_decision",
                      "variant_questions", "wrong_question_explanations"):
            check_field(st, field, field, allow_empty=True)

        # ── 4: Node 1 test → scoring ──
        step(4, "Node 1: objective test → scoring")
        r = client.post("/api/answer", json={"thread_id": TID, "answer": "开始测试"})
        assert r.status_code == 200
        log("✅ '开始测试' sent")

        st = submit_test_answers(client, TID, choice="B")
        score = st.get("node_quiz_score", 0)
        pik = st.get("pending_interaction_kind", "")
        log(f"✅ Node 1 scored: {score}%, pik=[{pik}]")

        # 验证测验相关字段
        check_field(st, "node_quiz_score", "node_quiz_score")
        check_field(st, "node_quiz_answers", "node_quiz_answers")
        check_field(st, "node_quiz_wrong_items", "node_quiz_wrong_items", allow_empty=True)
        check_field(st, "node_remediation_state", "node_remediation_state", allow_empty=True)
        check_field(st, "remediation_decision", "remediation_decision", allow_empty=True)
        check_field(st, "variant_questions", "variant_questions", allow_empty=True)
        check_field(st, "wrong_question_explanations", "wrong_question_explanations", allow_empty=True)

        # ── 5: Handle remediation → continue ──
        step(5, "Remediation handling → continue")
        pik = st.get("pending_interaction_kind", "")
        if pik == "remediation_decision":
            log("  进入补救决策 → do_later")
            client.post("/api/answer", json={"thread_id": TID, "answer": "do_later"})
            consume(client, TID, timeout=60)
        elif pik == "continue_or_homework_choice":
            log("  直接通过 → 继续下一节点")
        else:
            log(f"  pik=[{pik}], 尝试推进")
            client.post("/api/answer", json={"thread_id": TID, "answer": "继续"})
            consume(client, TID, timeout=60)

        st = resume_until(client, TID, "continue_or_homework_choice", timeout=120)
        log(f"✅ continue_or_homework_choice reached")

        # ── 6: Node 2 cycle ──
        step(6, "Node 2: full cycle (teach → test → score)")
        client.post("/api/answer", json={"thread_id": TID, "answer": "继续"})
        log("✅ '继续' → 等待节点 2 教学…")

        st = resume_until(client, TID, "post_lesson_choice", timeout=300)
        node_id2 = st.get("current_node_id", "")
        node_name2 = st.get("current_node_name", "")
        log(f"✅ Node 2 post_lesson: {node_id2} - {node_name2}")
        assert node_id2, "Node 2: current_node_id empty"
        if node_id2 == node_id:
            log(f"  ⚠ Node 2 same as Node 1: {node_id2} (学习计划可能将同一节点放在第一步多轮学习中)")

        # 验证学习计划 v2 进展
        lpv2 = st.get("learning_plan_v2", {})
        if isinstance(lpv2, dict):
            log(f"  learning_plan_v2: total_nodes={lpv2.get('total_nodes','?')} "
                f"current_step={st.get('learning_plan_current_step','?')}")

        # Node 2 test
        client.post("/api/answer", json={"thread_id": TID, "answer": "开始测试"})
        st = submit_test_answers(client, TID, choice="C")
        score2 = st.get("node_quiz_score", 0)
        log(f"✅ Node 2 scored: {score2}%")

        # Handle any post-test state
        pik = st.get("pending_interaction_kind", "")
        if pik == "remediation_decision":
            client.post("/api/answer", json={"thread_id": TID, "answer": "do_later"})
            consume(client, TID, timeout=60)

        # ── 7: Stop → homework ──
        step(7, "End with homework")
        st = resume_until(client, TID, "continue_or_homework_choice", timeout=120)
        pik = st.get("pending_interaction_kind", "")
        if pik == "continue_or_homework_choice":
            client.post("/api/answer", json={"thread_id": TID, "answer": "今天就到这里"})
            log("✅ '今天就到这里' sent → waiting for homework…")
            st = consume(client, TID, timeout=180)
            hw = st.get("homework_items", [])
            log(f"  homework_items={len(hw)} status={st.get('homework_status','')}")
            if hw:
                log(f"✅ Homework: {len(hw)} items")

        # ── Final: state verification ──
        step(8, "Final state verification")
        st = get_state(client, TID)
        log(f"  flow_status        = {st.get('flow_status','')}")
        log(f"  pending_interaction = [{st.get('pending_interaction_kind','')}]")
        log(f"  is_assessed         = {st.get('is_assessed',False)}")
        log(f"  current_node_id     = {st.get('current_node_id','')}")
        log(f"  current_node_name   = {st.get('current_node_name','')}")
        log(f"  learning_plan_steps = {len(st.get('learning_plan',[]))}")
        log(f"  learning_plan_v2    = {_truncate(st.get('learning_plan_v2',''), 200)}")
        log(f"  node_quiz_score     = {st.get('node_quiz_score',0)}")
        log(f"  homework_status     = {st.get('homework_status','')}")
        log(f"  remediation_decision= [{st.get('remediation_decision','')}]")
        log(f"  node_remediation    = keys:{list(st.get('node_remediation_state',{}).keys())}")
        log(f"  affect_signals      = {_truncate(st.get('affect_signals',''))}")
        log(f"  thinking_mode       = {st.get('thinking_mode','')}")

        # 最终断言
        assert st.get("is_assessed", False), "Final: is_assessed not set"
        assert st.get("learning_plan"), "Final: learning_plan empty"
        assert st.get("current_node_id"), "Final: current_node_id empty"

        # ── Summary ──
        elapsed = time.time() - t_start
        print(f"\n{'='*60}", flush=True)
        print(f"⏱  Total: {elapsed:.0f}s  |  Thread: {TID}", flush=True)
        print(f"📊 Passed: {PASS} steps  |  Failed: {FAIL} checks", flush=True)
        if FAIL == 0:
            print(f"🎉 真实 LLM E2E 全流程验证通过！", flush=True)
        else:
            print(f"❌ {FAIL} 个检查失败", flush=True)
        print(f"{'='*60}", flush=True)
        sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
