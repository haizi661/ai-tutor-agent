"""Completion Wrapup — 全知识图谱完成后的结业总结。

当全部节点 mastered 后,生成一份 LLM 驱动的学习总结报告:
- 学习概览(掌握节点数、覆盖领域、学习轮次)
- 能力评估(优势领域 + 薄弱环节)
- 下一步建议(实践应用 + 延伸学习 + 复习策略)

同时附带一份综合复习作业。
"""

from __future__ import annotations

from ..core.ability_mapper import get_all_node_ids, get_ability_names, get_node_name_map
from ..core.events import make_event
from ..core.learning_support import (
    assign_homework_items,
    build_homework_items,
    load_student_state_snapshot,
)
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.student_profile import ConceptMastery, StudentProfile
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text
from langchain_core.messages import HumanMessage, SystemMessage


def _rebuild_profile(concept_mastery_raw: dict) -> StudentProfile | None:
    """从 concept_mastery 字典重建 StudentProfile。"""
    if not concept_mastery_raw:
        return None
    profile = StudentProfile(profile_id="student")
    for nid, cm_dict in concept_mastery_raw.items():
        if isinstance(cm_dict, dict):
            profile.concept_mastery[nid] = ConceptMastery.from_dict(cm_dict)
    return profile


def build_completion_wrapup_node(llm, runtime: RuntimeContext):
    event_sink = runtime.event_sink
    graph_rag_pipeline = getattr(runtime, "graph_rag_pipeline", None)
    student_state_store = getattr(runtime, "student_state_store", None)

    def node(state: AgentState) -> dict:
        student_id = (
            str(state.get("student_id") or "default_student").strip()
            or "default_student"
        )
        _, loaded_snapshot = load_student_state_snapshot(
            student_state_store, student_id
        )
        state_snapshot = loaded_snapshot or dict(
            state.get("student_state_snapshot") or {}
        )
        concept_mastery_raw = state_snapshot.get("concept_mastery") or {}

        profile = _rebuild_profile(concept_mastery_raw)
        name_map = get_node_name_map()
        ability_names = get_ability_names()
        all_ids = get_all_node_ids()

        # ── 统计 ──
        total_nodes = len(all_ids)
        mastered_ids = profile.get_mastered_concept_ids() if profile else set()
        mastered_count = len(mastered_ids)
        mastered_pct = round(mastered_count / max(total_nodes, 1) * 100, 1)
        session_index = int(state_snapshot.get("session_index", 0))
        wrong_question_book = state_snapshot.get("wrong_question_book") or []
        visited_nodes = state_snapshot.get("visited_nodes") or []

        # 覆盖的能力领域
        covered_abilities: set[str] = set()
        for nid in mastered_ids:
            entry = profile.concept_mastery.get(nid) if profile else None
            if entry:
                from ..core.ability_mapper import get_node_primary_ability
                ab = get_node_primary_ability(nid)
                if ab:
                    covered_abilities.add(ab)
        ability_labels = [
            ability_names.get(ab, ab) for ab in sorted(covered_abilities)
        ]

        # Top/Bottom 5 节点
        sorted_nodes = sorted(
            concept_mastery_raw.items(),
            key=lambda kv: float((kv[1] or {}).get("mastery", 0)),
            reverse=True,
        )
        top_nodes = sorted_nodes[:5]
        bottom_nodes = sorted_nodes[-5:] if len(sorted_nodes) >= 5 else sorted_nodes

        def _node_label(nid: str, data: dict) -> str:
            name = name_map.get(nid, nid)
            m = round(float((data or {}).get("mastery", 0)) * 100)
            return f"{name}({m}%)"

        top_text = "\n".join(
            f"  - {_node_label(nid, data)}" for nid, data in top_nodes
        )
        bottom_text = "\n".join(
            f"  - {_node_label(nid, data)}" for nid, data in bottom_nodes
        )

        # 薄弱点
        weak_lines: list[str] = []
        for nid, data in sorted_nodes:
            d = data or {}
            risk = str(d.get("risk", ""))
            failures = int(d.get("failure_count", 0))
            mastery = float(d.get("mastery", 0))
            if risk == "high" or failures >= 2 or mastery < 0.5:
                name = name_map.get(nid, nid)
                weak_lines.append(
                    f"  - {name}: 掌握度{round(mastery*100)}%, "
                    f"失败{failures}次, 风险{risk}"
                )
        weak_text = "\n".join(weak_lines[:8]) if weak_lines else "无明显薄弱点"

        # ── 事件 ──
        event_sink.emit(
            make_event(
                "node.start",
                "completion_wrapup",
                message="全部知识点已掌握，我来为你生成一份学习总结报告。",
                data={
                    "mastered_count": mastered_count,
                    "total_nodes": total_nodes,
                    "mastered_pct": mastered_pct,
                },
            )
        )

        # ── LLM 生成总结报告 ──
        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在不是继续讲新内容，而是在全部知识点都已掌握后的结业总结阶段，
帮学生回顾整个学习旅程并给出未来建议。

输出要求：
1. 标题用"学习完成！你的知识图谱已全部点亮"或类似温暖有力的总结句
2. 第一部分：学习概览
   - 已掌握节点数/总节点数、掌握率
   - 覆盖的知识领域
   - 累计学习轮次
3. 第二部分：能力评估
   - 列出学生的优势领域（掌握度最高的2-3个方向）
   - 诚实指出仍需巩固的薄弱点，给出具体的强化动作
4. 第三部分：下一步建议
   - 实践应用建议（用所学知识能解决什么问题）
   - 延伸学习方向（相关进阶主题）
   - 复习策略（如何保持不遗忘）
5. 全文控制在 400-500 字，语气像老师给学生写结业评语，温暖但不煽情
6. 不要出题，不要展开新知识点"""
            )
        )

        ability_summary = "、".join(ability_labels) if ability_labels else "全部领域"
        human_msg = HumanMessage(
            content=(
                f"学生画像数据：\n"
                f"- 知识图谱总节点：{total_nodes} 个\n"
                f"- 已掌握节点：{mastered_count} 个（{mastered_pct}%）\n"
                f"- 覆盖领域：{ability_summary}\n"
                f"- 学习轮次：{session_index} 轮\n"
                f"- 访问过的节点：{len(visited_nodes)} 个\n"
                f"- 错题累计：{len(wrong_question_book)} 道\n"
                f"- 平均掌握度：{profile.summary().get('avg_mastery', 0) if profile else 0}\n"
                f"- 平均置信度：{profile.summary().get('avg_confidence', 0) if profile else 0}\n"
                f"\n掌握度最高的节点（top 5）：\n{top_text}\n"
                f"\n掌握度最低的节点（bottom 5）：\n{bottom_text}\n"
                f"\n薄弱点（高风险或多次出错）：\n{weak_text}\n"
                f"\n请输出结业总结报告。"
            )
        )

        full_text = ""
        for chunk in llm.stream([system_msg, human_msg]):
            text = content_to_text(chunk.content)
            full_text += text
            event_sink.emit(
                make_event("node.stream", "completion_wrapup", data={"text": text})
            )

        full_text = (full_text or "").strip()
        if not full_text:
            full_text = (
                "### 学习完成！\n\n"
                f"你已完成「自动控制原理」全部 {total_nodes} 个知识点的学习，"
                f"掌握率 {mastered_pct}%，覆盖 {ability_summary} 等领域。\n\n"
                "你已经具备扎实的自动控制理论基础，可以尝试解决实际工程问题。"
            )

        # ── 生成复习作业 ──
        homework_items = build_homework_items(
            graph_pipeline=graph_rag_pipeline,
            student_state_snapshot=state_snapshot,
            limit=5,
        )
        updated_snapshot = assign_homework_items(
            student_state_store,
            student_id=student_id,
            homework_items=homework_items,
        )
        if updated_snapshot:
            state_snapshot = updated_snapshot

        if homework_items:
            homework_lines = ["### 复习作业"]
            for index, item in enumerate(homework_items, start=1):
                homework_lines.append(f"{index}. {item.get('prompt')}")
            full_text = f"{full_text}\n\n" + "\n".join(homework_lines)

        event_sink.emit(
            make_event(
                "node.complete",
                "completion_wrapup",
                message="结业总结报告已生成。",
            )
        )

        return {
            "tutor_content": full_text,
            "tutor_citations": [],
            "tutor_evidence": [],
            "flow_status": "homework_assigned" if homework_items else "normal",
            "homework_items": homework_items,
            "homework_status": "assigned" if homework_items else "",
            "student_state_snapshot": state_snapshot,
            "learning_phase": "daily_wrapup",
            "learning_resume_reason": "full_graph_completed",
        }

    return node
