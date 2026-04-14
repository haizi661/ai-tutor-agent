"""Tests for ai_tutor_agent.core.graph_service."""

import pytest
from ai_tutor_agent.core.graph_service import GraphQueryService


# ── Fixtures ──

NODES = {
    "传递函数": {
        "prerequisites": ["系统结构框图", "信号流图"],
        "neighbors": ["经典环节的传递函数", "Nyquist图"],
        "difficulty": "medium",
        "target_mastery_level": "Apply",
    },
    "系统结构框图": {
        "prerequisites": ["传递函数基础"],
        "neighbors": ["信号流图"],
        "difficulty": "easy",
        "target_mastery_level": "Understand",
    },
    "信号流图": {
        "prerequisites": ["传递函数基础"],
        "neighbors": ["系统结构框图"],
        "difficulty": "medium",
        "target_mastery_level": "Apply",
    },
    "传递函数基础": {
        "prerequisites": [],
        "neighbors": ["系统结构框图", "信号流图"],
        "difficulty": "easy",
        "target_mastery_level": "Understand",
    },
    "经典环节的传递函数": {
        "prerequisites": ["传递函数"],
        "neighbors": ["Bode图"],
        "difficulty": "medium",
        "target_mastery_level": "Apply",
    },
    "Bode图": {
        "prerequisites": ["经典环节的传递函数"],
        "neighbors": [],
        "difficulty": "hard",
        "target_mastery_level": "Master",
    },
    "Nyquist图": {
        "prerequisites": ["传递函数"],
        "neighbors": [],
        "difficulty": "hard",
        "target_mastery_level": "Master",
    },
}


@pytest.fixture
def gqs():
    return GraphQueryService(NODES)


# ── Prerequisite chain ──

def test_prerequisite_chain_depth1(gqs):
    chain = gqs.find_prerequisite_chain("传递函数", max_depth=1)
    assert set(chain) == {"系统结构框图", "信号流图"}


def test_prerequisite_chain_depth2(gqs):
    chain = gqs.find_prerequisite_chain("传递函数", max_depth=2)
    assert "传递函数基础" in chain
    # depth-1 items should appear before depth-2
    for d1 in ("系统结构框图", "信号流图"):
        assert chain.index(d1) < chain.index("传递函数基础")


def test_prerequisite_chain_no_prereqs(gqs):
    chain = gqs.find_prerequisite_chain("传递函数基础")
    assert chain == []


# ── Successor path ──

def test_successor_path(gqs):
    # 传递函数基础 is a prerequisite of 系统结构框图 and 信号流图
    # Those are prerequisites of 传递函数
    path = gqs.find_successor_path("传递函数基础", max_depth=2)
    assert "系统结构框图" in path
    assert "信号流图" in path
    # depth-2: 传递函数 depends on 系统结构框图 / 信号流图
    assert "传递函数" in path


def test_successor_path_leaf(gqs):
    path = gqs.find_successor_path("Bode图")
    assert path == []


# ── Prerequisite gap detection ──

def test_detect_gaps_all_unstarted(gqs):
    user_kg = {}
    gaps = gqs.detect_prerequisite_gaps("传递函数", user_kg)
    titles = [g["title"] for g in gaps]
    assert "系统结构框图" in titles
    assert "信号流图" in titles
    for g in gaps:
        assert g["status"] == "not_started"


def test_detect_gaps_some_mastered(gqs):
    user_kg = {
        "系统结构框图": {"status": "mastered", "turn_count": 5},
        "信号流图": {"status": "assessed_low", "turn_count": 1},
        "传递函数基础": {"status": "mastered", "turn_count": 3},
    }
    gaps = gqs.detect_prerequisite_gaps("传递函数", user_kg)
    assert len(gaps) == 1
    assert gaps[0]["title"] == "信号流图"
    assert gaps[0]["status"] == "assessed_low"


def test_detect_gaps_all_mastered(gqs):
    user_kg = {
        "系统结构框图": {"status": "mastered", "turn_count": 5},
        "信号流图": {"status": "assessed_high", "turn_count": 4},
        "传递函数基础": {"status": "mastered", "turn_count": 3},
    }
    gaps = gqs.detect_prerequisite_gaps("传递函数", user_kg)
    assert gaps == []


def test_detect_gaps_depth2(gqs):
    user_kg = {
        "系统结构框图": {"status": "mastered", "turn_count": 5},
        "信号流图": {"status": "mastered", "turn_count": 4},
        # 传递函数基础 not in user_kg → not_started
    }
    gaps = gqs.detect_prerequisite_gaps("传递函数", user_kg, max_depth=2)
    assert len(gaps) == 1
    assert gaps[0]["title"] == "传递函数基础"
    assert gaps[0]["depth"] == 2


# ── Recommend review target ──

def test_recommend_review_target(gqs):
    user_kg = {"系统结构框图": {"status": "mastered", "turn_count": 5}}
    target = gqs.recommend_review_target("传递函数", user_kg)
    assert target == "信号流图"


def test_recommend_review_target_none(gqs):
    user_kg = {
        "系统结构框图": {"status": "mastered", "turn_count": 5},
        "信号流图": {"status": "mastered", "turn_count": 4},
        "传递函数基础": {"status": "mastered", "turn_count": 3},
    }
    assert gqs.recommend_review_target("传递函数", user_kg) is None


# ── Blind-spot detection ──

def test_detect_blind_spots(gqs):
    user_kg = {
        "传递函数": {"status": "mastered", "turn_count": 10},
    }
    spots = gqs.detect_blind_spots(user_kg, current_node="传递函数")
    # Neighbors of 传递函数 are 经典环节的传递函数 and Nyquist图
    titles = [s["title"] for s in spots]
    assert "经典环节的传递函数" in titles or "Nyquist图" in titles


def test_detect_blind_spots_empty_kg(gqs):
    spots = gqs.detect_blind_spots({})
    assert spots == []


def test_detect_blind_spots_excludes_mastered(gqs):
    user_kg = {
        "传递函数": {"status": "mastered", "turn_count": 10},
        "经典环节的传递函数": {"status": "mastered", "turn_count": 5},
        "Nyquist图": {"status": "mastered", "turn_count": 4},
    }
    spots = gqs.detect_blind_spots(user_kg, current_node="传递函数")
    # Both neighbors are mastered, plus neighbors of those
    mastered_titles = {s["title"] for s in spots}
    assert "经典环节的传递函数" not in mastered_titles
    assert "Nyquist图" not in mastered_titles


# ── Curriculum location ──

def test_locate_in_curriculum(gqs):
    loc = gqs.locate_in_curriculum("传递函数")
    assert loc["exists_in_graph"] is True
    assert "系统结构框图" in loc["prerequisites"]
    assert loc["difficulty"] == "medium"
    assert loc["target_mastery_level"] == "Apply"
    # successors: nodes that depend on 传递函数
    assert "经典环节的传递函数" in loc["successors"]


def test_locate_in_curriculum_nonexistent(gqs):
    loc = gqs.locate_in_curriculum("不存在的节点")
    assert loc["exists_in_graph"] is False
    assert loc["prerequisites"] == []
    assert loc["successors"] == []


# ── Format helpers ──

def test_format_prerequisite_gaps_hint_empty(gqs):
    assert gqs.format_prerequisite_gaps_hint([]) == ""


def test_format_prerequisite_gaps_hint_nonempty(gqs):
    gaps = [
        {"title": "信号流图", "status": "not_started", "turn_count": 0, "depth": 1},
    ]
    hint = gqs.format_prerequisite_gaps_hint(gaps, current_node="传递函数")
    assert "信号流图" in hint
    assert "前驱节点缺口" in hint
    assert "直接前置" in hint


def test_format_successor_path_hint(gqs):
    hint = gqs.format_successor_path_hint("传递函数基础", ["系统结构框图", "信号流图"])
    assert "学习路径定位" in hint
    assert "系统结构框图" in hint


def test_format_blind_spots_hint(gqs):
    spots = [{"title": "Bode图"}, {"title": "Nyquist图"}]
    hint = gqs.format_blind_spots_hint(spots)
    assert "盲区" in hint
    assert "Bode图" in hint


# ── Edge cases ──

def test_empty_graph():
    gqs = GraphQueryService({})
    assert gqs.find_prerequisite_chain("anything") == []
    assert gqs.find_successor_path("anything") == []
    assert gqs.detect_prerequisite_gaps("anything", {}) == []
    assert gqs.recommend_review_target("anything", {}) is None
    assert gqs.detect_blind_spots({}) == []


def test_node_with_none_prerequisites():
    nodes = {"A": {"prerequisites": None, "neighbors": None}}
    gqs = GraphQueryService(nodes)
    assert gqs.find_prerequisite_chain("A") == []
    assert gqs.detect_prerequisite_gaps("A", {}) == []
