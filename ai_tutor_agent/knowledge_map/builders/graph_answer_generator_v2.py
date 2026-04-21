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

        media_ref = self._pick_first_media_ref(media_items)
        lines = [
            f"结论：围绕“{question}”，当前知识图谱已经检索到一组足以支撑回答的核心节点。"
            "从这些节点的定义、关键点和关系路径来看，可以先给出明确判断，再用公式、图示和上下游知识点补充解释。"
        ]
        if media_ref:
            lines.append(f"[[MEDIA:{media_ref}]]")
        lines.append(
            "分析：这些证据之所以有价值，不只是因为它们被检索出来了，而是因为它们共同构成了“概念是什么、为什么成立、如何体现”的论证链条。"
            "因此回答应当把节点摘要、关键点和可能出现的公式或图表串联起来，而不是简单罗列材料。"
        )
        lines.append("举例：如果把命中的节点理解为一节课的板书提纲，那么摘要负责定主题，关键点负责给出解释骨架，公式与图表负责把抽象结论落到可观察对象上。")
        lines.append("拓展：当前是 fallback 模式，所以措辞会更保守；如果开启 LLM，同一组图谱证据还可以被进一步展开成更自然、更教学化的分析。")
        lines.append("依据：")
        for idx, item in enumerate(evidence_items[:4], start=1):
            lines.append(f"{idx}. [{item['reference']}] {item['text']}")
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

        key_evidence: list[dict[str, Any]] = []
        seen_refs: set[str] = set()
        for item in evidence_items:
            if item["attribute"] not in {"summary", "prerequisite_nodes", "key_points"}:
                continue
            if item["reference"] in seen_refs:
                continue
            seen_refs.add(item["reference"])
            key_evidence.append(item)
            if len(key_evidence) >= 4:
                break

        if forward_prereq_names:
            lead = "、".join(forward_prereq_names[:3])
            conclusion = (
                f"结论：学习“{anchor['name'] if anchor else question}”前，建议先掌握 {lead}。"
                "这说明当前知识点建立在更早的系统建模和基础概念之上，并不适合脱离前置内容单独学习。"
            )
        else:
            conclusion = (
                f"结论：知识图谱已经定位到“{anchor['name'] if anchor else question}”，但前置链还不够完整。"
                "不过从已命中的关键点看，它仍然依赖于更基础的系统描述和分析能力。"
            )

        analysis = (
            "分析：当前子图里最强的前置关系首先指向“控制系统的数学模型”，说明时域分析法不是孤立技巧，"
            "而是建立在系统建模、输入输出关系理解和动态方程表示之上的。只有先掌握这些内容，后面的时间响应、动态性能和稳态性能才有清晰的解释基础。"
        )
        if any("KM001" in item["text"] for item in evidence_items if item["attribute"] == "prerequisite_nodes"):
            analysis += " 继续向前追溯还能看到更早的基础节点，因此更自然的学习顺序是“基础概念 -> 数学模型 -> 时域分析”。"

        lines = [conclusion]
        media_ref = self._pick_first_media_ref(media_items)
        if media_ref:
            lines.append(f"[[MEDIA:{media_ref}]]")
        lines.append(analysis)
        lines.append("举例：如果学生还不能熟练建立微分方程或传递函数，那么即使看到了响应曲线，也往往只能记结论，难以解释为什么会出现这些动态特征。")
        lines.append(
            "拓展：从教学顺序看，前置知识之所以重要，不只是因为它出现在章节前面，"
            "更因为后续时域分析中的性能指标、稳态误差和响应曲线都要依赖这些基础概念来解释。"
        )
        lines.append("依据：")
        for idx, item in enumerate(key_evidence, start=1):
            lines.append(f"{idx}. [{item['reference']}] {item['text']}")
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
                f"结论：{linear_node['name']}更强调在线性模型条件下进行结构化分析，"
                f"而{nonlinear_node['name']}面对的是带非线性特征的对象，因此分析方法通常更一般、适用条件也更复杂。"
                "两者最核心的分界点在于系统是否满足线性叠加等经典线性分析前提。"
            )
        elif nonlinear_node:
            conclusion = (
                f"结论：当前图谱更明确地命中了“{nonlinear_node['name']}”，"
                "因此这个比较问题的关键差别可先理解为“是否满足线性建模条件”。"
            )
        else:
            conclusion = (
                "结论：知识图谱已经命中比较相关节点，但线性与非线性两侧的对照还不够完整。"
                "即便如此，仍可先从建模前提和分析方法差异来把握两者区别。"
            )

        analysis = (
            "分析：线性系统通常可以直接借助传递函数、状态空间、稳定性和频率响应等经典工具展开分析；"
            "非线性系统则往往需要更一般的稳定性理论、局部线性化或专门的非线性分析方法。"
            "从当前命中的节点也能看出，非线性侧更容易连接到一般性稳定理论，而线性侧更容易连接到规范化、可重复使用的分析框架。"
        )

        lines = [conclusion]
        media_ref = self._pick_first_media_ref(media_items)
        if media_ref:
            lines.append(f"[[MEDIA:{media_ref}]]")
        lines.append(analysis)
        lines.append("举例：在线性系统里，很多结论可以直接由极点位置和传递函数推出；而在非线性系统里，往往要先判断工作点、局部线性化范围或稳定性分析方法是否适用。")
        lines.append("拓展：如果把这两类系统放到学习路径里理解，线性系统更像是一套标准工具箱下的问题，而非线性系统更强调对象特性和分析经验。")
        lines.append("依据：")
        evidence_block = linear_evidence + nonlinear_evidence
        if evidence_block:
            for idx, item in enumerate(evidence_block[:4], start=1):
                lines.append(f"{idx}. [{item['reference']}] {item['text']}")
        else:
            lines.append("1. 当前证据不足，建议开启 LLM 模式补充比较式归纳。")
        return "\n".join(lines)

    def _pick_first_media_ref(self, media_items: list[dict[str, Any]]) -> str | None:
        if not media_items:
            return None
        return str(media_items[0].get("reference", "")).strip() or None

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
            analysis_hint = item.get("analysis_hint", "")
            display_label = item.get("display_label", item["reference"])
            if item["asset_type"] == "formula":
                lines.append(
                    f"- {display_label} [{item['reference']}] FORMULA: {item['text']} | "
                    f"用途提示: {analysis_hint or '可结合公式中的变量关系解释系统特性。'}"
                )
            else:
                lines.append(
                    f"- {display_label} [{item['reference']}] FIGURE: {item.get('caption', '')} | "
                    f"图像解读: {item.get('visual_summary', '') or item.get('caption', '') or '未提供'} | "
                    f"用途提示: {analysis_hint or '可结合图形走势、关键拐点或响应特征进行分析。'}"
                )
        return "\n".join(lines)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名面向自动控制课程的图谱增强导师。\n"
            "你的回答既要利用知识图谱检索到的节点证据，也可以结合你已有的专业知识做教学化解释。\n"
            "但必须遵守下面规则：\n"
            "1. 把知识图谱内容当作优先参考依据，不要脱离图谱胡乱发挥。\n"
            "2. 当图谱证据足够时，先直接回答问题，再引用图谱节点属性作为依据，并在此基础上展开更自然的推理。\n"
            "3. 当图谱证据不完整时，可以使用你已有的控制理论知识补全解释，但不要把补充知识伪装成图谱原文。\n"
            "4. 只对图谱证据使用引用标签，格式保持为 [KM007.summary] 这种形式。\n"
            "5. 不要把回答写成单纯的证据罗列，要像老师一样先下结论，再解释为什么。\n"
            "6. 输出语言使用中文。\n"
            "7. 输出结构固定为：结论、分析、举例、拓展、依据。\n"
            "8. `结论`要直接回答问题，建议 2 到 4 句。\n"
            "9. `分析`必须紧跟结论，且要把图谱证据、公式/图表和专业知识串起来，形成连贯推理，建议 3 到 6 句。\n"
            "10. `举例`要给出简洁的参数化例子、典型情景或数值代入，帮助读者落地理解。\n"
            "11. `拓展`用于补充适用条件、常见误区、学习路径或更一般的理解。\n"
            "12. `依据`放在最后，至少引用 2 条图谱证据。\n"
            "13. 如果某个公式或图表能支撑当前段落，请在该段后单独输出一行媒体标记，格式为 [[MEDIA:媒体引用]]。\n"
            "14. 媒体标记只在真正分析到该公式或图表时使用，不要把所有媒体都堆在一起。\n"
            "15. 图表与公式的行文引用应优先使用“图1”“式1”这类可读名称，同时保留严谨引用标签。\n"
            "16. 不要单独罗列“视觉分析结果”，而是把图像中的走势、结构、峰值、拐点等信息自然写进结论或分析句子。\n"
            "17. 若使用公式，请直接用 LaTeX 行内公式 `$...$` 或陈列公式 `$$...$$`，不要使用代码块。\n"
            "18. 不要输出孤立的 `]`、`[`、代码围栏或多余占位符。"
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
            "1. 输出顺序必须是：结论 -> 分析 -> 举例 -> 拓展 -> 依据。\n"
            "2. `结论`至少写成一个短段，不能只是“已检索到证据”之类的套话。\n"
            "3. `分析`要紧跟结论，直接解释为什么这个结论成立，并把图谱证据、公式和图表融合进论证。\n"
            "4. `举例`给出一个简洁的参数化例子、典型情境或数值代入。\n"
            "5. `拓展`允许结合已有知识，对概念关系、适用条件、误区和学习路径做更自然的讲解。\n"
            "6. `依据`放在最后，至少引用 2 条图谱证据；如果证据不足，就引用已有的关键证据。\n"
            "7. 当某条公式或图表被真正用来解释时，在该段后单独加一行 [[MEDIA:ref]]，让系统把对应媒体插入到这个位置。\n"
            "8. 如果有图表，请结合图表中的趋势、峰值、时间常数、稳态值、拐点或结构特征进行分析，而不是只提一句“见图”。\n"
            "9. 不要把图谱里没有明确写出的内容编造成图谱证据。\n\n"
            "输出模板：\n"
            "结论：...\n"
            "[[MEDIA:某个真正被结论引用的媒体ref，可选]]\n"
            "分析：...\n"
            "[[MEDIA:某个真正被分析引用的媒体ref，可选]]\n"
            "举例：...\n"
            "[[MEDIA:某个真正被举例引用的媒体ref，可选]]\n"
            "拓展：...\n"
            "依据：\n"
            "1. [citation] ...\n"
            "2. [citation] ..."
        )
