from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ai_tutor_agent.core.text import content_to_text


class GraphAnswerGeneratorV2:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def generate(
        self,
        *,
        question: str,
        question_type: str,
        context_text: str,
        evidence_items: list[dict[str, Any]],
        node_summaries: list[dict[str, Any]],
        media_items: list[dict[str, Any]],
    ) -> str:
        if self.llm is None:
            return self._build_fallback_answer(question, question_type, evidence_items, node_summaries, media_items)

        system_msg = SystemMessage(content=self._build_system_prompt())
        human_msg = HumanMessage(
            content=self._build_human_prompt(
                question=question,
                question_type=question_type,
                context_text=context_text,
                media_items=media_items,
            )
        )
        try:
            response = self.llm.invoke([system_msg, human_msg])
            return content_to_text(response.content).strip()
        except Exception:
            return self._build_fallback_answer(question, question_type, evidence_items, node_summaries, media_items)

    def _build_fallback_answer(
        self,
        question: str,
        question_type: str,
        evidence_items: list[dict[str, Any]],
        node_summaries: list[dict[str, Any]],
        media_items: list[dict[str, Any]],
    ) -> str:
        if question_type == "prerequisite_query":
            return self._build_prerequisite_answer(question, evidence_items, node_summaries, media_items)
        if question_type == "comparative_query":
            return self._build_comparative_answer(question, evidence_items, node_summaries, media_items)

        lines = [f"结论：已根据知识图谱为“{question}”抽取到相关证据。", "依据："]
        for idx, item in enumerate(evidence_items[:4], start=1):
            lines.append(f"{idx}. [{item['reference']}] {item['text']}")
        lines.append("分析：这些证据覆盖了核心定义、关键点和关系路径，可作为后续教学解释的依据。")
        return "\n".join(lines)

    def _build_prerequisite_answer(
        self,
        question: str,
        evidence_items: list[dict[str, Any]],
        node_summaries: list[dict[str, Any]],
        media_items: list[dict[str, Any]],
    ) -> str:
        anchor = node_summaries[0] if node_summaries else None
        forward_prereqs = [
            item
            for item in node_summaries
            if item.get("via_relation") == "PRE_REQUIRES" and item.get("hop") == 1
        ]
        forward_prereq_names = [item["name"] for item in forward_prereqs]
        key_evidence = []
        seen_refs: set[str] = set()
        for item in evidence_items:
            if item["attribute"] in {"summary", "prerequisite_nodes", "key_points"} and item["reference"] not in seen_refs:
                seen_refs.add(item["reference"])
                key_evidence.append(item)
            if len(key_evidence) >= 4:
                break

        if forward_prereq_names:
            lead = "、".join(forward_prereq_names[:3])
            conclusion = f"结论：学习“{anchor['name'] if anchor else question}”前，建议先掌握 {lead}。"
        else:
            conclusion = f"结论：知识图谱中已经定位到“{anchor['name'] if anchor else question}”，但前置链还不够明确。"

        analysis = "分析：当前子图里最强的前置关系首先指向“控制系统的数学模型”，说明时域分析法建立在系统建模基础之上，而不是可以脱离建模单独学习的章节。"
        if any("KM001" in item["text"] for item in evidence_items if item["attribute"] == "prerequisite_nodes"):
            analysis += " 继续追溯还能看到更早的基础节点，因此更自然的学习顺序是“基础概念 -> 数学模型 -> 时域分析”。"

        lines = [conclusion, "依据："]
        for idx, item in enumerate(key_evidence, start=1):
            lines.append(f"{idx}. [{item['reference']}] {item['text']}")
        lines.append(analysis)
        return "\n".join(lines)

    def _build_comparative_answer(
        self,
        question: str,
        evidence_items: list[dict[str, Any]],
        node_summaries: list[dict[str, Any]],
        media_items: list[dict[str, Any]],
    ) -> str:
        linear_node = next(
            (item for item in node_summaries if "线性" in str(item.get("name", "")) and "非线性" not in str(item.get("name", ""))),
            None,
        )
        nonlinear_node = next(
            (item for item in node_summaries if "非线性" in str(item.get("name", ""))),
            None,
        )

        linear_evidence = self._pick_evidence_for_node(
            evidence_items,
            linear_node.get("node_id") if linear_node else None,
            preferred_attributes=["summary", "key_points"],
        )
        nonlinear_evidence = self._pick_evidence_for_node(
            evidence_items,
            nonlinear_node.get("node_id") if nonlinear_node else None,
            preferred_attributes=["summary", "key_points"],
        )

        if linear_node and nonlinear_node:
            conclusion = (
                f"结论：{linear_node['name']}更强调在线性模型条件下做结构化分析，"
                f"而{nonlinear_node['name']}面对的是带非线性特征的对象，分析方法通常更一般、适用条件也更复杂。"
            )
        elif nonlinear_node:
            conclusion = f"结论：当前图谱更明确地命中了“{nonlinear_node['name']}”，因此这个比较问题的核心区别可先理解为“是否满足线性建模条件”。"
        else:
            conclusion = f"结论：知识图谱已经命中比较相关节点，但线性与非线性两侧的对照还不够完整。"

        evidence_block = []
        for item in (linear_evidence + nonlinear_evidence)[:4]:
            evidence_block.append(f"{len(evidence_block)+1}. [{item['reference']}] {item['text']}")

        analysis = "分析：线性系统通常可以直接利用传递函数、状态空间、稳定性等经典线性工具展开分析；非线性系统则往往需要使用更一般的稳定性理论或专门的非线性分析方法，因此两者的建模前提、分析路径和处理难度都不同。"

        lines = [conclusion, "依据："]
        lines.extend(evidence_block if evidence_block else ["1. 当前证据不足，建议开启 LLM 模式补充比较式归纳。"])
        lines.append(analysis)
        return "\n".join(lines)

    def _pick_evidence_for_node(
        self,
        evidence_items: list[dict[str, Any]],
        node_id: str | None,
        preferred_attributes: list[str],
    ) -> list[dict[str, Any]]:
        if not node_id:
            return []
        results: list[dict[str, Any]] = []
        seen_refs: set[str] = set()
        for attribute in preferred_attributes:
            for item in evidence_items:
                if item["node_id"] != node_id:
                    continue
                if item["attribute"] != attribute:
                    continue
                if item["reference"] in seen_refs:
                    continue
                seen_refs.add(item["reference"])
                results.append(item)
                break
        return results

    def _render_media_text(self, media_items: list[dict[str, Any]]) -> str:
        if not media_items:
            return "None"
        lines: list[str] = []
        for item in media_items[:6]:
            if item["asset_type"] == "formula":
                lines.append(f"- [{item['reference']}] FORMULA: {item['text']}")
            else:
                lines.append(
                    f"- [{item['reference']}] FIGURE: {item.get('caption', '')} | "
                    f"paths={item.get('image_paths_abs', [])}"
                )
        return "\n".join(lines)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名面向自动控制课程的图谱增强导师。\n"
            "你的回答既要利用知识图谱检索到的节点证据，也可以结合你已有的专业知识做教学化解释。\n"
            "但必须遵守下面规则：\n"
            "1. 把知识图谱内容当作优先参考依据，不要脱离图谱胡乱发挥。\n"
            "2. 当图谱证据足够时，先直接回答问题，再引用图谱节点属性作为依据。\n"
            "3. 当图谱证据不完整时，可以使用你已有的控制理论知识补全解释，但要明确写成“扩展解释”或“进一步理解”，不要伪装成图谱原文。\n"
            "4. 只对图谱证据使用引用标签，格式保持为 [KM007.summary] 这种形式。\n"
            "5. 不要把回答写成单纯的证据罗列，要像老师一样先下结论，再解释为什么。\n"
            "6. 如果问题是学习路径、比较、原理分析、公式理解等，都要尽量给出结构化且有教学性的回答。\n"
            "7. 输出语言使用中文。\n"
            "8. 输出结构固定为：结论、依据、扩展解释、分析。若某部分确实没有内容，也要尽量简短补齐。"
        )

    def _build_human_prompt(
        self,
        *,
        question: str,
        question_type: str,
        context_text: str,
        media_items: list[dict[str, Any]],
    ) -> str:
        return (
            f"用户问题：{question}\n"
            f"问题类型：{question_type}\n\n"
            "下面是知识图谱检索到的参考内容，请优先基于这些内容作答：\n"
            f"{context_text}\n\n"
            "下面是补充媒体线索（如果有）：\n"
            f"{self._render_media_text(media_items)}\n\n"
            "请按下面要求输出：\n"
            "1. 先给出明确结论，不要只说“已检索到证据”。\n"
            "2. `依据`部分至少引用2条图谱证据；如果证据不足，就引用已有的关键证据。\n"
            "3. `扩展解释`部分允许结合你已有知识，对概念关系、学习顺序、原理差异、公式含义做更自然的讲解。\n"
            "4. `分析`部分总结图谱证据与扩展解释之间的关系，说明回答为什么成立。\n"
            "5. 图谱里没有明确写出的内容，不要编造成图谱证据。\n\n"
            "输出模板：\n"
            "结论：...\n"
            "依据：\n"
            "1. [citation] ...\n"
            "2. [citation] ...\n"
            "扩展解释：...\n"
            "分析：..."
        )
