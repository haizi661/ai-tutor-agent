#!/usr/bin/env python3
"""录制 AI Tutor Agent 完整学习闭环：测评→路径→多节点→路径完成→新一轮。"""
import argparse, json, re, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
def log(s): print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)
def esc(pg):
    try: pg.keyboard.press("Escape"); time.sleep(0.2)
    except: pass

def wait_end(pg, t=300):
    dl=time.time()+t
    while time.time()<dl:
        try:
            n=pg.evaluate("""()=>[...document.querySelectorAll('.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator')].filter(e=>e.offsetParent&&e.style.display!=='none').length""")
            if n==0: time.sleep(2)
            if pg.evaluate("""()=>[...document.querySelectorAll('.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator')].filter(e=>e.offsetParent&&e.style.display!=='none').length""")==0: return True
        except: pass; time.sleep(1)
    return False

def find_btn(pg, txt, t=180):
    dl=time.time()+t
    while time.time()<dl:
        esc(pg)
        for s in [f"button:text-is('{txt}')",f"button:has-text('{txt}')",f".chip:text-is('{txt}')"]:
            try:
                el=pg.locator(s).first
                if el.count()>0 and el.is_visible(): el.click(); return True
            except: pass
        time.sleep(1)
    return False

def type_send(pg, msg):
    esc(pg); ta=pg.locator("textarea").first
    try: ta.wait_for(state="visible",timeout=5000)
    except: pass
    ta.click(); ta.fill(msg); time.sleep(0.3); pg.keyboard.press("Enter"); time.sleep(1)

def wait_card(pg, selector, t=120):
    dl=time.time()+t
    while time.time()<dl:
        if pg.locator(selector).first.count()>0: return True
        time.sleep(2)
    return False

# ── Stepper (assessment) ──
def answer_stepper(pg, label, total):
    choices="CBADCBADCBAD"
    for i in range(total):
        for _ in range(30):
            if pg.locator(".q-opt:not(.locked)").first.count()>0: break
            time.sleep(1)
        k=choices[i%len(choices)]
        for s in [f".q-opt:not(.locked) .q-opt-letter:text-is('{k}')", f".q-opt:not(.locked)[data-v='{k}']"]:
            try:
                el=pg.locator(s).first
                if el.count()>0 and el.is_visible(): el.click(); break
            except: pass
        time.sleep(0.3)
        is_last=pg.locator(".q-stepper-submit:not([disabled])").first
        if is_last.count()>0 and is_last.is_visible():
            is_last.click(); log(f"  {label} #{i+1}/{total}: {k} → ✅提交"); time.sleep(2); return
        nxt=pg.locator(".q-stepper-next:not([disabled])").first
        if nxt.count()>0 and nxt.is_visible(): nxt.click(); log(f"  {label} #{i+1}/{total}: {k}")
        time.sleep(0.5)

# ── Objective test card ──
def answer_objtest(pg, label):
    # Dismiss any old locked/submitted test cards
    pg.locator(".obj-test-card.submitted-collapsed").all()
    pg.evaluate("""()=>{document.querySelectorAll('.obj-test-card.submitted-collapsed').forEach(c=>c.remove())}""")
    time.sleep(0.5)
    qs=pg.locator(".obj-test-q:not(.submitted-collapsed .obj-test-q)").all()
    if len(qs)==0: qs=pg.locator(".obj-test-q").all()
    total=len(qs)
    log(f"  {label}: {total}题")
    choices="CBADCBADCBAD"
    for i in range(total):
        k=choices[i%len(choices)]
        q_el=pg.locator(f".obj-test-q").nth(i)
        # Only click non-locked options
        opt=q_el.locator(f".obj-test-opt:not(.locked)[data-v='{k}']").first
        if opt.count()==0:
            opt=q_el.locator(f".obj-test-opt[data-v='{k}']").first
        if opt.count()>0:
            try: opt.click(timeout=5000)
            except: pass
            log(f"  {label} #{i+1}/{total}: {k}")
            time.sleep(0.3)
    time.sleep(0.5)
    for _ in range(30):
        sub=pg.locator(".obj-test-submit:not([disabled])").first
        if sub.count()>0: break
        time.sleep(0.5)
    sub=pg.locator(".obj-test-submit:not([disabled])").first
    if sub.count()>0: sub.click(); log(f"  {label}: ✅提交"); time.sleep(3); wait_end(pg)

# ── One node cycle: post_lesson → test → score → continue ──
def do_node_cycle(pg, node_num):
    """Execute one full node learning cycle. Returns 'continue' or 'plan_completed'."""
    # Wait for post_lesson card (longer timeout for subsequent nodes)
    log(f"  节点{node_num}: 等待课后卡...")
    card_ok = wait_card(pg, ".post-lesson-card", t=180)
    if card_ok:
        find_btn(pg, "我懂了，进入小测", t=30); log("  ✅卡片→小测")
    else:
        log("  ⚠️卡片未出现，文本fallback"); type_send(pg, "开始测试")
    wait_end(pg)

    # Wait for test questions
    log(f"  节点{node_num}: 等待测试题...")
    test_ok = False
    for _ in range(90):
        if pg.locator(".obj-test-q,.q-stepper-label").first.count()>0: test_ok=True; break
        time.sleep(2)
    if test_ok:
        if pg.locator(".obj-test-q").first.count()>0:
            answer_objtest(pg, f"节点{node_num}")
        elif pg.locator(".q-stepper-label").first.count()>0:
            t=pg.locator(".q-stepper-label").first.inner_text()
            total=int(re.search(r'共\s*(\d+)\s*题',t).group(1)) if re.search(r'共\s*(\d+)\s*题',t) else 10
            answer_stepper(pg, f"节点{node_num}", total)
    else:
        log(f"  ⚠️测试题超时"); return "timeout"
    wait_end(pg)

    # Handle scoring result
    log(f"  节点{node_num}: 评分...")
    time.sleep(3)
    # Try remediation first
    for btn_text in ["稍后复习，加入错题本", "稍后复习", "继续做变式训练", "复习本节点"]:
        if find_btn(pg, btn_text, t=10):
            log(f"  点击'{btn_text}'"); wait_end(pg); break
    # Wait for continue/new-round card (or use fallback)
    card_found = False
    for _ in range(40):
        if pg.locator("button:has-text('开始新一轮完整学习')").first.count()>0:
            log(f"  节点{node_num}: 🎯路径完成！")
            return "plan_completed"
        if pg.locator("button:has-text('开始下一个节点')").first.count()>0:
            card_found = True; break
        time.sleep(2)
    if card_found:
        find_btn(pg, "开始下一个节点", t=10)
        log(f"  节点{node_num}: ✅继续下一节点"); wait_end(pg)
        return "continue"
    # Fallback: use API directly (bypass SSE card rendering issue)
    log(f"  节点{node_num}: 卡片未出现，API直发")
    tid = pg.evaluate("()=>window.localStorage.getItem('ai_tutor_last_thread_id') || window.app?.state?.currentThreadId || ''")
    if tid:
        req = urllib.request.Request('http://127.0.0.1:8000/api/answer',
            data=json.dumps({'thread_id': tid, 'answer': '继续'}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=30)
        log(f"  API: 已发送'继续'"); time.sleep(2)
        # Reload → frontend reconnects SSE → should restore to post_lesson_choice
        pg.goto(f"{BASE}/?thread={tid}", wait_until="networkidle", timeout=30000)
        time.sleep(5); wait_end(pg)
        # After reload, state should be post_lesson_choice for next node
        # Return 'continue' so the loop handles the next node normally
        return "continue"
    return "stuck"

def record(out, headless=True):
    log(f"Chromium headless={headless}")
    with sync_playwright() as p:
        b=p.chromium.launch(headless=headless,args=["--no-sandbox"])
        ctx=b.new_context(viewport={"width":1440,"height":900},
                          record_video_dir=str(Path(out).parent),
                          record_video_size={"width":1440,"height":900})
        pg=ctx.new_page(); sd=Path(out).parent; step=0
        def ss(n): nonlocal step; step+=1; pg.screenshot(path=str(sd/f"{step:02d}_{n}.png"))

        # ── SESSION 1: 初始化 ──
        log("SESSION 1: 初始化")
        pg.goto(BASE,wait_until="networkidle",timeout=30000); time.sleep(2)
        ss("home")
        # 直接在着陆页点击课程方向（auto-confirm 会跳过主题确认，直接进入测评）
        for _ in range(30):
            chip = pg.locator('[data-starter-prompt]').first
            if chip.count()>0 and chip.is_visible(): break
            time.sleep(1)
        pg.locator('[data-starter-prompt]').first.click()
        log("  点击课程方向 → auto-confirm → 直达测评")
        time.sleep(5)
        # Wait for assessment stepper
        for _ in range(60):
            if pg.locator(".q-stepper-label").first.count()>0: break
            time.sleep(2)
        t=pg.locator(".q-stepper-label").first.inner_text()
        total=int(re.search(r'共\s*(\d+)\s*题',t).group(1)) if re.search(r'共\s*(\d+)\s*题',t) else 10
        ss("assess_start")
        log(f"  测评 {total} 题")

        # ── Assessment ──
        answer_stepper(pg,"测评",total); wait_end(pg)
        ss("assess_done")

        # ── Plan + Tutor ──
        wait_end(pg); time.sleep(5); ss("plan")
        wait_end(pg); time.sleep(3); ss("tutor")
        log("  Session 1: 测评→画像→路径→讲解 ✅")

        # ── NODE CYCLES ──
        for node_num in range(1, 10):
            result = do_node_cycle(pg, node_num)
            ss(f"node{node_num}_{result}")
            if result == "plan_completed":
                log(f"  🎯 所有节点完成！")
                break
            elif result == "timeout":
                log(f"  ⚠️ 节点{node_num}超时，跳过")
                break
            elif result == "stuck":
                log(f"  ⚠️ 节点{node_num}卡住，跳过")
                break

        # ── NEW ROUND ──
        log("SESSION 2: 新一轮完整学习")
        ok = find_btn(pg, "开始新一轮完整学习", t=30)
        if not ok:
            tid = pg.evaluate("()=>window.localStorage.getItem('ai_tutor_last_thread_id') || window.app?.state?.currentThreadId || ''")
            if tid:
                req = urllib.request.Request('http://127.0.0.1:8000/api/answer',
                    data=json.dumps({'thread_id': tid, 'answer': '开始新一轮完整学习'}).encode(),
                    headers={'Content-Type': 'application/json'}, method='POST')
                urllib.request.urlopen(req, timeout=30)
                log("  API: 已发送'开始新一轮完整学习'")
                time.sleep(2)
                pg.goto(f"{BASE}/?thread={tid}", wait_until="networkidle", timeout=30000)
                time.sleep(3)
        wait_end(pg); time.sleep(5); ss("new_plan")
        log("  ✅ 新学习路径已生成！")

        # ── Final ──
        try: pg.locator("button:has-text('学习路径')").first.click(timeout=5000)
        except:
            try: pg.locator("[aria-label*='学习路径']").first.click(timeout=3000)
            except: pass
        time.sleep(2); ss("final")
        pg.screenshot(path=str(sd/"fullpage.png"),full_page=True)

        time.sleep(2); ctx.close(); b.close()

    vf=sorted(Path(out).parent.glob("*.webm"),key=lambda p:p.stat().st_mtime,reverse=True)
    if vf: vf[0].rename(out); log(f"✅视频:{out} ({Path(out).stat().st_size/1024/1024:.1f}MB)")
    log("🎉完成!")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="scripts/demo_video.webm")
    p.add_argument("--headless",default="true",choices=["true","false"])
    a=p.parse_args()
    import urllib.request
    try:
        if urllib.request.urlopen(f"{BASE}/api/health",timeout=5).status!=200:
            print("❌ 服务未就绪"); sys.exit(1)
    except: print("❌ 服务未连接"); sys.exit(1)
    o=Path(a.output); o.parent.mkdir(parents=True,exist_ok=True)
    record(str(o),headless=a.headless=="true")
