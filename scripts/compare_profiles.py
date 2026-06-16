#!/usr/bin/env python3
"""画像对比实验：全A自评 vs 全D自评，比较教学差异。"""
import json, sys, os, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update({
    'AI_TUTOR_EMBEDDING_PROVIDER': 'local', 'OPENAI_API_KEY': 'test-key',
    'CHAT_PROFILE': 'qwen', 'LLM_PROVIDER': 'openai',
    'MODEL_NAME': 'qwen-plus', 'OPENAI_API_BASE': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
})
t0 = time.time()

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.interfaces.api.runtime import build_runtime
from ai_tutor_agent.interfaces.api.app import create_api_app
from tests.asgi_test_client import SyncASGITestClient as TestClient

get_settings.cache_clear()
runtime = build_runtime()
app = create_api_app(runtime_factory=lambda: runtime)


def gs(c, t):
    r = c.get(f'/api/history/{t}')
    return json.loads(r.text)['state'] if r.status_code == 200 else {}


def wait(c, t, pik_target='', to=300):
    """等待 graph 停在一个需要用户输入的状态或有 pending_interaction_kind。"""
    dl = time.monotonic() + to
    while time.monotonic() < dl:
        c.get(f'/api/stream?thread_id={t}')
        s = gs(c, t)
        p = s.get('pending_interaction_kind', '')
        f = s.get('flow_status', '')
        # Target-specific: return when pik matches
        if pik_target and p == pik_target:
            return s
        # No target: return when there's ANY pending_interaction_kind
        if not pik_target and p:
            return s
        # Also return for genuinely terminal flow_statuses that don't
        # set pik (e.g. awaiting_assessment sets pik="")
        terminal_no_pik = {'awaiting_assessment', 'awaiting_topic_confirmation',
                           'awaiting_next_step_selector', 'greeting', 'topic_intake',
                           'assessment_dialog'}
        if not pik_target and f in terminal_no_pik:
            return s
        # 'normal' is NOT terminal here — it appears on intermediate checkpoints
        # during graph execution. Only return when pik is set.
        time.sleep(0.5)
    return gs(c, t)


def run_session(client, tid, answer_letter, label):
    print(f'\n{"=" * 60}', flush=True)
    print(f'  {label} (all answers = "{answer_letter}")', flush=True)
    print(f'{"=" * 60}', flush=True)
    step_start = time.time()

    # 1. Start & confirm topic
    client.post('/api/sessions', json={'thread_id': tid})
    client.post('/api/start', json={'thread_id': tid, 'topic': '根轨迹法绘图规则'})
    wait(client, tid, to=60)
    client.post('/api/confirm_topic', json={'thread_id': tid, 'confirmed': True, 'start_mode': 'assessment'})
    s = wait(client, tid, to=60)
    asm = s.get('assessment_questions', [])
    print(f'  [1] Assessment questions: {len(asm)}', flush=True)

    # 2. Submit all answers with same choice
    answers = {str(q.get('id', i)): answer_letter for i, q in enumerate(asm)}
    client.post('/api/submit_assessment', json={'thread_id': tid, 'answers': answers})
    s = wait(client, tid, to=300)
    elapsed = time.time() - step_start

    # 3. Extract profile data
    profile = {
        'difficulty_level': s.get('difficulty_level'),
        'teaching_strategy': s.get('teaching_strategy'),
        'assessment_radar': s.get('assessment_radar', {}),
        'assessment_concept_gaps': s.get('assessment_concept_gaps', {}),
        'current_node_id': s.get('current_node_id'),
        'current_node_name': s.get('current_node_name'),
        'learning_plan': s.get('learning_plan', []),
        'tutor_content': s.get('tutor_content', ''),
        'is_assessed': s.get('is_assessed'),
        'node_content': s.get('node_content', ''),
    }

    print(f'  [2] is_assessed={profile["is_assessed"]}', flush=True)
    print(f'      difficulty_level={profile["difficulty_level"]}', flush=True)
    print(f'      teaching_strategy={profile["teaching_strategy"]}', flush=True)
    print(f'      node={profile["current_node_id"]} - {profile["current_node_name"]}', flush=True)
    print(f'      plan_steps={len(profile["learning_plan"])}', flush=True)

    radar = profile['assessment_radar']
    if radar:
        dims = radar.get('dimensions', [])
        ss = radar.get('self_scores', [])
        os_ = radar.get('objective_scores', [])
        print(f'      radar_dims={dims}', flush=True)
        print(f'      radar_self={ss}', flush=True)
        print(f'      radar_obj={os_}', flush=True)

    gaps = profile['assessment_concept_gaps']
    if gaps and isinstance(gaps, dict):
        flat = {k: round(v, 1) for k, v in gaps.items() if isinstance(v, (int, float))}
        if flat:
            print(f'      concept_gaps={flat}', flush=True)

    tc = profile['tutor_content']
    print(f'  [Tutor Preview] {tc[:500]}', flush=True)
    print(f'  [2] time={elapsed:.0f}s', flush=True)

    # Print learning plan
    for si, step in enumerate(profile['learning_plan']):
        nids = step.get('node_ids', [])
        nns = step.get('node_names', [])
        pairs = ', '.join(f'{nid}/{nn}' for nid, nn in zip(nids, nns))
        print(f'      plan[{si}]: {step.get("step_name")} -> [{pairs}]', flush=True)

    return profile, s


# ── Run ──
with TestClient(app) as c:
    prof_a, _ = run_session(c, 'cmp-a-' + str(int(time.time() % 100000)), 'A', '初学者画像（全部选A自评）')
    print(f'\n  >>> 累计 {time.time() - t0:.0f}s，开始第二组...', flush=True)
    prof_d, _ = run_session(c, 'cmp-d-' + str(int(time.time() % 100000)), 'D', '高能力画像（全部选D自评）')

# ── Comparison ──
print('\n\n' + '=' * 95)
print('  画像对比总结')
print('=' * 95)

header = f'{"指标":<28} {"全A（初学者）":<35} {"全D（高能力）":<35}'
print(header)
print('-' * 95)


def cmp(name):
    a = prof_a.get(name, '?')
    d = prof_d.get(name, '?')
    print(f'{name:<28} {str(a):<35} {str(d):<35}')


cmp('difficulty_level')
cmp('teaching_strategy')
cmp('is_assessed')
cmp('current_node_id')
cmp('current_node_name')

# Plan steps
pa = prof_a.get('learning_plan', [])
pd = prof_d.get('learning_plan', [])
print(f'{"plan_step_count":<28} {str(len(pa)):<35} {str(len(pd)):<35}')
for i in range(max(len(pa), len(pd))):
    sta = pa[i] if i < len(pa) else {}
    std = pd[i] if i < len(pd) else {}
    na = f'{sta.get("step_name","?")} ({len(sta.get("node_ids",[]))}nodes)'
    nd = f'{std.get("step_name","?")} ({len(std.get("node_ids",[]))}nodes)'
    print(f'{"  plan[%d]" % i:<28} {na:<35} {nd:<35}')

# Tutor content length
len_a = len(prof_a.get('tutor_content', ''))
len_d = len(prof_d.get('tutor_content', ''))
print(f'{"tutor_length":<28} {str(len_a):<35} {str(len_d):<35}')

# Radar comparison
ra = prof_a.get('assessment_radar', {})
rd = prof_d.get('assessment_radar', {})
self_a = ra.get('self_scores', [])
self_d = rd.get('self_scores', [])
obj_a = ra.get('objective_scores', [])
obj_d = rd.get('objective_scores', [])
avg_self_a = sum(self_a) / len(self_a) if self_a else 0
avg_self_d = sum(self_d) / len(self_d) if self_d else 0
avg_obj_a = sum(obj_a) / len(obj_a) if obj_a else 0
avg_obj_d = sum(obj_d) / len(obj_d) if obj_d else 0
print(f'{"radar_self_average":<28} {avg_self_a:<35.1f} {avg_self_d:<35.1f}')
print(f'{"radar_obj_average":<28} {avg_obj_a:<35.1f} {avg_obj_d:<35.1f}')

# Keyword presence in tutor content
tc_a = prof_a.get('tutor_content', '')
tc_d = prof_d.get('tutor_content', '')
print(f'\n{"Tutor 关键词对比":^95}')
print('-' * 95)
print(f'{"关键词":<20} {"全A（初学者）":<35} {"全D（高能力）":<35}')
print('-' * 95)
for kw, desc in [
    ('基础', '"基础"'),
    ('简单', '"简单"'),
    ('深入', '"深入"'),
    ('反馈', '"反馈"'),
    ('根轨迹', '"根轨迹"'),
    ('传递函数', '"传递函数"'),
    ('开环', '"开环"'),
    ('闭环', '"闭环"'),
    ('稳定性', '"稳定性"'),
    ('控制', '"控制"'),
    ('概念', '"概念"'),
    ('规则', '"规则"'),
]:
    in_a = kw in tc_a
    in_d = kw in tc_d
    print(f'{desc:<20} {"✅ 出现" if in_a else "❌ 未出现":<35} {"✅ 出现" if in_d else "❌ 未出现":<35}')

print(f'\n⏱ 总耗时: {time.time() - t0:.0f}s', flush=True)
