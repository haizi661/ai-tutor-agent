#!/usr/bin/env python3
"""单独录制 Phase 8: 作业生成与结业总结。从当前会话继续。"""
import json, re, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT_DIR = Path("scripts/phase_recordings")
THREAD_FILE = OUT_DIR / ".last_thread_id"

def log(s): print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)
def esc(pg):
    try: pg.keyboard.press("Escape"); time.sleep(0.2)
    except: pass

def wait_idle(pg, t=300):
    dl = time.time()+t
    while time.time()<dl:
        try:
            n=pg.evaluate("""()=>[...document.querySelectorAll('.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator')].filter(e=>e.offsetParent&&e.style.display!=='none').length""")
            if n==0: time.sleep(2)
            if pg.evaluate("""()=>[...document.querySelectorAll('.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator')].filter(e=>e.offsetParent&&e.style.display!=='none').length""")==0: return True
        except: pass; time.sleep(1)
    return False

def find_btn(pg, txt, t=60):
    dl=time.time()+t
    while time.time()<dl:
        esc(pg)
        for s in [f"button:text-is('{txt}')",f"button:has-text('{txt}')"]:
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

def answer_objtest(pg,label):
    choices="CBADCBADCBAD"
    try: qs=pg.locator(".obj-test-q").all(); total=len(qs) if qs else 10
    except: total=10
    log(f"  {label}: {total}题")
    for i in range(min(total,10)):
        k=choices[i%len(choices)]
        try:
            q=pg.locator(".obj-test-q").nth(i)
            o=q.locator(f".obj-test-opt[data-v='{k}']").first
            if o.count()>0: o.click(); log(f"  #{i+1}: {k}"); time.sleep(0.3)
        except: pass
    time.sleep(0.5)
    for _ in range(30):
        try:
            s=pg.locator(".obj-test-submit:not([disabled])").first
            if s.count()>0: s.click(); log(f"  ✅提交"); break
        except: pass; time.sleep(0.5)

# Check service
try:
    if urllib.request.urlopen(f"{BASE}/api/health",timeout=5).status!=200:
        print("❌ 服务未就绪"); sys.exit(1)
except: print("❌ 服务未连接"); sys.exit(1)

tid = THREAD_FILE.read_text().strip() if THREAD_FILE.exists() else ""
if not tid: print("❌ 无 thread_id"); sys.exit(1)
log(f"使用会话: {tid}")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,args=["--no-sandbox"])
    ctx=b.new_context(viewport={"width":1440,"height":900},
                      record_video_dir=str(OUT_DIR),
                      record_video_size={"width":1440,"height":900})
    pg=ctx.new_page()
    t0=time.time()
    
    pg.goto(f"{BASE}/?thread={tid}",wait_until="networkidle",timeout=30000)
    time.sleep(3)
    
    # Wait for tutor content to finish (next node might be loading)
    log("等待下一节点教学完成...")
    wait_idle(pg, timeout=300)
    time.sleep(2)
    pg.screenshot(path=str(OUT_DIR/"phase08_01_resume.png"))
    
    # Find post_lesson card or proceed to test
    for _ in range(60):
        try:
            if pg.locator("button:has-text('我懂了，进入小测')").first.count()>0:
                find_btn(pg, "我懂了，进入小测", t=10)
                log("→ 进入小测")
                break
        except: pass
        time.sleep(1)
    
    # Wait for test
    wait_idle(pg, timeout=120)
    
    # Answer test if present
    try:
        if pg.locator(".obj-test-q").first.count()>0:
            answer_objtest(pg, "Phase8客观题")
            wait_idle(pg, timeout=180)
    except: pass
    
    pg.screenshot(path=str(OUT_DIR/"phase08_02_test_done.png"))
    
    # Handle remediation
    for btn in ["稍后复习，加入错题本","稍后复习"]:
        if find_btn(pg, btn, t=10): log(f"选择: {btn}"); wait_idle(pg, timeout=60); break
    
    # Wait for continue/homework card
    for _ in range(90):
        try:
            if pg.locator("button:has-text('今天就到这里')").first.count()>0:
                break
            if pg.locator("button:has-text('今天不学了')").first.count()>0:
                break
        except: pass
        time.sleep(2)
    
    pg.screenshot(path=str(OUT_DIR/"phase08_03_continue_card.png"))
    
    # Click "今天就到这里"
    found = find_btn(pg, "今天就到这里", t=30)
    if not found:
        found = find_btn(pg, "今天不学了", t=10)
    if not found:
        # API fallback
        req = urllib.request.Request('http://127.0.0.1:8000/api/answer',
            data=json.dumps({'thread_id': tid, 'answer': '今天就到这里'}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=30)
        log("API: 发送'今天就到这里'")
    
    wait_idle(pg, timeout=300)
    time.sleep(3)
    pg.screenshot(path=str(OUT_DIR/"phase08_04_homework.png"))
    
    # Check for completion wrap-up
    try:
        if pg.locator("button:has-text('查看学习报告')").first.count()>0:
            find_btn(pg, "查看学习报告", t=10)
            wait_idle(pg, timeout=120)
            time.sleep(2)
            pg.screenshot(path=str(OUT_DIR/"phase08_05_wrapup.png"))
            log("✅ 结业总结已生成")
    except: pass
    
    elapsed = time.time()-t0
    pg.screenshot(path=str(OUT_DIR/"phase08_final.png"), full_page=True)
    
    time.sleep(2); ctx.close(); b.close()

# Rename video
vfs=sorted(OUT_DIR.glob("*.webm"),key=lambda p:p.stat().st_mtime,reverse=True)
if vfs:
    vf=vfs[0]; target=OUT_DIR/"phase08_homework_completion.webm"
    if vf!=target: vf.rename(target)
    log(f"✅ 视频: {target} ({target.stat().st_size/1024/1024:.1f}MB)")

log("🎉 Phase 8 完成!")
