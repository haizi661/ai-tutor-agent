"""Workflow 拓扑一致性测试：自动化确保路由函数返回值与条件边定义同步。

核心检查：
  1. route_after_*() 函数中每个 return "xxx" 常量 → 对应 add_conditional_edges 的 dict key
  2. 通过 normalize_resume_target(target) + return target 的路径
     → 在独立测试中验证 target 集合都在边 dict 中
  3. 导入的路由函数（route_after_remediation_decision）→ 独立测试验证
"""

import ast

import pytest

from ai_tutor_agent.core.learning_flow import ROUTE_PAUSE, ROUTE_INTERRUPTION, ROUTE_COACH, ROUTE_FAIL, ROUTE_TARGETS
from ai_tutor_agent.nodes.remediation_decision import route_after_remediation_decision

WORKFLOW_PATH = "ai_tutor_agent/orchestration/workflow.py"
REMEDIATION_PATH = "ai_tutor_agent/nodes/remediation_decision.py"

# ── 需要额外校验 normalize_resume_target 返回路径的路由函数 ──
# 这些函数中通过 return target（而非 return "xxx" 常量）返回的目标值
# 需要在独立测试中逐一手动校验
ROUTES_WITH_NORMALIZE_TARGET = {
    "route_after_session_resume_router",
    "route_after_homework_review",
    "route_after_objective_test_scorer",
    "route_after_wrong_question_explainer",
    "route_after_variant_question_generator",
    "route_after_variant_test_answer_dialog",
    "route_after_homework_answer_dialog",
    "route_after_homework_scorer",
    "route_after_homework_explainer",
    "route_after_topic_confirmer",
    "route_after_assessment_generator",
}


# ── AST 解析工具 ──

def _parse_route_returns(tree: ast.AST) -> dict[str, set[str]]:
    """抽取 route_after_* 函数中 return "xxx" 常量 -> set[str]。
    只取直接的 return 常量，不追踪 normalize_resume_target 变量路径。
    """
    routes: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("route_after_"):
            consts: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Constant):
                    consts.add(sub.value.value)
            routes[node.name] = consts
    return routes


def _parse_edge_dict_keys(tree: ast.AST) -> dict[str, set[str]]:
    """抽取 add_conditional_edges 调用的 {key -> value} 中的 key 集合。
    返回 {source_node_name: set_of_keys}。
    """
    edges: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_conditional_edges"
                and len(node.args) >= 3):
            source = node.args[0]
            if not isinstance(source, ast.Constant):
                continue
            edge_dict = node.args[2]
            if not isinstance(edge_dict, ast.Dict):
                continue
            keys: set[str] = set()
            for k in edge_dict.keys:
                if isinstance(k, ast.Constant):
                    keys.add(k.value)
            edges[source.value] = keys
    return edges


def _extract_normalize_target_set(tree: ast.AST, func_name: str) -> set[str]:
    """抽取路由函数中 target in {...} 或 target == 'xxx' 时的目标字符串。
    只提取 target 来自 normalize_resume_target 返回值的比较。
    """
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            func_node = node
            break
    if func_node is None:
        return set()

    result: set[str] = set()

    # 找 target = normalize_resume_target(...) 这行
    target_var: str | None = None
    for sub in ast.walk(func_node):
        if (isinstance(sub, ast.Assign)
                and len(sub.targets) == 1
                and isinstance(sub.targets[0], ast.Name)
                and isinstance(sub.value, ast.Call)
                and isinstance(sub.value.func, ast.Name)
                and sub.value.func.id == "normalize_resume_target"):
            target_var = sub.targets[0].id
            break

    if target_var is not None:
        # 处理 if target in {"xxx", ...}
        for sub in ast.walk(func_node):
            if isinstance(sub, ast.If) and isinstance(sub.test, ast.Compare):
                left = sub.test.left
                op = sub.test.ops[0]
                right = sub.test.comparators[0]
                if (isinstance(left, ast.Name) and left.id == target_var
                        and isinstance(op, ast.In)
                        and isinstance(right, ast.Set)):
                    for elt in right.elts:
                        if isinstance(elt, ast.Constant):
                            result.add(elt.value)
                if (isinstance(left, ast.Name) and left.id == target_var
                        and isinstance(op, ast.Eq)
                        and isinstance(right, ast.Constant)):
                    result.add(right.value)

    # 处理 if normalize_resume_target(...) == "xxx"（无赋值，直接调用的模式）
    for sub in ast.walk(func_node):
        if (isinstance(sub, ast.If)
                and isinstance(sub.test, ast.Compare)
                and isinstance(sub.test.ops[0], ast.Eq)):
            left = sub.test.left
            right = sub.test.comparators[0]
            if (isinstance(left, ast.Call)
                    and isinstance(left.func, ast.Name)
                    and left.func.id == "normalize_resume_target"
                    and isinstance(right, ast.Constant)):
                result.add(right.value)

    return result


# ── 测试 ──

def test_direct_return_constants_have_edge_keys():
    """每个 route_after_*() 中 return "xxx" 常量都必须在边 dict 中有对应 key。
    本测试只覆盖直接 return "xxx" 的路径，不检查 normalize_resume_target 变量路径。
    """
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    route_returns = _parse_route_returns(tree)
    edge_dict_keys = _parse_edge_dict_keys(tree)

    # 构建 source_node_name -> route_fn_name
    source_to_route: dict[str, str] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_conditional_edges"
                and len(node.args) >= 2):
            source = node.args[0]
            route_fn = node.args[1]
            if isinstance(source, ast.Constant) and isinstance(route_fn, ast.Name):
                source_to_route[source.value] = route_fn.id

    errors: list[str] = []
    for source_node, route_fn_name in sorted(source_to_route.items()):
        if route_fn_name not in route_returns:
            continue
        expected_keys = route_returns[route_fn_name]
        actual_keys = edge_dict_keys.get(source_node, set())
        missing = expected_keys - actual_keys
        if missing:
            extra_info = ""
            if route_fn_name in ROUTES_WITH_NORMALIZE_TARGET:
                extra_info = " (该路由函数也使用 normalize_resume_target 变量返回)"
            errors.append(
                f"{source_node} ({route_fn_name}): "
                f"缺少边 key {sorted(missing)}{extra_info}。"
            )

    assert not errors, (
        f"路由函数中直接 return 的常量在边 dict 中缺少对应 key ({len(errors)} 处):\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_session_resume_router_normalize_targets():
    """route_after_session_resume_router 通过 return target 返回，
    target 来自 normalize_resume_target，且限定在 if target in {...} 集合内。
    集合中所有值都必须在边 dict 中。
    """
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    targets = _extract_normalize_target_set(tree, "route_after_session_resume_router")
    # 补上 fallback return "tutor"
    targets.add("tutor")

    edge_keys = _parse_edge_dict_keys(tree).get("session_resume_router", set())
    missing = targets - edge_keys
    assert not missing, (
        f"route_after_session_resume_router 的 normalize 返回集 {sorted(targets)} 中，"
        f"session_resume_router 边 dict 缺少 {sorted(missing)}"
    )


def test_homework_review_normalize_targets():
    """route_after_homework_review 也使用 return target + normalize_resume_target。"""
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    targets = _extract_normalize_target_set(tree, "route_after_homework_review")

    edge_keys = _parse_edge_dict_keys(tree).get("homework_review", set())
    missing = targets - edge_keys
    assert not missing, (
        f"route_after_homework_review 的 normalize 返回集 {sorted(targets)} 中，"
        f"homework_review 边 dict 缺少 {sorted(missing)}"
    )


def test_individual_normalize_targets():
    """验证其余通过 normalize_resume_target + return target 或 if target == 'x' 的路由。
    逐一检查每个函数的 target 值是否在边 dict 中。
    """
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    edge_keys = _parse_edge_dict_keys(tree)

    cases = [
        # (source_node, func_name, expected_targets)
        ("objective_test_scorer", "route_after_objective_test_scorer",
         {"wrong_question_explainer", "remediation_decision", "objective_test_generator", "next_node_planner"}),
        ("wrong_question_explainer", "route_after_wrong_question_explainer",
         {"remediation_decision", "variant_question_generator"}),
        ("variant_question_generator", "route_after_variant_question_generator",
         {"variant_test_answer_dialog"}),
        ("variant_test_answer_dialog", "route_after_variant_test_answer_dialog",
         {"objective_test_scorer"}),
        ("homework_answer_dialog", "route_after_homework_answer_dialog",
         {"homework_scorer"}),
        ("homework_scorer", "route_after_homework_scorer",
         {"homework_explainer"}),
        ("homework_explainer", "route_after_homework_explainer",
         {"session_resume_router"}),
        ("topic_confirmer", "route_after_topic_confirmer",
         {"learning_plan_generator", "initial_node_selector"}),
        ("assessment_generator", "route_after_assessment_generator",
         {"initial_node_selector"}),
    ]

    errors = []
    for source_node, func_name, expected in cases:
        actual = edge_keys.get(source_node, set())
        missing = expected - actual
        if missing:
            errors.append(f"{source_node} ({func_name}): 缺少 {sorted(missing)}")
    assert not errors, (
        "normalize_resume_target 返回的目标值缺失:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_remediation_decision_route_edges():
    """route_after_remediation_decision 是外部导入的路由函数。
    验证其 return 常量都在 remediation_decision 边 dict 中。
    """
    # 从 remediation_decision.py 抽取 return 常量
    with open(REMEDIATION_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    returns: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "route_after_remediation_decision":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Constant):
                    returns.add(sub.value.value)
            break

    assert returns, "未解析到 route_after_remediation_decision 的 return 常量"

    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    edge_keys = _parse_edge_dict_keys(tree).get("remediation_decision", set())
    missing = returns - edge_keys
    assert not missing, (
        f"route_after_remediation_decision 返回 {sorted(returns)}，"
        f"但 remediation_decision 边 dict 缺少 {sorted(missing)}"
    )


def test_all_route_return_values_are_in_route_targets():
    """route_after_*() 中每个 return "xxx" 都必须在 ROUTE_TARGETS 中。"""
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    route_returns = _parse_route_returns(tree)

    bad: list[str] = []
    for fn_name, returns in sorted(route_returns.items()):
        for val in returns:
            if val not in ROUTE_TARGETS:
                bad.append(f"{fn_name} 返回 '{val}' 不在 ROUTE_TARGETS 中")

    assert not bad, (
        f"路由函数返回了 ROUTE_TARGETS 之外的值 ({len(bad)} 处):\n"
        + "\n".join(f"  - {b}" for b in bad)
    )


def test_all_edge_keys_are_in_route_targets():
    """add_conditional_edges 的每个 dict key 都必须在 ROUTE_TARGETS 中。"""
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    edge_dict_keys = _parse_edge_dict_keys(tree)

    bad: list[str] = []
    for source_node, keys in sorted(edge_dict_keys.items()):
        for key in keys:
            if key not in ROUTE_TARGETS:
                bad.append(f"{source_node} 的边 dict key '{key}' 不在 ROUTE_TARGETS 中")

    assert not bad, (
        f"边 dict key 存在 ROUTE_TARGETS 之外的值 ({len(bad)} 处):\n"
        + "\n".join(f"  - {b}" for b in bad)
    )


def test_no_dead_edge_keys():
    """边 dict 中没有不被路由函数返回的冗余 key。
    注意：通过 normalize_resume_target(target) 变量返回的 target 已在 route_returns 覆盖。
    这里检查的是：edge dict key → route const returns ∪ normalize target set。
    """
    with open(WORKFLOW_PATH) as f:
        source = f.read()
    tree = ast.parse(source)

    route_const_returns = _parse_route_returns(tree)
    edge_dict_keys = _parse_edge_dict_keys(tree)

    # source_node -> route_fn_name
    source_to_route: dict[str, str] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_conditional_edges"
                and len(node.args) >= 2):
            source = node.args[0]
            route_fn = node.args[1]
            if isinstance(source, ast.Constant) and isinstance(route_fn, ast.Name):
                source_to_route[source.value] = route_fn.id

    # remediation_decision 的路由函数是外部导入的，单独处理
    source_to_route.pop("remediation_decision", None)

    errors: list[str] = []
    for source_node, route_fn_name in sorted(source_to_route.items()):
        if route_fn_name not in route_const_returns:
            continue
        const_returns = route_const_returns[route_fn_name]
        normalize_targets = _extract_normalize_target_set(tree, route_fn_name)

        all_valid_returns: set[str] = const_returns | normalize_targets
        edge_keys = edge_dict_keys.get(source_node, set())

        dead = edge_keys - all_valid_returns
        if dead:
            errors.append(
                f"{source_node} ({route_fn_name}): "
                f"死键 {sorted(dead)}。"
                f" 路由可返回={sorted(all_valid_returns)}, 边 dict key={sorted(edge_keys)}"
            )

    assert not errors, (
        f"边 dict 包含不被路由函数返回的死键 ({len(errors)} 处):\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
