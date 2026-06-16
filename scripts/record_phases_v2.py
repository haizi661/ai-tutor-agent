#!/usr/bin/env python3
"""AI Tutor Agent 完整学习流程 — 单会话分阶段录制脚本。

在单个浏览器会话中录制完整 14 步主流程，在每阶段边界记录时间戳。
录制完成后用 ffmpeg 按时间戳切分为 8 个独立阶段视频，并生成映射文档。

用法:
  python scripts/record_phases_v2.py                    # 全部阶段
  python scripts/record_phases_v2.py --headless false   # 可视化调试
"""

import argparse, json, os, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT_DIR = Path("scripts/phase_recordings")
FULL_VIDEO = OUT_DIR / "00_full_flow.webm"


def log(s: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)


def esc(page):
    try:
        page.keyboard.press("Escape")
        time.sleep(0.2)
    except Exception:
        pass


def wait_idle(page, timeout: int = 300) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            n = page.evaluate(
                """()=>[...document.querySelectorAll(
                    '.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator'
                )].filter(e=>e.offsetParent&&e.style.display!=='none').length"""
            )
            if n == 0:
                time.sleep(2)
                n2 = page.evaluate(
                    """()=>[...document.querySelectorAll(
                        '.typing-indicator,.loading-dots,.stream-cursor,.thinking-indicator'
                    )].filter(e=>e.offsetParent&&e.style.display!=='none').length"""
                )
                if n2 == 0:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def find_and_click(page, text: str, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        esc(page)
        for sel in [
            f"button:text-is('{text}')",
            f"button:has-text('{text}')",
            f".chip:text-is('{text}')",
            f"[data-starter-prompt]:has-text('{text}')",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    return True
            except Exception:
                pass
        time.sleep(1)
    return False


def type_and_send(page, msg: str) -> None:
    esc(page)
    ta = page.locator("textarea").first
    try:
        ta.wait_for(state="visible", timeout=5000)
    except Exception:
        pass
    ta.click()
    ta.fill(msg)
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(1)


# Phase boundary timestamps (seconds from recording start)
phase_timestamps: dict[int, tuple[float, str, str]] = {}
recording_start: float = 0.0


def mark_phase(page, num: int, name: str, cn_name: str) -> None:
    """Mark a phase boundary with screenshot and timestamp."""
    global recording_start
    elapsed = time.time() - recording_start

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ss_name = f"phase{num:02d}_{name}.png"
    page.screenshot(path=str(OUT_DIR / ss_name))
    log(f"  📸 {ss_name} (t={elapsed:.1f}s)")

    phase_timestamps[num] = (elapsed, name, cn_name)


# ═══════════════════════════════════════════════════════════════════════════════
#  Core flow actions
# ═══════════════════════════════════════════════════════════════════════════════

def answer_stepper(page, label: str) -> None:
    """Answer assessment stepper questions."""
    choices = "CBADCBADCBAD"
    total = 10
    try:
        t = page.locator(".q-stepper-label").first.inner_text()
        m = re.search(r"共\s*(\d+)\s*题", t)
        if m:
            total = int(m.group(1))
    except Exception:
        pass

    log(f"  {label}: {total} 题作答...")
    for i in range(total):
        k = choices[i % len(choices)]
        for _ in range(30):
            try:
                if page.locator(".q-opt:not(.locked)").first.count() > 0:
                    break
            except Exception:
                pass
            time.sleep(1)

        for sel in [
            f".q-opt:not(.locked) .q-opt-letter:text-is('{k}')",
            f".q-opt:not(.locked)[data-v='{k}']",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    break
            except Exception:
                pass
        time.sleep(0.3)

        is_last = (
            page.locator(".q-stepper-submit:not([disabled])").first.count() > 0
        )
        if is_last:
            try:
                page.locator(".q-stepper-submit:not([disabled])").first.click()
                log(f"  {label} #{i+1}/{total}: {k} → ✅提交")
            except Exception:
                pass
            time.sleep(2)
            break
        else:
            try:
                page.locator(".q-stepper-next:not([disabled])").first.click()
                log(f"  {label} #{i+1}/{total}: {k}")
            except Exception:
                pass
            time.sleep(0.5)


def answer_objtest(page, label: str) -> None:
    """Answer objective test questions."""
    choices = "CBADCBADCBAD"
    try:
        qs = page.locator(".obj-test-q").all()
        total_q = len(qs) if qs else 10
    except Exception:
        total_q = 10

    log(f"  {label}: {total_q} 题")
    for i in range(min(total_q, 10)):
        k = choices[i % len(choices)]
        try:
            q_el = page.locator(".obj-test-q").nth(i)
            opt = q_el.locator(f".obj-test-opt[data-v='{k}']").first
            if opt.count() > 0:
                opt.click()
                log(f"  {label} #{i+1}: {k}")
                time.sleep(0.3)
        except Exception:
            pass

    time.sleep(0.5)
    for _ in range(30):
        try:
            sub = page.locator(".obj-test-submit:not([disabled])").first
            if sub.count() > 0:
                sub.click()
                log(f"  {label}: ✅提交")
                break
        except Exception:
            pass
        time.sleep(0.5)


def record_full_flow(headless: bool = True) -> bool:
    """Record complete flow in single browser session. Returns True if successful."""
    global recording_start, phase_timestamps
    phase_timestamps = {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(OUT_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        recording_start = time.time()

        try:
            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: 入口 → 主题确认 → 测评生成
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 1: 入口与主题确认")
            log("=" * 60)
            page.goto(BASE, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            mark_phase(page, 1, "entry_topic", "入口与主题确认")

            # Click course direction chip (auto-confirms topic)
            found = False
            for _ in range(30):
                try:
                    chip = page.locator("[data-starter-prompt]").first
                    if chip.count() > 0 and chip.is_visible():
                        chip.click()
                        found = True
                        break
                except Exception:
                    pass
                time.sleep(1)
            if not found:
                log("  ⚠️ 未找到着陆芯片，手动输入")
                type_and_send(page, "我想学习自动控制原理")
            log("  ✅ 主题已提交")
            time.sleep(5)

            # Wait for assessment stepper
            for _ in range(90):
                try:
                    if page.locator(".q-stepper-label").first.count() > 0:
                        break
                    if page.locator(".assessment-card").first.count() > 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            mark_phase(page, 1, "entry_topic", "入口与主题确认")
            log("  ✅ PHASE 1 完成: 测评题已生成")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: 测评作答 → 用户画像
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 2: 学前测评与用户画像")
            log("=" * 60)

            # Answer all assessment questions
            answer_stepper(page, "测评")
            wait_idle(page, timeout=60)
            mark_phase(page, 2, "assessment_profiling", "学前测评与用户画像")

            # Wait for profiling + plan generation
            log("  等待画像分析 + 学习路径生成...")
            wait_idle(page, timeout=300)
            time.sleep(3)
            mark_phase(page, 2, "assessment_profiling", "学前测评与用户画像")
            log("  ✅ PHASE 2 完成: 画像 + 学习路径已生成")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: 学习路径面板 + 初始节点
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 3: 学习路径生成与初始节点选择")
            log("=" * 60)

            # Open learning plan panel
            try:
                lp_btn = page.locator("button:has-text('学习路径')").first
                if lp_btn.count() > 0 and lp_btn.is_visible():
                    lp_btn.click()
                    time.sleep(1)
            except Exception:
                pass
            mark_phase(page, 3, "learning_plan", "学习路径与初始节点")
            log("  ✅ PHASE 3 完成: 路径面板 + 初始节点")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 4: Tutor 教学讲解
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 4: AI 教学讲解")
            log("=" * 60)

            # Wait for tutor content to appear (this happens automatically)
            log("  等待 AI 教学讲解...")
            for _ in range(120):
                try:
                    msgs = page.locator(".message.assistant").all()
                    if len(msgs) >= 2:
                        break
                except Exception:
                    pass
                time.sleep(2)
            wait_idle(page, timeout=60)
            mark_phase(page, 4, "tutor_teaching", "AI教学讲解")
            log("  ✅ PHASE 4 完成: AI 教学已生成")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 5: 课后停顿 → 临时追问
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 5: 课后停顿与临时追问")
            log("=" * 60)

            # Wait for post_lesson_choice card
            for _ in range(60):
                try:
                    if page.locator(".post-lesson-card").first.count() > 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            mark_phase(page, 5, "post_lesson_temporary", "课后停顿与临时追问")

            # Type a free-form stuck point (测试临时追问)
            log("  测试自由卡点表达...")
            type_and_send(page, "请再解释一下闭环控制和开环控制的区别")
            time.sleep(5)
            wait_idle(page, timeout=120)
            mark_phase(page, 5, "post_lesson_temporary", "课后停顿与临时追问")
            log("  ✅ PHASE 5 完成: 临时追问已测试")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 6: 客观题测试 → 评分 → 错题补救
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 6: 客观题测试与错题补救")
            log("=" * 60)

            # Go to test
            found = find_and_click(page, "我懂了，进入小测", timeout=30)
            if not found:
                type_and_send(page, "开始测试")
                time.sleep(3)
            wait_idle(page, timeout=120)

            # Wait for test questions
            for _ in range(90):
                try:
                    if page.locator(".obj-test-q").first.count() > 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            mark_phase(page, 6, "objective_test_remediation", "客观题测试与错题补救")

            # Answer objective test
            answer_objtest(page, "客观题")
            wait_idle(page, timeout=180)
            time.sleep(3)
            mark_phase(page, 6, "objective_test_remediation", "客观题测试与错题补救")

            # Handle remediation decision
            for btn in ["稍后复习，加入错题本", "稍后复习"]:
                if find_and_click(page, btn, timeout=15):
                    log(f"  选择: {btn}")
                    wait_idle(page, timeout=60)
                    break
            mark_phase(page, 6, "objective_test_remediation", "客观题测试与错题补救")
            log("  ✅ PHASE 6 完成: 客观题 + 评分 + 补救")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 7: 节点推进 → 继续/作业选择
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 7: 节点推进与学习决策")
            log("=" * 60)

            # Wait for continue/homework card
            for _ in range(60):
                try:
                    if page.locator("button:has-text('开始下一个节点')").first.count() > 0:
                        break
                    if page.locator("button:has-text('今天就到这里')").first.count() > 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            mark_phase(page, 7, "node_progression", "节点推进与学习决策")

            # Continue to next node
            found = find_and_click(page, "开始下一个节点", timeout=15)
            if found:
                log("  继续下一节点")
                wait_idle(page, timeout=120)
                time.sleep(3)
            mark_phase(page, 7, "node_progression", "节点推进与学习决策")
            log("  ✅ PHASE 7 完成: 节点推进")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 8: 作业生成 → 结业总结
            # ═══════════════════════════════════════════════════════════════
            log("=" * 60)
            log("PHASE 8: 作业生成与结业总结")
            log("=" * 60)

            # Try stop and get homework
            # First go through one more node cycle quickly
            for _ in range(60):
                try:
                    if page.locator("button:has-text('我懂了，进入小测')").first.count() > 0:
                        find_and_click(page, "我懂了，进入小测", timeout=10)
                except Exception:
                    pass
                time.sleep(1)

            # Try to end the session
            found = find_and_click(page, "今天就到这里", timeout=10)
            if not found:
                # Try API fallback
                tid = page.evaluate(
                    "()=>window.localStorage.getItem('ai_tutor_last_thread_id') || "
                    "window.app?.state?.currentThreadId || ''"
                )
                if tid:
                    import urllib.request
                    req = urllib.request.Request(
                        "http://127.0.0.1:8000/api/answer",
                        data=json.dumps(
                            {"thread_id": tid, "answer": "今天就到这里"}
                        ).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=30)
                    log("  API: 发送'今天就到这里'")
                    time.sleep(3)

            wait_idle(page, timeout=180)
            time.sleep(3)
            mark_phase(page, 8, "homework_completion", "作业与结业总结")

            # Check for completion wrap-up
            try:
                if page.locator("button:has-text('查看学习报告')").first.count() > 0:
                    find_and_click(page, "查看学习报告", timeout=10)
                    wait_idle(page, timeout=120)
                    time.sleep(2)
                    mark_phase(page, 8, "homework_completion", "作业与结业总结")
            except Exception:
                pass
            log("  ✅ PHASE 8 完成: 作业 + 结业总结")

            # ═══════════════════════════════════════════════════════════════
            #  Full page screenshot
            # ═══════════════════════════════════════════════════════════════
            page.screenshot(path=str(OUT_DIR / "fullpage_final.png"), full_page=True)
            log("  📸 完整页面截图已保存")

        except Exception as e:
            log(f"  ❌ 录制异常: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path=str(OUT_DIR / "error.png"))
            return False

        finally:
            time.sleep(2)
            context.close()
            browser.close()

    # Rename full video
    candidates = sorted(
        OUT_DIR.glob("*.webm"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        vf = candidates[0]
        if vf != FULL_VIDEO:
            vf.rename(FULL_VIDEO)
        size_mb = FULL_VIDEO.stat().st_size / 1024 / 1024
        log(f"\n✅ 完整视频: {FULL_VIDEO} ({size_mb:.1f}MB)")
        return True
    return False


def split_video_with_ffmpeg() -> dict[int, str]:
    """Split the full video into phase segments using ffmpeg."""
    if not FULL_VIDEO.exists():
        log("❌ 完整视频不存在，无法切分")
        return {}

    video_files: dict[int, str] = {}
    sorted_phases = sorted(phase_timestamps.items())

    for i, (num, (start_t, name, cn_name)) in enumerate(sorted_phases):
        # Determine end time
        if i + 1 < len(sorted_phases):
            end_t = sorted_phases[i + 1][1][0]
        else:
            # Last phase: use video duration
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(FULL_VIDEO),
                ],
                capture_output=True,
                text=True,
            )
            try:
                end_t = float(result.stdout.strip())
            except ValueError:
                end_t = start_t + 60

        duration = end_t - start_t
        if duration < 1:
            log(f"  ⚠️ Phase {num} duration too short ({duration:.1f}s), 跳过")
            continue

        out_file = OUT_DIR / f"phase{num:02d}_{name}.webm"
        log(f"  切分 Phase {num}: {start_t:.1f}s → {end_t:.1f}s (时长 {duration:.1f}s)")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start_t),
                "-i",
                str(FULL_VIDEO),
                "-t",
                str(duration),
                "-c",
                "copy",
                str(out_file),
            ],
            capture_output=True,
        )
        if out_file.exists():
            size_mb = out_file.stat().st_size / 1024 / 1024
            log(f"    ✅ {out_file.name} ({size_mb:.1f}MB)")
            video_files[num] = str(out_file)

    return video_files


def generate_phase_map(video_files: dict[int, str]):
    """Generate PHASE_VIDEOS.md mapping document."""
    phase_meta = [
        (1, "entry_topic", "入口与主题确认",
         "intake_router → greeter → topic_confirmer → assessment_generator",
         "着陆页 → 点击课程方向芯片 → 主题自动确认 → 测评题生成 (8维自评)"),
        (2, "assessment_profiling", "学前测评与用户画像",
         "assessment_dialog → user_profiler",
         "逐题作答8维自评配对题 → user_profiler计算难度等级+教学策略+概念差距"),
        (3, "learning_plan", "学习路径生成与初始节点选择",
         "learning_plan_generator → initial_node_selector",
         "基于画像生成多步学习路径 → 选择第一步第一个节点 (强制full_learning)"),
        (4, "tutor_teaching", "AI 教学讲解",
         "node_content_loader → tutor",
         "加载节点教学内容 (学习目标/必会点/误区/媒体证据) → AI生成650-1000字讲解"),
        (5, "post_lesson_temporary", "课后停顿与临时追问",
         "post_lesson_choice → temporary_question_collector → interruption_tutor",
         "课后停顿卡 → 自由输入卡点表达 → GraphRAG检索证据增强回答 → 回到停顿"),
        (6, "objective_test_remediation", "客观题测试与错题补救",
         "objective_test_generator → scorer → remediation_decision",
         "10道四选一客观题 (优先题库) → answer_key评分 → 错题讲解+变式题/稍后复习"),
        (7, "node_progression", "节点推进与学习决策",
         "next_node_planner → continue_or_homework_selector",
         "按Step推进节点 (plan_completed检测) → 继续下一节点/今天结束/新一轮/巩固薄弱/查看报告"),
        (8, "homework_completion", "作业生成与结业总结",
         "homework_generator → completion_wrapup",
         "从题库抽取作业 (3-tier fallback) → 全部节点掌握后LLM生成学习总结报告"),
    ]

    lines = [
        "# AI Tutor Agent 分阶段演示视频映射",
        f"",
        f"录制时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"完整视频: `00_full_flow.webm`",
        f"",
        f"## 完整流程概览 (14步)",
        f"",
        f"```",
        f"用户进入",
        f"  → [Phase 1] intake_router → greeter → topic_confirmer  (意图识别+主题确认)",
        f"  → [Phase 2] assessment_generator → assessment_dialog → user_profiler  (8维测评+画像)",
        f"  → [Phase 3] learning_plan_generator → initial_node_selector  (路径生成+初始节点)",
        f"  → [Phase 4] node_content_loader → tutor  (加载内容+AI讲解)",
        f"  → [Phase 5] post_lesson_choice → temporary_question → interruption_tutor  (停顿+追问)",
        f"  → [Phase 6] objective_test_generator → scorer → remediation_decision  (测试+补救)",
        f"  → [Phase 7] next_node_planner → continue_or_homework_selector  (推进+决策)",
        f"  → [多节点轮转: Phase 4-7 循环...]",
        f"  → [Phase 8] homework_generator → completion_wrapup  (作业+结业总结)",
        f"```",
    ]

    # Phase video table
    lines.extend([
        "",
        "## 阶段视频清单",
        "",
        "| 阶段 | 视频文件 | 流程节点 | 说明 |",
        "|------|---------|---------|------|",
    ])
    for num, name, cn_name, nodes, desc in phase_meta:
        vf = f"phase{num:02d}_{name}.webm"
        status = "✅" if num in video_files else "⚠️ (时长不足)"
        lines.append(f"| Phase {num}: {cn_name} | {status} `{vf}` | `{nodes}` | {desc} |")

    # Quick lookup table
    lines.extend([
        "",
        "## 快速查找：想看什么就看哪个视频",
        "",
        "| 你想了解... | 看这个视频 |",
        "|-----------|-----------|",
        "| 用户如何进入系统、确认学习主题 | Phase 1: `phase01_entry_topic.webm` |",
        "| 学前诊断怎么测、能力画像怎么生成 | Phase 2: `phase02_assessment_profiling.webm` |",
        "| 学习路径如何规划、第一个节点怎么选 | Phase 3: `phase03_learning_plan.webm` |",
        "| AI 老师如何讲解一个知识节点 | Phase 4: `phase04_tutor_teaching.webm` |",
        "| 学生如何自由提问、系统如何检索回答 | Phase 5: `phase05_post_lesson_temporary.webm` |",
        "| 客观题测试、自动评分、错题补救流程 | Phase 6: `phase06_objective_test_remediation.webm` |",
        "| 节点间如何推进、学习决策选项 | Phase 7: `phase07_node_progression.webm` |",
        "| 作业如何生成、结业总结报告 | Phase 8: `phase08_homework_completion.webm` |",
        "",
        "## 各阶段详细截图",
        "",
    ])
    for num, name, cn_name, nodes, desc in phase_meta:
        lines.append(f"### Phase {num}: {cn_name}")
        lines.append(f"- **视频**: `phase{num:02d}_{name}.webm`")
        lines.append(f"- **流程节点**: `{nodes}`")
        lines.append(f"- **说明**: {desc}")
        pngs = sorted(OUT_DIR.glob(f"phase{num:02d}_{name}*.png"))
        if not pngs:
            pngs = sorted(OUT_DIR.glob(f"phase{num:02d}*.png"))
        if pngs:
            lines.append(f"- **截图**: {', '.join(p.name for p in pngs)}")
        lines.append("")

    # Footer with auxiliary info
    lines.extend([
        "---",
        "",
        "## 辅助验证",
        "",
        f"- 全流程 API E2E 验证: `python scripts/real_e2e_verify.py`",
        f"- 全量单元测试: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`",
        f"- 完整 Playwright 录制 (原始): `python scripts/record_demo_flow.py`",
        "",
        f"## 技术参数",
        f"- 模型: deepseek-v4-flash",
        f"- 知识图谱: 42 节点 (KM001-KM042), 95 条边",
        f"- 题库: 420 客观题 + 210 变式题",
        f"- 流程节点: 29 个 LangGraph 节点",
    ])

    out_path = OUT_DIR / "PHASE_VIDEOS.md"
    out_path.write_text("\n".join(lines))
    log(f"  📄 映射文档: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="AI Tutor 完整流程分阶段录制 v2")
    parser.add_argument(
        "--headless",
        default="true",
        choices=["true", "false"],
        help="headless 模式",
    )
    parser.add_argument(
        "--no-split",
        action="store_true",
        help="不切分视频 (保留完整视频即可)",
    )
    args = parser.parse_args()

    # Verify service
    import urllib.request
    try:
        if (
            urllib.request.urlopen(f"{BASE}/api/health", timeout=5).status
            != 200
        ):
            print("❌ 服务未就绪")
            sys.exit(1)
    except Exception:
        print("❌ 服务未连接，请先启动: python main.py")
        sys.exit(1)

    headless = args.headless == "true"
    log(f"录制模式: {'headless' if headless else '可视化'}")
    log(f"完整视频: {FULL_VIDEO}")
    log(f"输出目录: {OUT_DIR}")

    # Record
    ok = record_full_flow(headless=headless)
    if not ok:
        print("❌ 录制失败")
        sys.exit(1)

    log(f"\n阶段时间戳:")
    for num in sorted(phase_timestamps):
        elapsed, name, cn_name = phase_timestamps[num]
        log(f"  Phase {num} ({cn_name}): t={elapsed:.1f}s")

    # Split video
    video_files = {}
    if not args.no_split:
        log(f"\n切分视频...")
        check = subprocess.run(["which", "ffmpeg"], capture_output=True)
        if check.returncode == 0:
            video_files = split_video_with_ffmpeg()
        else:
            log("  ⚠️ ffmpeg 未安装，跳过视频切分")
            # Generate manual split commands
            log("\n  手动切分命令:")
            sorted_phases = sorted(phase_timestamps.items())
            for i, (num, (start_t, name, cn_name)) in enumerate(sorted_phases):
                if i + 1 < len(sorted_phases):
                    end_t = sorted_phases[i + 1][1][0]
                else:
                    end_t = start_t + 60
                log(f"    ffmpeg -ss {start_t:.1f} -i 00_full_flow.webm -t {end_t-start_t:.1f}s -c copy phase{num:02d}_{name}.webm")
    else:
        log("  (跳过分割)")

    # Generate mapping document
    generate_phase_map(video_files)

    print(f"\n{'='*60}")
    print(f"📊 录制完成!")
    print(f"{'='*60}")
    print(f"输出目录: {OUT_DIR}")
    print(f"完整视频: {FULL_VIDEO}")
    print(f"阶段截图: {len(list(OUT_DIR.glob('phase*.png')))} 张")
    if video_files:
        print(f"阶段视频: {len(video_files)} 个")
        for num, vf in sorted(video_files.items()):
            cn = phase_timestamps.get(num, ("", "", ""))[2]
            print(f"  Phase {num} ({cn}): {Path(vf).name}")
    print(f"映射文档: {OUT_DIR / 'PHASE_VIDEOS.md'}")


if __name__ == "__main__":
    main()
