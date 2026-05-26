from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.initial_node_selector import build_initial_node_selector_node
from ai_tutor_agent.nodes.node_content_loader import build_node_content_loader_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "id": "KM001",
                "name": "稳定性基础",
                "core_concepts": ["稳定性的定义", "有界输入有界输出"],
                "key_points": ["判断系统响应是否收敛", "区分稳定与临界稳定"],
                "explanation_teacher_style": "【预置教师讲解】稳定性基础只讲这个字段中的内容。",
                "extra": {"common_errors": ["把振荡都当成不稳定"]},
                "recommended_next_nodes": ["KM002"],
                "related_nodes": ["KM003"],
                "prerequisite_nodes": [],
                "chapter": "自动控制原理-稳定性",
            },
            "KM002": {
                "node_id": "KM002",
                "id": "KM002",
                "name": "劳斯判据",
                "core_concepts": ["劳斯表", "首列符号"],
                "key_points": ["由特征方程判断稳定性"],
                "extra": {"common_errors": ["零首项处理错误"]},
                "recommended_next_nodes": [],
                "related_nodes": [],
                "prerequisite_nodes": ["KM001"],
                "chapter": "自动控制原理-稳定性",
            },
            "KM003": {
                "node_id": "KM003",
                "id": "KM003",
                "name": "根轨迹入门",
                "core_concepts": ["闭环极点轨迹"],
                "key_points": ["理解开环增益变化对闭环极点的影响"],
                "extra": {"common_errors": ["把开环零点当闭环极点"]},
                "recommended_next_nodes": [],
                "related_nodes": [],
                "prerequisite_nodes": ["KM001"],
                "chapter": "自动控制原理-根轨迹",
            },
        }
        self.queries = []

    def query(self, question, **kwargs):
        self.queries.append((question, kwargs))
        return {
            "answer": "稳定性描述系统受到扰动后响应是否能回到平衡或保持有界。",
            "evidence_items": [
                {
                    "node_id": "KM001",
                    "node_name": "稳定性基础",
                    "attribute": "definition",
                    "text": "若系统响应最终收敛或保持有界，则称系统稳定。",
                    "reference": "稳定性基础.definition",
                }
            ],
            "subgraph_roles": {
                "primary_nodes": [{"node_id": "KM001", "name": "稳定性基础", "reason": "当前主讲节点"}],
                "prerequisite_nodes": [],
                "supporting_nodes": [],
                "comparison_nodes": [],
            },
            "anchor_nodes": [{"node_id": "KM001", "name": "稳定性基础"}],
        }


def test_initial_node_selector_picks_first_unvisited_node_in_sequential_order():
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, graph_rag_pipeline=FakeGraphPipeline())
    node = build_initial_node_selector_node(runtime)

    result = node(
        {
            "current_topic": "自动控制原理",
            "student_state_snapshot": {"visited_nodes": []},
        }
    )

    assert result["current_node_id"] == "KM001"
    assert result["current_node_name"] == "稳定性基础"
    assert result["learning_phase"] == "node_selected"
    assert result["learning_resume_target"] == "node_content_loader"
    assert result["next_node_candidate_reason"] == "course_root_start"
    assert any(
        event.type == "graph.node_update"
        and event.data.get("type") == "current"
        and event.data.get("id") == "KM001"
        for event in sink.events
    )


def test_initial_node_selector_skips_visited_and_picks_next():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=FakeGraphPipeline())
    node = build_initial_node_selector_node(runtime)

    result = node(
        {
            "current_topic": "自动控制原理",
            "student_state_snapshot": {"visited_nodes": ["KM001"]},
        }
    )

    assert result["current_node_id"] == "KM002"
    assert result["current_node_name"] == "劳斯判据"
    assert result["learning_phase"] == "node_selected"
    assert result["learning_resume_target"] == "node_content_loader"
    assert result["next_node_candidate_reason"] == "smallest_unvisited"


def test_initial_node_selector_sorts_by_km_number_not_all_digits():
    class MixedPrefixGraphPipeline:
        def __init__(self):
            self.node_map = {
                "chapter_02_KM010": {"node_id": "chapter_02_KM010", "name": "第十节点", "prerequisite_nodes": ["KM001"]},
                "chapter_10_KM002": {"node_id": "chapter_10_KM002", "name": "第二节点", "prerequisite_nodes": ["KM001"]},
            }

    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=MixedPrefixGraphPipeline())
    node = build_initial_node_selector_node(runtime)

    result = node({"current_topic": "自动控制原理", "student_state_snapshot": {"visited_nodes": ["KM001"]}})

    assert result["current_node_id"] == "chapter_10_KM002"
    assert result["current_node_name"] == "第二节点"


def test_initial_node_selector_prefers_course_root_over_lower_numeric_non_root():
    class RootAwareGraphPipeline:
        def __init__(self):
            self.node_map = {
                "KM001": {
                    "node_id": "KM001",
                    "name": "非起点节点",
                    "prerequisite_nodes": ["KM010"],
                    "recommended_next_nodes": [],
                    "related_nodes": [],
                    "source_type": "skeleton_topic",
                },
                "KM010": {
                    "node_id": "KM010",
                    "name": "自动控制的一般概念",
                    "prerequisite_nodes": [],
                    "recommended_next_nodes": ["KM001"],
                    "related_nodes": [],
                    "source_type": "skeleton_chapter_anchor",
                },
            }

    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=RootAwareGraphPipeline())
    node = build_initial_node_selector_node(runtime)

    result = node({"current_topic": "自动控制原理", "student_state_snapshot": {"visited_nodes": []}})

    assert result["current_node_id"] == "KM010"
    assert result["current_node_name"] == "自动控制的一般概念"
    assert result["next_node_candidate_reason"] == "course_root_start"


def test_node_content_loader_uses_only_prebuilt_teacher_explanation_for_teaching_context():
    graph = FakeGraphPipeline()
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, graph_rag_pipeline=graph)
    node = build_node_content_loader_node(runtime)

    result = node({"current_topic": "自动控制原理", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert result["graph_anchor_id"] == "KM001"
    assert result["graph_anchor_title"] == "稳定性基础"
    assert "稳定性的定义" in result["graph_must_know"]
    assert "把振荡都当成不稳定" in result["graph_common_errors"]
    assert result["node_content_context"] == "【预置教师讲解】稳定性基础只讲这个字段中的内容。"
    assert "稳定性描述系统" not in result["node_content_context"]
    assert result["tutor_citations"] == []
    assert result["tutor_evidence"] == []
    assert result["learning_phase"] == "node_content_loaded"
    assert result["learning_resume_target"] == "tutor"
    assert not graph.queries
    assert any(
        event.type == "graph.node_update"
        and event.data.get("type") == "current"
        and event.data.get("status") == "content_loaded"
        for event in sink.events
    )


def test_node_content_loader_falls_back_to_structured_context_when_teacher_explanation_missing():
    class NoTeacherExplanationGraphPipeline(FakeGraphPipeline):
        def __init__(self):
            super().__init__()
            self.node_map["KM001"].pop("explanation_teacher_style", None)

    graph = NoTeacherExplanationGraphPipeline()
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=graph)
    node = build_node_content_loader_node(runtime)

    result = node({"current_topic": "自动控制原理", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert "当前图谱节点：稳定性基础（KM001）" in result["node_content_context"]
    assert "稳定性描述系统" not in result["node_content_context"]
    assert not graph.queries


def test_node_content_loader_handles_missing_graph_node_without_topic_name_error():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=FakeGraphPipeline())
    node = build_node_content_loader_node(runtime)

    result = node({"current_topic": "自动控制原理", "current_node_id": "KM999"})

    assert result["current_node_id"] == "KM999"
    assert result["turn_goal"] == "KM999"
    assert result["learning_resume_target"] == "tutor"


def test_node_content_loader_does_not_query_graph_rag_or_include_relation_path_text():
    class RawRelationGraphPipeline(FakeGraphPipeline):
        def query(self, question, **kwargs):
            self.queries.append((question, kwargs))
            return {
                "answer": "自动控制系统示例 --[parallel_to]--> 自动控制的基本原理与方式；方向：正向扩展；关系强度=0.70；边权重=0.70",
                "context_text": "自动控制的一般概念先抓系统组成、反馈作用和基本要求。",
                "evidence_items": [
                    {
                        "node_id": "KM001",
                        "node_name": "稳定性基础",
                        "attribute": "relation_path",
                        "text": "自动控制系统示例 --[parallel_to]--> 自动控制的基本原理与方式",
                        "reference": "path.1",
                    },
                ],
                "subgraph_roles": {},
                "anchor_nodes": [{"node_id": "KM001", "name": "稳定性基础"}],
            }

    graph = RawRelationGraphPipeline()
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=graph)
    node = build_node_content_loader_node(runtime)

    result = node({"current_topic": "自动控制原理", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert result["node_content_context"] == "【预置教师讲解】稳定性基础只讲这个字段中的内容。"
    assert "parallel_to" not in result["node_content_context"]
    assert "relation_path" not in result["node_content_context"]
    assert "自动控制的一般概念先抓系统组成" not in result["node_content_context"]
    assert result["tutor_evidence"] == []
    assert not graph.queries


def test_workflow_routes_profiler_to_initial_selector_then_loader():
    assert workflow_module.route_after_user_profiler({"current_node_id": "KM001"}) == "initial_node_selector"
    assert workflow_module.route_after_initial_node_selector({"current_node_id": "KM001"}) == "node_content_loader"
    assert workflow_module.route_after_node_content_loader({"node_content_context": "context"}) == "tutor"
