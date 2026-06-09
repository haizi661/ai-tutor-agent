"""教学洞察 (Teaching Insights) 功能测试
覆盖：数据聚合逻辑 + API 端点 + 端到端记录→读取链路
"""

from types import SimpleNamespace

from ai_tutor_agent.core.learning_support import record_teaching_episode
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api.teaching_insights import _aggregate_episodes
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore
from tests.asgi_test_client import SyncASGITestClient


# ── 聚合逻辑单元测试 ──

def test_aggregate_empty():
    result = _aggregate_episodes([])
    s = result["summary"]
    assert s["total_episodes"] == 0
    assert s["strategy_distribution"] == {}
    assert s["affect_distribution"] == {}
    assert s["entry_mode_distribution"] == {}
    assert s["total_nodes_visited"] == 0
    assert result["node_details"] == []
    assert result["recent_episodes"] == []


def test_aggregate_single_episode():
    episodes = [
        {
            "node_id": "KM001",
            "node_title": "闭环控制基本概念",
            "strategy": "stepbystep",
            "attempt_count": 1,
            "affect": "neutral",
            "entry_mode": "first_entry",
            "created_at": "2026-06-03T10:00:00",
        }
    ]
    result = _aggregate_episodes(episodes)
    s = result["summary"]
    assert s["total_episodes"] == 1
    assert s["strategy_distribution"] == {"stepbystep": 1}
    assert s["affect_distribution"] == {"neutral": 1}
    assert s["entry_mode_distribution"] == {"first_entry": 1}
    assert s["total_nodes_visited"] == 1

    assert len(result["node_details"]) == 1
    nd = result["node_details"][0]
    assert nd["node_id"] == "KM001"
    assert nd["node_title"] == "闭环控制基本概念"
    assert nd["total_visits"] == 1
    assert nd["attempt_count"] == 1
    assert nd["strategy_distribution"] == {"stepbystep": 1}
    assert nd["affect_distribution"] == {"neutral": 1}

    assert len(result["recent_episodes"]) == 1


def test_aggregate_multiple_episodes_across_nodes():
    episodes = [
        {"node_id": "KM001", "node_title": "闭环控制", "strategy": "stepbystep",
         "attempt_count": 1, "affect": "neutral", "entry_mode": "first_entry",
         "created_at": "2026-06-03T09:00:00"},
        {"node_id": "KM001", "node_title": "闭环控制", "strategy": "analogy",
         "attempt_count": 2, "affect": "confused", "entry_mode": "return",
         "created_at": "2026-06-03T09:30:00"},
        {"node_id": "KM002", "node_title": "传递函数", "strategy": "socratic",
         "attempt_count": 1, "affect": "curious", "entry_mode": "first_entry",
         "created_at": "2026-06-03T10:00:00"},
        {"node_id": "KM002", "node_title": "传递函数", "strategy": "summary",
         "attempt_count": 2, "affect": "", "entry_mode": "remediation",
         "created_at": "2026-06-03T10:30:00"},
    ]
    result = _aggregate_episodes(episodes)
    s = result["summary"]
    assert s["total_episodes"] == 4
    assert s["strategy_distribution"] == {
        "stepbystep": 1, "analogy": 1, "socratic": 1, "summary": 1,
    }
    assert s["affect_distribution"] == {"neutral": 1, "confused": 1, "curious": 1}
    assert s["entry_mode_distribution"] == {"first_entry": 2, "return": 1, "remediation": 1}
    assert s["total_nodes_visited"] == 2

    # 节点排序：按最近活动时间倒序 (KM002 最新)
    assert result["node_details"][0]["node_id"] == "KM002"
    assert result["node_details"][1]["node_id"] == "KM001"

    # KM001 聚合
    km001 = result["node_details"][1]
    assert km001["total_visits"] == 2
    assert km001["attempt_count"] == 2  # max
    assert km001["strategy_distribution"] == {"stepbystep": 1, "analogy": 1}
    assert km001["first_seen"] == "2026-06-03T09:00:00"
    assert km001["latest_seen"] == "2026-06-03T09:30:00"

    # 最近记录倒序
    recent = result["recent_episodes"]
    assert len(recent) == 4
    assert recent[0]["node_id"] == "KM002"  # 最新的在前


def test_aggregate_filters_empty_string_keys():
    """空字符串的 strategy/affect/entry_mode 应被过滤掉。"""
    episodes = [
        {"node_id": "KM001", "node_title": "测试", "strategy": "",
         "attempt_count": 1, "affect": "", "entry_mode": "",
         "created_at": "2026-06-03T10:00:00"},
    ]
    result = _aggregate_episodes(episodes)
    s = result["summary"]
    assert s["total_episodes"] == 1
    assert s["strategy_distribution"] == {}
    assert s["affect_distribution"] == {}
    assert s["entry_mode_distribution"] == {}


def test_aggregate_recent_capped_at_10():
    """超过 10 条时 recent_episodes 只保留最近 10 条。"""
    episodes = []
    for i in range(15):
        episodes.append({
            "node_id": f"KM{i:03d}", "node_title": f"节点{i}",
            "strategy": "stepbystep", "attempt_count": 1,
            "affect": "", "entry_mode": "",
            "created_at": f"2026-06-03T{i:02d}:00:00",
        })
    result = _aggregate_episodes(episodes)
    assert len(result["recent_episodes"]) == 10
    # 最新的在前 (KM014)
    assert result["recent_episodes"][0]["node_id"] == "KM014"


# ── API 端到端测试 ──

def _make_client(tmp_path):
    """构建同步测试客户端。"""
    store = StudentStateStore(tmp_path / "student_states")
    runtime = SimpleNamespace(
        student_state_store=store,
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    return SyncASGITestClient(app), runtime


def test_api_returns_empty_for_unknown_student(tmp_path):
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/nobody/teaching-insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_episodes"] == 0
    assert data["node_details"] == []
    assert data["recent_episodes"] == []


def test_api_returns_aggregated_data(tmp_path):
    """写入教学记录后，API 返回正确的聚合数据。"""
    store = StudentStateStore(tmp_path / "student_states")
    # 写入两条记录
    record_teaching_episode(
        store,
        student_id="s1",
        node_id="KM001",
        node_title="闭环控制",
        strategy="stepbystep",
        attempt_count=1,
        affect="neutral",
        entry_mode="first_entry",
    )
    record_teaching_episode(
        store,
        student_id="s1",
        node_id="KM001",
        node_title="闭环控制",
        strategy="analogy",
        attempt_count=2,
        affect="confused",
        entry_mode="return",
    )
    # 构建 client（复用同一 store 目录）
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/s1/teaching-insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_episodes"] == 2
    assert data["summary"]["total_nodes_visited"] == 1
    assert data["summary"]["strategy_distribution"] == {"stepbystep": 1, "analogy": 1}
    assert data["node_details"][0]["node_id"] == "KM001"
    assert data["node_details"][0]["total_visits"] == 2
    assert data["snapshot"]["current_node_id"] == ""


def test_api_record_and_read_roundtrip(tmp_path):
    """多次记录后 API 返回完整链路。"""
    store = StudentStateStore(tmp_path / "student_states")
    for i in range(3):
        record_teaching_episode(
            store, student_id="s2",
            node_id="KM010", node_title="根轨迹法",
            strategy=["stepbystep", "analogy", "summary"][i],
            attempt_count=i + 1,
            affect=["neutral", "curious", "confident"][i],
            entry_mode="first_entry",
        )

    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/s2/teaching-insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_episodes"] == 3
    assert data["summary"]["strategy_distribution"] == {
        "stepbystep": 1, "analogy": 1, "summary": 1,
    }
    assert data["summary"]["affect_distribution"] == {
        "neutral": 1, "curious": 1, "confident": 1,
    }
    nd = data["node_details"][0]
    assert nd["attempt_count"] == 3  # max
    assert nd["total_visits"] == 3
    assert len(data["recent_episodes"]) == 3
    # 时间戳相同时排序稳定，只验证所有 attempt_count 都在
    recent_counts = {ep["attempt_count"] for ep in data["recent_episodes"]}
    assert recent_counts == {1, 2, 3}


def test_record_teaching_episode_rejects_empty_node_id(tmp_path):
    """空 node_id 时不应该写入记录。"""
    store = StudentStateStore(tmp_path / "student_states")
    record_teaching_episode(
        store, student_id="s3", node_id="",
        strategy="stepbystep", attempt_count=1,
    )

    # 空 node_id 不会写入，加载也不应有 teaching_episodes
    state = store.load("s3")
    episodes = getattr(state, "teaching_episodes", [])
    assert episodes == []


def test_record_teaching_episode_survives_store_reload(tmp_path):
    """记录写入后重新加载不丢失。"""
    store = StudentStateStore(tmp_path / "student_states")
    record_teaching_episode(
        store, student_id="s4",
        node_id="KM020", node_title="频率响应",
        strategy="socratic", attempt_count=1,
        affect="curious", entry_mode="first_entry",
    )
    # 重新加载
    store2 = StudentStateStore(tmp_path / "student_states")
    state = store2.load("s4")
    episodes = getattr(state, "teaching_episodes", [])
    assert len(episodes) == 1
    assert episodes[0]["node_id"] == "KM020"
    assert episodes[0]["strategy"] == "socratic"


# ── 情绪检测测试 ──

from ai_tutor_agent.nodes.affect import detect_affect, primary_affect, _keyword_detect


def test_keyword_detect_empty():
    assert detect_affect("") == {}
    assert detect_affect("   ") == {}


def test_keyword_detect_confused():
    signals = detect_affect("我有点困惑，这里不太明白")
    assert "confused" in signals
    assert signals["confused"] > 0


def test_keyword_detect_confident():
    signals = detect_affect("我懂了，原来是这个意思")
    assert "confident" in signals
    assert signals["confident"] > 0


def test_keyword_detect_anxious():
    signals = detect_affect("怎么办，跟不上了，很焦虑")
    assert "anxious" in signals
    assert signals["anxious"] > 0


def test_keyword_label_mapping_frustrated_to_anxious():
    """旧 label 'frustrated' 应映射为 'anxious'。"""
    signals = detect_affect("完全不会，太难了，看不懂")
    assert "frustrated" not in signals  # 原始 label 不应出现
    assert "anxious" in signals


def test_keyword_label_mapping_curious_to_neutral():
    """旧 label 'curious' 应映射为 'neutral'。"""
    signals = detect_affect("为什么是这样，再讲讲")
    assert "curious" not in signals
    assert "neutral" in signals


def test_primary_affect():
    assert primary_affect({}) == ""
    assert primary_affect({"confused": 0.6, "confident": 0.3}) == "confused"
    assert primary_affect({"anxious": 0.8, "confused": 0.5}) == "anxious"


def test_keyword_detect_no_llm():
    """不传 llm 时应走关键词路径，返回统一 label 空间。"""
    signals = detect_affect("我明白了，没问题")
    assert "confident" in signals
    # 确认不会返回旧 label
    for old in ("frustrated", "curious", "passive"):
        assert old not in signals


# ── 日期筛选 API 测试 ──

def test_api_date_filter_future_start_returns_empty(tmp_path):
    """start 设为未来日期应返回空数据。"""
    store = StudentStateStore(tmp_path / "student_states")
    record_teaching_episode(
        store, student_id="s_date", node_id="KM001",
        strategy="stepbystep", attempt_count=1,
        affect="neutral", entry_mode="first_entry",
    )
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/s_date/teaching-insights?start=2099-01-01")
    assert resp.status_code == 200
    assert resp.json()["summary"]["total_episodes"] == 0


def test_api_date_filter_past_start_returns_data(tmp_path):
    """start 设为过去日期应返回全部数据。"""
    store = StudentStateStore(tmp_path / "student_states")
    record_teaching_episode(
        store, student_id="s_date2", node_id="KM002",
        strategy="analogy", attempt_count=1,
        affect="confident", entry_mode="first_entry",
    )
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/s_date2/teaching-insights?start=2020-01-01")
    assert resp.status_code == 200
    assert resp.json()["summary"]["total_episodes"] == 1


def test_api_date_filter_end_past_returns_empty(tmp_path):
    """end 设为过去日期应返回空。"""
    store = StudentStateStore(tmp_path / "student_states")
    record_teaching_episode(
        store, student_id="s_date3", node_id="KM003",
        strategy="summary", attempt_count=1,
        affect="neutral", entry_mode="first_entry",
    )
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.get("/api/students/s_date3/teaching-insights?end=2020-01-01")
    assert resp.status_code == 200
    assert resp.json()["summary"]["total_episodes"] == 0
