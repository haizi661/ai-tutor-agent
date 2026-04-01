from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.tutor import build_tutor_node


class FakeStreamingLLM:
    def __init__(self, responses):
        if isinstance(responses, str):
            responses = [responses]
        self.responses = list(responses)
        self.messages = []

    def stream(self, messages):
        self.messages.append(messages)
        response = self.responses.pop(0)
        yield SimpleNamespace(content=response)


class StubKnowledgeProvider:
    def query(self, query):
        del query
        return ""


def test_tutor_formats_json_payload_into_stable_sections():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        """
        {
          "main_line": "先抓住稳定性判断的核心：看系统最终会不会回到平衡点。",
          "steps": [
            "先分清稳定性问的是最终趋势，不是中间抖不抖。",
            "再看系统受到扰动后，输出会不会慢慢回到原来的平衡附近。",
            "最后不要把稳定性和响应快慢混在一起。"
          ],
          "example": "比如温控系统被你突然打开窗户后，如果温度最后还能重新回到设定值附近，我们才说它稳定。",
          "key_points": [
            "稳定性看的是最终是否回到平衡。",
            "响应快慢和超调大小属于瞬态性能，不等于稳定性。"
          ],
          "self_check": "如果一个系统晃了几下但最后回到原位，你会怎么判断它是否稳定？"
        }
        """
    )
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    content = result["tutor_content"]
    assert "### 先抓主线" in content
    assert "### 再拆台阶" in content
    assert "### 代入一个例子" in content
    assert "### 💡 本次核心要点" in content
    streamed = "".join(event.data.get("text", "") for event in sink.events if event.type == "node.stream")
    assert streamed == content


def test_tutor_fallback_still_builds_stable_sections_from_plain_text():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM(
        "稳定性先看最终会不会回到平衡点。不要把它和瞬态性能混在一起。比如温控系统扰动后还能回到设定温度附近。核心要点：最终趋势比中间抖动更重要。"
    )
    node = build_tutor_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "控制理论中的稳定性",
            "difficulty_level": 3,
            "attempt_count": 0,
            "feedback": "",
            "assessment_radar": {},
        }
    )

    content = result["tutor_content"]
    assert content.startswith("### 先抓主线")
    assert "### 再拆台阶" in content
    assert "### 代入一个例子" in content
    assert "### 💡 本次核心要点" in content
