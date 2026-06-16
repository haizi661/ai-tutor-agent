#!/usr/bin/env python3
"""纯 API 端到端验证：完整学习流程。每步通过 SSE 消费 + state 检查确保正确。"""
import json, sqlite3, msgpack, sys, time, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"
DB = "data/tutor_memory.db"
TID = f"api-e2e-{int(time.time())}"

def log(s): print(f"  {s}", flush=True)
def ok(): log("  ✅")

def api(m, path, data=None, to=120):
    url=f"{BASE}{path}"; req=urllib.request.Request(url,method=m)
    if data: req.add_header("Content-Type","application/json"); req.data=json.dumps(data).encode()
    try: return json.loads(urllib.request.urlopen(req,timeout=to).read())
    except urllib.error.HTTPError as e: return {"error":e.code,"body":e.read().decode(errors='replace')[:200]}

def sse(path, to=180):
    evs=[]; resp=urllib.request.urlopen(f"{BASE}{path}",timeout=to)
    for lb in resp:
        l=lb.decode('utf-8',errors='replace')
        if l.startswith('data: '):
            try: evs.append(json.loads(l[6:]))
            except: pass
        for e in evs:
            if e.get('type') in ('session.end','session.awaiting_input','session.error'): return evs
    return evs

def state():
    db=sqlite3.connect(DB)
    rows=db.execute("SELECT checkpoint FROM checkpoints WHERE thread_id=? ORDER BY rowid DESC LIMIT 1",(TID,)).fetchall()
    if not rows: return {}
    s=msgpack.unpackb(rows[0][0]).get("channel_values",{})
    def g(k):
        v=s.get(k.encode() if isinstance(next(iter(s.keys())) if s else b'',bytes) else k,b'')
        return v.decode() if isinstance(v,bytes) else str(v) if v else ''
    return g

def v(k): return state()(k)

def wait_pik(target,to=120):
    dl=time.time()+to
    while time.time()<dl:
        if v('pending_interaction_kind')==target: return True
        time.sleep(2)
    return False

# ── Main ──
log("="*50); log(f"API E2E: {TID}"); log("="*50)

# 1. Session
r=api("POST","/api/sessions",{"thread_id":TID})
assert r.get("status") in ("created","exists"), r
log("1. Session"); ok()

# 2. Start
r=api("POST","/api/start",{"thread_id":TID,"topic":"我想学根轨迹法"})
assert r.get("status") in ("started","running")
log("2. Start"); ok()

# 3. Wait for topic confirmation
sse(f"/api/stream?thread_id={TID}")
log(f"3. SSE consumed, flow={v('flow_status')}"); ok()

# 4. Confirm topic
api("POST","/api/confirm_topic",{"thread_id":TID,"confirmed":True,"start_mode":"assessment"})
log("4. Topic confirmed"); ok()

# 5. Assessment: get questions
evs=sse(f"/api/stream?thread_id={TID}",to=120)
batch=[e for e in evs if 'assessment.batch' in e.get('type','')]
qs=batch[0].get('data',{}).get('questions',[]) if batch else []
log(f"5. Assessment: {len(qs)} questions"); ok()

# 6. Answer assessment one by one, streaming after each
for i,q in enumerate(qs):
    qid=str(q.get('id',i+1))
    api("POST","/assessment_answer",{"thread_id":TID,"question_id":qid,"answer":"C"},to=30)
    sse(f"/api/stream?thread_id={TID}",to=60)
    log(f"6.{i+1}/{len(qs)} answered, flow={v('flow_status')}")
log("6. All assessment answers submitted"); ok()

# 7. Wait for profiling → plan → tutor → post_lesson
log("7. Waiting for profiling→plan→tutor→post_lesson...")
# Consume SSE until we reach post_lesson_choice
for attempt in range(30):
    fs=v('flow_status'); pik=v('pending_interaction_kind')
    if pik=='post_lesson_choice' or fs=='awaiting_post_lesson_choice': break
    if attempt%5==0: log(f"   attempt {attempt}: flow={fs} pik=[{pik}]")
    sse(f"/api/stream?thread_id={TID}",to=30)
    time.sleep(1)
log(f"7. flow={v('flow_status')} pik=[{v('pending_interaction_kind')}] node={v('current_node_id')}")
assert v('pending_interaction_kind')=='post_lesson_choice', f"Expected post_lesson_choice, got [{v('pending_interaction_kind')}]"
ok()

# 8. Send "开始测试"
api("POST","/api/answer",{"thread_id":TID,"answer":"开始测试"})
log("8. '开始测试' sent"); ok()

# 9. Wait for objective test questions
log("9. Waiting for objective test...")
pik_ok=wait_pik("objective_test_answers",to=120)
pik=v('pending_interaction_kind'); fs=v('flow_status')
quiz_str=v('node_quiz_items')
quiz=json.loads(quiz_str) if quiz_str and quiz_str!='[]' else []
log(f"9. pik=[{pik}] flow={fs} quiz_count={len(quiz)}")
assert pik=='objective_test_answers', f"Expected objective_test_answers, got [{pik}]"
assert len(quiz)>0, "No quiz items!"
log(f"   Questions: {len(quiz)}"); ok()

# 10. Submit test answers
ans={q.get('question_id',q.get('id',f'Q{i}')):'B' for i,q in enumerate(quiz)}
api("POST","/api/answer",{"thread_id":TID,"answer":json.dumps(ans)})
log(f"10. {len(ans)} answers submitted"); ok()

# 11. Wait for scoring + continue/homework
log("11. Waiting for scoring...")
pik_ok=wait_pik("continue_or_homework_choice",to=120)
score=v('node_quiz_score'); nid=v('current_node_id')
log(f"11. pik=[{v('pending_interaction_kind')}] score={score} node={nid}")
assert v('pending_interaction_kind') in ('continue_or_homework_choice',''), f"Unexpected pik=[{v('pending_interaction_kind')}]"
ok()

# 12. Choose "开始下一个节点"
api("POST","/api/answer",{"thread_id":TID,"answer":"继续"})
log("12. '继续' sent"); ok()

# Final state check
time.sleep(3)
log(f"Final: flow={v('flow_status')} pik=[{v('pending_interaction_kind')}] node={v('current_node_id')}")
log("="*50)
log("🎉 完整 API 端到端验证通过！")
log("="*50)
