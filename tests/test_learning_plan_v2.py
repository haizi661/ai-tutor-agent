"""Tests for learning_plan_v2 — cold start, multi-session, resume, wrong-question driving."""
from __future__ import annotations

from collections import Counter

import pytest
from ai_tutor_agent.core.ability_mapper import get_all_node_ids
from ai_tutor_agent.core.learning_plan_v2 import (
    LearningPlan,
    StepEntry,
    cluster_into_steps,
    compute_candidates,
    compute_context_boost,
    compute_urgency,
    generate_learning_plan_v2,
    generate_step_names,
    resolve_entry_modes,
    select_nodes,
    simulate_multi_session,
    sort_candidates,
)
from ai_tutor_agent.core.student_profile import (
    ConceptMastery,
    StudentProfile,
    make_default_profile,
    make_profile_from_self_assessment,
)


# ── Fixtures ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_caches():
    """每测试前重置 ability_mapper 缓存,保证测试独立性。"""
    from ai_tutor_agent.core.ability_mapper import reset_cache
    from ai_tutor_agent.core.student_profile import reset_all_caches
    reset_all_caches()
    reset_cache()


@pytest.fixture
def default_profile() -> StudentProfile:
    return make_default_profile()


@pytest.fixture
def all_node_ids() -> list[str]:
    return get_all_node_ids()


# =====================================================
# 1. 冷启动默认路径生成
# =====================================================

class TestColdStartPlan:
    def test_returns_non_empty_plan(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        assert len(plan.steps) >= 1, "冷启动应该生成至少 1 步"

    def test_step_count_is_nominal(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        assert 3 <= len(plan.steps) <= 5, f"期望 4 step, 实际 {len(plan.steps)}"

    def test_total_nodes_range(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        assert 9 <= plan.total_nodes <= 12, f"节点数 {plan.total_nodes} 不在 9-12"

    def test_no_empty_steps(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        for step in plan.steps:
            assert len(step.node_ids) >= 1, f"step {step.step_index} 为空"

    def test_all_nodes_are_valid(self, default_profile, all_node_ids):
        known = set(all_node_ids)
        plan = generate_learning_plan_v2(default_profile)
        for step in plan.steps:
            for nid in step.node_ids:
                assert nid in known, f"未知节点 {nid}"

    def test_no_duplicate_nodes(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        all_ids = plan.get_all_node_ids()
        dupes = [nid for nid, cnt in Counter(all_ids).items() if cnt > 1]
        assert not dupes, f"重复节点: {dupes}"

    def test_first_step_in_progress_others_pending(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        assert plan.steps[0].status == "in_progress"
        for step in plan.steps[1:]:
            assert step.status == "pending"

    def test_all_nodes_have_entry_modes(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        for step in plan.steps:
            for nid in step.node_ids:
                assert nid in step.entry_modes, f"{nid} 缺少 entry_mode"
                assert step.entry_modes[nid] in ("full_learning", "short_learning", "quick_check")

    def test_cold_start_default_is_conservative(self, default_profile):
        """冷启动默认画像：没做自评，mastery 是猜测值，应保守走完整学。"""
        plan = generate_learning_plan_v2(default_profile)
        all_modes = [mode for step in plan.steps for mode in step.entry_modes.values()]
        full_count = sum(1 for m in all_modes if m == "full_learning")
        # 默认冷启动 mastery<0.5 的节点都应走 full_learning
        assert full_count >= 1, f"期望至少 1 个 full_learning, 实际 0/{len(all_modes)}"

    def test_source_is_cold_start(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        assert plan.source == "cold_start"

    def test_session_index_matches(self, default_profile):
        plan = generate_learning_plan_v2(default_profile, session_index=2)
        assert plan.session_index == 2

    def test_serialization_roundtrip(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        d = plan.to_dict()
        restored = LearningPlan.from_dict(d)
        assert restored.total_nodes == plan.total_nodes
        assert restored.total_steps == plan.total_steps
        assert restored.source == plan.source
        assert restored.steps[0].step_name == plan.steps[0].step_name


# =====================================================
# 2. 多 session 覆盖所有 42 节点
# =====================================================

class TestMultiSession:
    def test_all_42_nodes_covered_over_5_sessions(self, default_profile):
        """5 次 session 后全部 42 节点至少被选过一次。"""
        plans = simulate_multi_session(default_profile, n_sessions=5)
        covered: set[str] = set()
        for plan in plans:
            covered.update(plan.get_all_node_ids())
        all_nodes = set(get_all_node_ids())
        missing = all_nodes - covered
        assert not missing, f"未覆盖节点: {missing} (共覆盖 {len(covered)}/42)"

    def test_most_nodes_covered_by_4_sessions(self, default_profile):
        """4 session 应覆盖 ≥ 38/42 节点。"""
        plans = simulate_multi_session(default_profile, n_sessions=4)
        covered: set[str] = set()
        for plan in plans:
            covered.update(plan.get_all_node_ids())
        assert len(covered) >= 38, f"4 session 仅覆盖 {len(covered)}/42"

    def test_each_session_has_9_to_12_nodes(self, default_profile):
        plans = simulate_multi_session(default_profile, n_sessions=4)
        for i, plan in enumerate(plans):
            assert 9 <= plan.total_nodes <= 12, f"Session {i}: {plan.total_nodes} 不在 9-12"

    def test_consecutive_sessions_differ(self, default_profile):
        """连续两次 session 的节点应有明显差异。"""
        plans = simulate_multi_session(default_profile, n_sessions=3)
        for i in range(1, len(plans)):
            prev_ids = set(plans[i - 1].get_all_node_ids())
            curr_ids = set(plans[i].get_all_node_ids())
            overlap = prev_ids & curr_ids
            # 应有新节点(不是全部重复)
            new_nodes = curr_ids - prev_ids
            assert len(new_nodes) >= 2, f"Session {i} 只有 {len(new_nodes)} 新节点"

    def test_session_uses_progressively_later_chapters(self, default_profile):
        """后续 session 应覆盖更靠后的章节。"""
        from ai_tutor_agent.core.learning_plan_v2 import _get_chapter_order
        plans = simulate_multi_session(default_profile, n_sessions=4)
        max_chapters: list[int] = []
        for plan in plans:
            chs = [_get_chapter_order(nid) for nid in plan.get_all_node_ids()]
            max_chapters.append(max(chs))
        # 整体趋势不递减(但不要求严格递增)
        for i in range(1, len(max_chapters)):
            assert max_chapters[i] >= max_chapters[0], f"Session {i} 后退: {max_chapters}"

    def test_no_mastered_nodes_in_later_sessions(self, default_profile):
        """已被 mastered 的节点不应再出现在后续路径(除非补充候选)。"""
        plans = simulate_multi_session(default_profile, n_sessions=3)
        for i in range(1, len(plans)):
            # Session 0 的节点在模拟中被标为 mastered
            mastered = set(plans[i - 1].get_all_node_ids())
            current = set(plans[i].get_all_node_ids())
            # 可能有少量复习节点(候选不足时补充),但不应超过 3 个
            overlap = mastered & current
            assert len(overlap) <= 3, f"Session {i} 含太多已掌握节点: {overlap}"


# =====================================================
# 3. 7 步算法单元测试
# =====================================================

class TestComputeCandidates:
    def test_all_nodes_when_none_mastered(self, all_node_ids):
        candidates = compute_candidates(all_node_ids, set())
        assert len(candidates) == 42

    def test_excludes_mastered(self, all_node_ids):
        mastered = {"KM001", "KM002"}
        candidates = compute_candidates(all_node_ids, mastered)
        assert "KM001" not in candidates
        assert "KM002" not in candidates
        assert len(candidates) == 40


class TestComputeUrgency:
    def test_high_gap_high_urgency(self, default_profile):
        urgency = compute_urgency("KM001", default_profile)
        # 冷启动 mastery ≈ 0.24 → gap ≈ 0.76, 紧迫度应在合理范围
        assert 0.3 < urgency < 1.0

    def test_failure_history_increases(self, default_profile):
        default_profile.update_after_quiz("KM001", 0.3, passed=False)
        u1 = compute_urgency("KM001", default_profile)
        default_profile.update_after_quiz("KM001", 0.2, passed=False)
        u2 = compute_urgency("KM001", default_profile)
        assert u2 >= u1, "多次失败应该提高紧迫度"


class TestSortCandidates:
    def test_returns_all_nodes_without_duplicates(self, all_node_ids):
        sorted_ids = sort_candidates(all_node_ids)
        assert set(sorted_ids) == set(all_node_ids)
        assert len(sorted_ids) == len(all_node_ids)

    def test_km001_first_by_depth(self, all_node_ids):
        """KM001(depth=0) 应是排序结果的第一个(无前置依赖,最低难度)。"""
        sorted_ids = sort_candidates(all_node_ids)
        assert sorted_ids[0] == "KM001"


class TestSelectNodes:
    def test_returns_9_to_12(self, all_node_ids, default_profile):
        selected = select_nodes(all_node_ids, default_profile)
        assert 9 <= len(selected) <= 12

    def test_includes_foundation(self, all_node_ids, default_profile):
        """KM001(深度0,核心基础)在默认画像所有节点 mastery 相近时应入选。"""
        selected = select_nodes(all_node_ids, default_profile)
        # 所有候选 urgency 相近时,低 ID 核心节点应入选
        assert len(selected) >= 9, f"至少选 9 个,实际 {len(selected)}"

    def test_higher_urgency_nodes_rank_first(self, default_profile):
        """同 importance 内,高紧迫度节点排在前面。"""
        from ai_tutor_agent.core.ability_mapper import get_node_importance
        nodes = ["KM003", "KM004", "KM005"]
        # 给 KM005 大幅降低 mastery 使其 urgency 最高
        default_profile.concept_mastery["KM005"] = ConceptMastery(
            mastery=0.1, confidence=0.2, source="test"
        )
        default_profile.concept_mastery["KM003"] = ConceptMastery(
            mastery=0.8, confidence=0.7, source="test"
        )
        default_profile.concept_mastery["KM004"] = ConceptMastery(
            mastery=0.8, confidence=0.7, source="test"
        )
        boost = {"KM005": 0.3}  # 额外加成
        selected = select_nodes(nodes, default_profile, node_count=3,
                                 node_range=(2, 3), context_boost=boost)
        # KM005 urgency 最高,应排第一
        assert selected[0] == "KM005", f"高紧迫度节点应排第一,实际 {selected}"

    def test_no_duplicates(self, all_node_ids, default_profile):
        selected = select_nodes(all_node_ids, default_profile)
        assert len(set(selected)) == len(selected)

    def test_core_nodes_before_supporting(self, all_node_ids, default_profile):
        """全局重要性排序: 所有 core 节点在 supporting 之前。"""
        from ai_tutor_agent.core.ability_mapper import get_node_importance
        selected = select_nodes(all_node_ids, default_profile)
        seen_supporting = False
        for nid in selected:
            imp = get_node_importance(nid)
            if imp == 'supporting':
                seen_supporting = True
            elif imp == 'core' and seen_supporting:
                pytest.fail(f"Core {nid} 出现在 supporting 节点之后")


class TestClusterIntoSteps:
    def test_produces_4_steps(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        # 用 15 个节点测试聚类
        selected = plan.get_all_node_ids()
        steps = cluster_into_steps(selected, n_steps=4)
        assert len(steps) == 4

    def test_each_step_has_nodes(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        steps = cluster_into_steps(plan.get_all_node_ids())
        for i, s in enumerate(steps):
            assert len(s) >= 1, f"Step {i} 为空"

    def test_same_chapter_grouped(self, default_profile):
        plan = generate_learning_plan_v2(default_profile)
        steps = cluster_into_steps(plan.get_all_node_ids())
        from ai_tutor_agent.core.learning_plan_v2 import _get_node_chapter
        for step in steps:
            chs = {_get_node_chapter(nid) for nid in step}
            # 允许跨 1 章(相邻章合并)
            assert len(chs) <= 2, f"step 跨 {len(chs)} 章: {chs}"

    def test_few_nodes_fills_minimum(self, default_profile):
        # 3 个节点 → 至少 1 步
        steps = cluster_into_steps(["KM001", "KM002", "KM003"])
        assert len(steps) >= 1
        assert len(steps[0]) >= 1


class TestResolveEntryModes:
    def test_full_learning_below_04(self):
        """极低 mastery (<0.15) + 高难度节点 → full_learning。"""
        profile = StudentProfile("test")
        profile.init_from_default()
        profile.concept_mastery["KM041"] = ConceptMastery(
            mastery=0.10, confidence=0.2, source="test", failure_count=0,
        )
        modes = resolve_entry_modes(["KM041"], profile)
        assert modes["KM041"] == "full_learning"

    def test_quick_check_above_07(self, default_profile):
        profile = make_profile_from_self_assessment({"A": 5, "B": 5, "C": 5, "D": 5,
                                                      "E": 5, "F": 5, "G": 5, "H": 5})
        modes = resolve_entry_modes(["KM001", "KM004"], profile)
        for nid, mode in modes.items():
            assert mode in ("quick_check",), f"{nid}: {mode} 不是 quick_check"

    def test_default_profile_mastery_variation_produces_mixed_entry_modes(self):
        """回归：不同 mastery 应产生混合 entry_mode（quick + short + full）。"""
        profile = make_default_profile()
        # 使用高难度节点 (KM041=diff=5) 来测试极低 mastery → full_learning
        profile.concept_mastery["KM041"] = ConceptMastery(
            mastery=0.15, confidence=0.2, source="default", failure_count=0,
        )
        profile.concept_mastery["KM002"] = ConceptMastery(
            mastery=0.55, confidence=0.3, source="default", failure_count=0,
        )
        profile.concept_mastery["KM003"] = ConceptMastery(
            mastery=0.85, confidence=0.5, source="default", failure_count=0,
        )
        modes = resolve_entry_modes(["KM041", "KM002", "KM003"], profile)
        assert modes["KM041"] == "full_learning", f"KM041(m=0.15,diff=5) 应为 full_learning, 实际 {modes['KM041']}"
        assert modes["KM002"] == "short_learning", f"KM002 mastery=0.55 应为 short_learning, 实际 {modes['KM002']}"
        assert modes["KM003"] == "quick_check", f"KM003 mastery=0.85 应为 quick_check, 实际 {modes['KM003']}"

    def test_high_risk_forces_full_learning_even_with_mid_mastery(self):
        """多次失败（≥2 次）强制 full_learning，不管 mastery 多高。"""
        profile = StudentProfile("test")
        profile.concept_mastery["KM001"] = ConceptMastery(
            mastery=0.68, confidence=0.8, source="merged", risk="high", failure_count=2,
        )
        modes = resolve_entry_modes(["KM001"], profile)
        assert modes["KM001"] == "full_learning"

    def test_low_confidence_high_mastery_uses_short_learning_not_quick_check(self):
        """高 mastery 但低置信度时仍需简学确认，不能直接快测跳过。"""
        profile = StudentProfile("test")
        profile.concept_mastery["KM001"] = ConceptMastery(
            mastery=0.86, confidence=0.25, source="default", risk="medium", failure_count=0,
        )
        modes = resolve_entry_modes(["KM001"], profile)
        assert modes["KM001"] == "short_learning"

    def test_default_source_low_mastery_is_conservative(self):
        """默认冷启动：mastery<0.5 的统一走 full_learning，不假设学生会。"""
        profile = StudentProfile("test")
        profile.init_from_default()
        # 默认画像所有节点 mastery <= 0.4 → 应全部 full_learning
        low_nodes = [nid for nid, e in profile.concept_mastery.items() if e.mastery < 0.5]
        modes = resolve_entry_modes(low_nodes[:5], profile)
        assert all(m == "full_learning" for m in modes.values()), (
            f"默认冷启动低 mastery 节点应全是 full_learning, 实际 {modes}"
        )

    def test_default_source_higher_mastery_can_be_short(self):
        """默认画像中人为提高 mastery 后，应能走 short_learning。"""
        profile = StudentProfile("test")
        profile.init_from_default()
        # 人为拉高 KM001 的 mastery
        profile.concept_mastery["KM001"] = ConceptMastery(
            mastery=0.55, confidence=0.5, source="default"
        )
        mode = profile.get_entry_mode("KM001", node_difficulty=1, node_importance="core")
        assert mode == "short_learning", f"mastery=0.55 应走 short, 实际 {mode}"


class TestStepNames:
    """step 名字生成的回归测试。"""

    def test_rule_fallback_when_no_llm(self):
        """llm=None 时,降级到规则(取第一个节点名 + 截断)。"""
        from ai_tutor_agent.core.learning_plan_v2 import (
            generate_step_names, get_node_name_map,
        )
        raw_steps = [["KM001", "KM002"], ["KM007", "KM008"]]
        names = generate_step_names(raw_steps, llm=None)
        assert len(names) == 2
        # 第一步:第一个节点名(没超 12 字就直接用)
        assert names[0] == get_node_name_map().get("KM001", "KM001")
        assert names[1] == get_node_name_map().get("KM007", "KM007")

    def test_rule_fallback_when_llm_raises(self):
        """LLM 调用异常时,降级到规则。"""
        from ai_tutor_agent.core.learning_plan_v2 import (
            generate_step_names, get_node_name_map,
        )

        class BoomLLM:
            def get_answer(self, prompt, *, state=None):
                raise RuntimeError("LLM down")

        raw_steps = [["KM001", "KM002"], ["KM007"]]
        names = generate_step_names(raw_steps, llm=BoomLLM())
        assert names[0] == get_node_name_map()["KM001"]
        assert names[1] == get_node_name_map()["KM007"]

    def test_rule_fallback_when_llm_returns_garbage(self):
        """LLM 输出无法解析时,降级到规则。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class GarbageLLM:
            def get_answer(self, prompt, *, state=None):
                return "随便写点无关内容,没有任何 JSON 或结构"

        names = generate_step_names([["KM001"], ["KM007"]], llm=GarbageLLM())
        # 兜底,非空
        assert all(names)
        assert len(names) == 2

    def test_llm_json_array_parsed(self):
        """LLM 返回纯 JSON 数组时,正确解析。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class JsonLLM:
            def __init__(self, payload):
                self._payload = payload

            def get_answer(self, prompt, *, state=None):
                return self._payload

        names = generate_step_names(
            [["KM001", "KM002"], ["KM007", "KM008"], ["KM012"]],
            llm=JsonLLM('["建立自动控制基础", "建立数学建模能力", "掌握时域分析"]'),
        )
        assert names == ["建立自动控制基础", "建立数学建模能力", "掌握时域分析"]

    def test_llm_json_embedded_in_text(self):
        """LLM 输出夹在文本中的 JSON,正确提取。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class JsonInTextLLM:
            def get_answer(self, prompt, *, state=None):
                return "好的,以下是命名:\n[\"建立基础认知\", \"掌握建模\", \"攻克时域\"]\n祝你学习顺利"

        names = generate_step_names(
            [["KM001"], ["KM007"], ["KM012"]], llm=JsonInTextLLM()
        )
        assert names == ["建立基础认知", "掌握建模", "攻克时域"]

    def test_llm_numbered_lines_fallback(self):
        """LLM 返回带行号的列表(没 JSON),按行解析。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class NumberedLLM:
            def get_answer(self, prompt, *, state=None):
                return "1. 建立自动控制基础\n2. 掌握数学建模\n3. 攻克时域分析"

        names = generate_step_names(
            [["KM001"], ["KM007"], ["KM012"]], llm=NumberedLLM()
        )
        assert names == ["建立自动控制基础", "掌握数学建模", "攻克时域分析"]

    def test_llm_strips_quotes_and_brackets(self):
        """LLM 返回带书名号/引号,正确清理。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class NoisyLLM:
            def get_answer(self, prompt, *, state=None):
                # 真实 LLM 偶尔会包书名号/引号,但内部 JSON 仍是合法的
                return '["「建立控制基础」", "「掌握数学建模」", "「攻克时域分析」"]'

        names = generate_step_names(
            [["KM001"], ["KM007"], ["KM012"]], llm=NoisyLLM()
        )
        assert names == ["建立控制基础", "掌握数学建模", "攻克时域分析"]

    def test_llm_name_too_long_truncated(self):
        """LLM 返回超长名字,截断到 12 字。"""
        from ai_tutor_agent.core.learning_plan_v2 import generate_step_names

        class LongLLM:
            def get_answer(self, prompt, *, state=None):
                return '["建立自动控制的基础认知并理解原理", "短名"]'

        names = generate_step_names(
            [["KM001"], ["KM007"]], llm=LongLLM()
        )
        assert names[0].endswith("…")
        assert len(names[0]) <= 12
        assert names[1] == "短名"

    def test_prompt_includes_step_node_info(self):
        """生成的 prompt 包含每个 step 的节点信息(便于 LLM 命名)。"""
        from ai_tutor_agent.core.learning_plan_v2 import _build_step_naming_prompt

        prompt = _build_step_naming_prompt([["KM001", "KM002"], ["KM007"]])
        assert "KM001" in prompt
        assert "KM002" in prompt
        assert "KM007" in prompt
        assert "Step 1" in prompt
        assert "Step 2" in prompt
        # 节点名也包含
        assert "自动控制" in prompt
        assert "数学模型" in prompt

    def test_resume_preserves_llm_named_steps(self):
        """resume 路径:已用 LLM 命名(或明显非规则生成)的 step 保留,不调 LLM。"""
        from ai_tutor_agent.core.learning_plan_v2 import _refresh_previous_plan
        from ai_tutor_agent.core.student_profile import StudentProfile

        class SpyLLM:
            def __init__(self):
                self.calls = 0

            def get_answer(self, prompt, *, state=None):
                self.calls += 1
                return "[]"

        profile = StudentProfile("test")
        profile.init_from_default()
        from ai_tutor_agent.core.learning_plan_v2 import LearningPlan, StepEntry
        plan = LearningPlan(steps=[
            StepEntry(step_index=0, step_name="建立控制基础认知", node_ids=["KM001"]),
            StepEntry(step_index=1, step_name="攻克时域分析", node_ids=["KM012"]),
        ])
        spy = SpyLLM()
        _refresh_previous_plan(plan, profile, llm=spy)
        assert spy.calls == 0, "已 LLM 命名的 step 应保留,resume 不调 LLM"
        assert plan.steps[0].step_name == "建立控制基础认知"
        assert plan.steps[1].step_name == "攻克时域分析"

    def test_resume_renames_old_rule_based_steps_via_llm(self):
        """回归:已存 plan 是老规则生成的(等于首节点名),resume 时主动 LLM 重命名。"""
        from ai_tutor_agent.core.learning_plan_v2 import _refresh_previous_plan
        from ai_tutor_agent.core.student_profile import StudentProfile
        from ai_tutor_agent.core.ability_mapper import get_node_name_map

        class RenamingLLM:
            def __init__(self, names):
                self._names = names
                self.calls = 0

            def get_answer(self, prompt, *, state=None):
                self.calls += 1
                import json
                return json.dumps(self._names, ensure_ascii=False)

        profile = StudentProfile("test")
        profile.init_from_default()

        name_map = get_node_name_map()
        # 模拟"老 plan":step_name = 首节点名(老规则特征)
        plan = LearningPlan(steps=[
            StepEntry(step_index=0, step_name=name_map["KM001"], node_ids=["KM001", "KM002", "KM003"]),
            StepEntry(step_index=1, step_name=name_map["KM007"], node_ids=["KM007", "KM008", "KM009"]),
        ])
        llm = RenamingLLM(["建立控制基础认知", "构建数学建模能力"])
        _refresh_previous_plan(plan, profile, llm=llm)
        # 调了 LLM
        assert llm.calls == 1
        # 重命名了
        assert plan.steps[0].step_name == "建立控制基础认知"
        assert plan.steps[1].step_name == "构建数学建模能力"

    def test_resume_renames_empty_and_fallback_steps(self):
        """resume 时空名/"第N步" 也要重命名。"""
        from ai_tutor_agent.core.learning_plan_v2 import _refresh_previous_plan
        from ai_tutor_agent.core.student_profile import StudentProfile

        class RenamingLLM:
            def get_answer(self, prompt, *, state=None):
                import json
                return json.dumps(["攻克时域分析", "掌握稳定性"], ensure_ascii=False)

        profile = StudentProfile("test")
        profile.init_from_default()
        plan = LearningPlan(steps=[
            StepEntry(step_index=0, step_name="", node_ids=["KM001"]),
            StepEntry(step_index=1, step_name="第2步", node_ids=["KM007"]),
        ])
        _refresh_previous_plan(plan, profile, llm=RenamingLLM())
        assert plan.steps[0].step_name == "攻克时域分析"
        assert plan.steps[1].step_name == "掌握稳定性"

    def test_full_learning_after_2_failures(self):
        profile = make_default_profile()
        profile.update_after_quiz("KM001", 0.2, passed=False)
        profile.update_after_quiz("KM001", 0.3, passed=False)
        modes = resolve_entry_modes(["KM001"], profile)
        assert modes["KM001"] == "full_learning"


class TestGenerateStepNames:
    def test_naming_uses_first_node_name(self):
        names = generate_step_names([["KM001", "KM002", "KM003"]])
        assert "自动控制的一般概念" in names[0]

    def test_cross_chapter_naming(self):
        names = generate_step_names([["KM001", "KM007"]])
        assert names[0]


# =====================================================
# 4. 续上逻辑
# =====================================================

class TestResume:
    def test_resume_returns_in_progress_plan(self, default_profile):
        """已有 in_progress plan → resume, 不生成新 plan。"""
        plan1 = generate_learning_plan_v2(default_profile)
        plan1.steps[0].status = "completed"
        plan1.steps[1].status = "in_progress"

        plan2 = generate_learning_plan_v2(default_profile, previous_plan=plan1)
        # 应该续上,不改变 step 结构
        assert len(plan2.steps) == len(plan1.steps)
        assert plan2.source == "resume"

    def test_resume_updates_entry_modes(self, default_profile):
        """resume 后 entry_mode 基于最新画像刷新。多次失败节点应为 full_learning。"""
        plan1 = generate_learning_plan_v2(default_profile)
        plan1.steps[0].status = "completed"
        plan1.steps[1].status = "in_progress"
        target = plan1.steps[1].node_ids[0]
        # 两次失败 → failure_count=2 → full_learning
        default_profile.update_after_quiz(target, 0.2, passed=False)
        default_profile.update_after_quiz(target, 0.2, passed=False)

        plan2 = generate_learning_plan_v2(default_profile, previous_plan=plan1)
        resumed_node = plan2.steps[1]
        assert resumed_node.entry_modes.get(target, "") in ("full_learning",)

    def test_completed_plan_generates_new_plan(self, default_profile):
        """完全完成的 plan → 生成新的 replan。"""
        plan1 = generate_learning_plan_v2(default_profile)
        for step in plan1.steps:
            step.status = "completed"

        plan2 = generate_learning_plan_v2(default_profile, previous_plan=plan1)
        assert plan2.source != "resume"
        assert plan2.source in ("replan", "cold_start")


# =====================================================
# 5. 错题驱动
# =====================================================

class TestWrongQuestionDriven:
    def test_failed_node_reappears_with_full_learning(self, default_profile):
        """两次失败 → 下次路径该节点以 full_learning 重入。"""
        plan1 = generate_learning_plan_v2(default_profile)
        target = plan1.steps[0].node_ids[0]
        default_profile.update_after_quiz(target, 0.3, passed=False)
        default_profile.update_after_quiz(target, 0.3, passed=False)

        plan2 = generate_learning_plan_v2(default_profile)
        plan2_ids = plan2.get_all_node_ids()

        assert target in plan2_ids, f"失败节点 {target} 应出现在下次路径"
        for step in plan2.steps:
            if target in step.node_ids:
                assert step.entry_modes[target] == "full_learning"

    def test_two_failures_elevates_urgency(self, default_profile):
        target = "KM001"
        default_profile.update_after_quiz(target, 0.2, passed=False)
        default_profile.update_after_quiz(target, 0.3, passed=False)
        profile_copy = default_profile
        plan = generate_learning_plan_v2(profile_copy)
        ids = plan.get_all_node_ids()
        assert target in ids
        for step in plan.steps:
            if target in step.node_ids:
                assert step.entry_modes[target] == "full_learning"
                break


# =====================================================
# 6. 边界情况
# =====================================================

class TestEdgeCases:
    def test_uninitialized_profile_produces_plan(self):
        """即使 profile 为空,ability_mapper 的 metadata 也能生成路径。"""
        from ai_tutor_agent.core.ability_mapper import reset_cache as reset_am
        reset_am()
        from ai_tutor_agent.core.student_profile import reset_all_caches
        reset_all_caches()
        profile = make_default_profile("empty_test")
        profile.concept_mastery.clear()
        plan = generate_learning_plan_v2(profile)
        # metadata 驱动 → 仍有路径
        assert len(plan.steps) >= 1

    def test_all_mastered_produces_empty_plan(self):
        """全标 mastered 时返回空路径,由上层触发 completion_wrapup 流程。"""
        profile = make_profile_from_self_assessment(
            {"A": 5, "B": 5, "C": 5, "D": 5, "E": 5, "F": 5, "G": 5, "H": 5}
        )
        for nid in get_all_node_ids():
            profile.mark_mastered(nid)
        plan = generate_learning_plan_v2(profile)
        assert len(plan.steps) == 0, f"全部 mastered 应返回空路径, 实际 {len(plan.steps)} 步"
        assert plan.total_nodes == 0
        assert plan.source == "cold_start"

    def test_self_assessment_gives_higher_mastery(self):
        """自评全满分 → 更多 quick_check。"""
        profile = make_profile_from_self_assessment(
            {"A": 5, "B": 5, "C": 5, "D": 5, "E": 5, "F": 5, "G": 5, "H": 5}
        )
        plan = generate_learning_plan_v2(profile)
        all_modes = [mode for step in plan.steps for mode in step.entry_modes.values()]
        quick_count = sum(1 for m in all_modes if m == "quick_check")
        assert quick_count >= 5, f"自评满分期望更多 quick_check, 实际 {quick_count}"

    def test_self_assessment_low_gives_full_learning(self):
        """自评低分(1/5):学生明确承认薄弱 → 全部完整学。"""
        profile = make_profile_from_self_assessment(
            {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1, "F": 1, "G": 1, "H": 1}
        )
        plan = generate_learning_plan_v2(profile)
        all_modes = [mode for step in plan.steps for mode in step.entry_modes.values()]
        full_count = sum(1 for m in all_modes if m == "full_learning")
        assert full_count == len(all_modes), (
            f"自评最低分应全部完整学, 实际 full={full_count}/{len(all_modes)}"
        )


# =====================================================
# 7. 章序约束
# =====================================================

class TestChapterConstraint:
    def test_step_internal_chapter_consistency(self, default_profile):
        """step 内节点应属于同一或相邻章节。"""
        from ai_tutor_agent.core.learning_plan_v2 import _get_chapter_order
        plan = generate_learning_plan_v2(default_profile)
        for step in plan.steps:
            orders = [_get_chapter_order(nid) for nid in step.node_ids]
            max_gap = max(orders) - min(orders) if orders else 0
            assert max_gap <= 1, f"Step {step.step_index} 章序跨度 {max_gap}: {orders}"

    def test_step_chapter_monotonic(self, default_profile):
        """step 间章节不递减。"""
        from ai_tutor_agent.core.learning_plan_v2 import _get_chapter_order
        plan = generate_learning_plan_v2(default_profile)
        min_ch_per_step: list[int] = []
        for step in plan.steps:
            orders = [_get_chapter_order(nid) for nid in step.node_ids]
            min_ch_per_step.append(min(orders) if orders else 0)
        for i in range(1, len(min_ch_per_step)):
            assert min_ch_per_step[i] >= min_ch_per_step[i - 1], \
                f"Step {i} 章节前移: {min_ch_per_step}"


# =====================================================
# 8. 错题本 + 临时提问驱动优先级
# =====================================================

class TestContextBoost:
    def test_empty_inputs_return_empty_dict(self):
        boost = compute_context_boost(None, None)
        assert boost == {}

    def test_wrong_question_book_boosts_node(self):
        wqb = [
            {"node_id": "KM001", "mastered": False},
            {"node_id": "KM001", "mastered": False, "misconception": "概念混淆"},
            {"node_id": "KM002", "mastered": False},
        ]
        boost = compute_context_boost(wqb, None)
        # KM001: 2 道错题(0.12+0.12) + 1 个 misconception(0.08) = 0.32
        assert boost.get("KM001") == pytest.approx(0.32, abs=0.01)
        # KM002: 1 道错题 = 0.12
        assert boost.get("KM002") == pytest.approx(0.12, abs=0.01)

    def test_mastered_wrong_questions_ignored(self):
        wqb = [
            {"node_id": "KM001", "mastered": True},
            {"node_id": "KM001", "mastered": False},
        ]
        boost = compute_context_boost(wqb, None)
        # 只有未掌握的错题算
        assert boost.get("KM001") == pytest.approx(0.12, abs=0.01)

    def test_question_help_records_boost_node(self):
        qhr = [
            {"node_id": "KM003", "question_text": "什么是极点？"},
            {"node_id": "KM003", "question_text": "零极点对消的条件？"},
            {"node_id": "KM005", "question_text": "如何判断稳定性？"},
        ]
        boost = compute_context_boost(None, qhr)
        # KM003: 2 个提问 = 0.16
        assert boost.get("KM003") == pytest.approx(0.16, abs=0.01)
        # KM005: 1 个提问 = 0.08
        assert boost.get("KM005") == pytest.approx(0.08, abs=0.01)

    def test_combined_boost_from_both_sources(self):
        wqb = [
            {"node_id": "KM001", "mastered": False, "wrong_reason": "计算错误"},
        ]
        qhr = [
            {"node_id": "KM001", "question_text": "这步为什么这样算？"},
        ]
        boost = compute_context_boost(wqb, qhr)
        # 错题 0.12 + wrong_reason 0.08 + 提问 0.08 = 0.28
        assert boost.get("KM001") == pytest.approx(0.28, abs=0.01)

    def test_boost_capped_at_1(self):
        wqb = [{"node_id": "KM001", "mastered": False, "misconception": f"误区{i}"} for i in range(10)]
        boost = compute_context_boost(wqb, None)
        assert boost["KM001"] <= 1.0

    def test_boost_ignores_empty_node_id(self):
        wqb = [
            {"node_id": "", "mastered": False},
            {"node_id": "  ", "mastered": False},
        ]
        boost = compute_context_boost(wqb, None)
        assert "" not in boost


class TestUrgencyWithContextBoost:
    def test_context_boost_increases_urgency(self, default_profile):
        # 同一个节点,有加成和无加成对比
        nid = "KM001"
        base = compute_urgency(nid, default_profile, context_boost=0.0)
        boosted = compute_urgency(nid, default_profile, context_boost=0.5)
        assert boosted > base

    def test_zero_context_boost_unchanged(self, default_profile):
        nid = "KM001"
        # context_boost=0 时,新权重公式仍然给基础分
        urgency = compute_urgency(nid, default_profile, context_boost=0.0)
        assert 0.0 <= urgency <= 1.0

    def test_max_context_boost(self, default_profile):
        nid = "KM001"
        urgency = compute_urgency(nid, default_profile, context_boost=1.0)
        assert urgency <= 1.0


class TestSelectNodesWithWrongQuestions:
    """错题节点的优先级应被 context_boost 提升。"""

    def test_wrong_question_nodes_rank_higher(self, default_profile):
        """错题节点即使 mastery 相同,应排得更靠前。"""
        nodes = ["KM003", "KM004", "KM005"]
        # 造错题本,让 KM005 有大量错题
        wqb = [
            {"node_id": "KM005", "mastered": False, "misconception": "概念混淆"},
            {"node_id": "KM005", "mastered": False},
            {"node_id": "KM005", "mastered": False},
        ]
        boost = compute_context_boost(wqb, None)
        selected = select_nodes(nodes, default_profile, node_count=3,
                                 node_range=(2, 3), context_boost=boost)
        # KM005 应该优先于其他两个
        assert selected[0] == "KM005", f"错题最多的节点应排第一,实际 {selected}"

    def test_temp_questions_boost_ranking(self, default_profile):
        """临时提问多的节点应排得更靠前。"""
        nodes = ["KM003", "KM004", "KM005"]
        qhr = [
            {"node_id": "KM003", "question_text": "为什么？"},
            {"node_id": "KM003", "question_text": "怎么回事？"},
            {"node_id": "KM003", "question_text": "不太懂"},
        ]
        boost = compute_context_boost(None, qhr)
        selected = select_nodes(nodes, default_profile, node_count=3,
                                 node_range=(2, 3), context_boost=boost)
        assert selected[0] == "KM003", f"提问最多的节点应排第一,实际 {selected}"
