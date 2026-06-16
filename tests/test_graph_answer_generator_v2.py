from ai_tutor_agent.knowledge_map.builders.graph_answer_generator_v2 import GraphAnswerGeneratorV2


def test_graph_answer_generator_prompt_encourages_grounded_and_extended_answer():
    generator = GraphAnswerGeneratorV2(llm=None)

    system_prompt = generator._build_system_prompt()
    human_prompt = generator._build_human_prompt(
        question="学习线性系统的时域分析法之前要先学什么？",
        question_type="prerequisite_query",
        context_text="[Subgraph Nodes]\n- KM012 | 线性系统的时域分析法",
        media_items=[],
    )

    assert "知识图谱" in system_prompt
    assert "扩展解释" in system_prompt
    assert "先给出明确结论" in human_prompt
    assert "至少引用2条图谱证据" in human_prompt
    assert "结合你已有知识" in human_prompt
