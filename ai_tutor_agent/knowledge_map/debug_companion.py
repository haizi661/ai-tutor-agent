from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Optional

import chromadb
import pandas as pd

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore



class KnowledgeMapDebugger:
    def __init__(
        self,
        nodes_csv_path: str = "data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
        collection_name: str = "knowledge",
    ) -> None:
        self.settings = get_settings()
        self.nodes_csv_path = Path(nodes_csv_path)
        self.collection_name = collection_name

        if not self.nodes_csv_path.exists():
            raise FileNotFoundError(f"节点表不存在: {self.nodes_csv_path}")

        self.nodes = self._load_nodes()
        self.node_map = {node["node_id"]: node for node in self.nodes}
        self.name_map = {str(node.get("name", "")).strip(): node for node in self.nodes}

        self.state_store = StudentStateStore()
        self.student_state = self.state_store.load(self.settings.default_thread_id)

        self.collection = self._load_existing_collection()

    def _load_existing_collection(self):
        chroma_dir = Path(self.settings.chroma_dir)
        if not chroma_dir.exists():
            print(f"⚠️ 向量库目录不存在: {chroma_dir}")
            return None

        client = chromadb.PersistentClient(path=str(chroma_dir))

        try:
            collection = client.get_collection(self.collection_name)
            print(f"✅ 已连接现有向量库 collection: {self.collection_name}")
            return collection
        except Exception:
            print(f"⚠️ 未找到 collection: {self.collection_name}")
            return None

    def _load_nodes(self) -> list[dict[str, Any]]:
        df = pd.read_csv(self.nodes_csv_path)
        records = df.to_dict(orient="records")
        return [self._parse_record(r) for r in records]

    def _parse_record(self, record: dict[str, Any]) -> dict[str, Any]:
        parsed = dict(record)

        list_like_fields = [
            "tags",
            "core_concepts",
            "key_points",
            "formulas",
            "examples",
            "figures_refs",
            "page_refs",
            "definition_candidates",
            "key_point_candidates",
            "formula_candidates",
            "example_candidates",
            "prerequisite_nodes",
            "next_nodes",
            "related_nodes",
            "application_nodes",
            "recommended_next_nodes",
        ]

        for field in list_like_fields:
            parsed[field] = self._safe_parse_literal(parsed.get(field), default=[])

        parsed["extra"] = self._safe_parse_literal(parsed.get("extra"), default={})
        return parsed

    def _safe_parse_literal(self, value: Any, default: Any) -> Any:
        if isinstance(value, (list, dict)):
            return value

        if value is None:
            return default

        text = str(value).strip()
        if not text:
            return default

        try:
            return ast.literal_eval(text)
        except Exception:
            return default

    def run(self) -> None:
        print("=" * 100)
        print("伴学智能体统一调试台（只读现有图谱 + 现有向量库，不重跑 MinerU）")
        print("=" * 100)
        print(f"当前 student_id: {self.student_state.student_id}")
        self._print_help()

        while True:
            user_input = input("\n请输入命令: ").strip()
            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q"}:
                self.state_store.save(self.student_state)
                print("👋 已退出调试台。")
                break

            try:
                self._handle_command(user_input)
            except Exception as exc:
                print(f"❌ 执行失败: {exc}")

    def _print_help(self) -> None:
        print("命令列表：")
        print("  help")
        print("  ask 自动控制的基本原理是什么")
        print("  node 自动控制的基本原理与方式")
        print("  path 控制系统的数学模型")
        print("  prereq 线性系统的时域分析法")
        print("  next 控制系统的数学模型")
        print("  req 控制系统的数学模型")
        print("  formulas 控制系统的复数域数学模型")
        print("  examples 自动控制系统示例")
        print("  search 根轨迹")
        print("  student")
        print("  set_current KM007")
        print("  mark_visited KM007")
        print("  mark_wrong KM012")
        print("  mastery KM007 0.75")
        print("  recommend")
        print("  review")
        print("  exit")
        print("=" * 100)

    def _handle_command(self, user_input: str) -> None:
        if " " not in user_input:
            cmd = user_input.strip().lower()

            if cmd == "student":
                self._show_student_state()
                return
            if cmd == "recommend":
                self._recommend_for_student()
                return
            if cmd == "review":
                self._review_for_student()
                return
            if cmd == "help":
                self._print_help()
                return

            print("⚠️ 请输入“命令 + 内容”，例如：node 自动控制的基本原理与方式")
            return

        cmd, arg = user_input.split(" ", 1)
        cmd = cmd.strip().lower()
        arg = arg.strip()

        if cmd == "ask":
            self._handle_ask(arg)
        elif cmd == "node":
            self._show_node(arg)
        elif cmd == "path":
            self._show_path(arg)
        elif cmd == "prereq":
            self._show_prerequisites(arg)
        elif cmd == "next":
            self._show_next_nodes(arg)
        elif cmd == "req":
            self._show_requirement(arg)
        elif cmd == "formulas":
            self._show_formulas(arg)
        elif cmd == "examples":
            self._show_examples(arg)
        elif cmd == "search":
            self._search_nodes(arg)
        elif cmd == "set_current":
            self._set_current(arg)
        elif cmd == "mark_visited":
            self._mark_visited(arg)
        elif cmd == "mark_wrong":
            self._mark_wrong(arg)
        elif cmd == "mastery":
            self._set_mastery(arg)
        else:
            print(f"⚠️ 未知命令: {cmd}")

    def _handle_ask(self, question: str) -> None:
        self.student_state.last_question = question
        matched_node = self._match_node(question)

        print("\n" + "=" * 100)
        print(f"[问题] {question}")

        if matched_node:
            print(f"[匹配节点] {matched_node['node_id']} | {matched_node['name']}")
        else:
            print("[匹配节点] 未命中明确节点")

        if self.collection is not None:
            try:
                result = self.collection.query(
                    query_texts=[question],
                    n_results=3,
                )

                docs = result.get("documents", [[]])[0]
                metas = result.get("metadatas", [[]])[0]

                print(f"[检索命中] {len(docs)} 条")
                for idx, (doc, meta) in enumerate(zip(docs, metas), start=1):
                    meta = meta or {}
                    print(f"\n--- Hit {idx} ---")
                    print(f"block_type: {meta.get('block_type')}")
                    print(f"filename: {meta.get('filename')}")
                    print(f"chunk_id: {meta.get('chunk_id')}")
                    print(f"section: {meta.get('section')}")
                    print(f"content: {str(doc)[:500]}")
            except Exception as exc:
                print(f"⚠️ 向量检索失败: {exc}")
                print("⚠️ 已自动降级为只看知识图谱讲解。")

        if matched_node:
            print("\n[节点讲解]")
            print(matched_node.get("explanation_teacher_style", "") or "(空)")

            print("\n[课程要求]")
            self._print_requirement_block(matched_node)

            print("\n[前置知识]")
            self._print_node_name_list(matched_node.get("prerequisite_nodes", []))

            print("\n[后继知识]")
            self._print_node_name_list(matched_node.get("next_nodes", []))

            print("\n[推荐学习路径]")
            self._print_recommended_path(matched_node)

    def _show_node(self, node_name: str) -> None:
        node = self._require_node(node_name)

        print("\n" + "=" * 100)
        print(f"[节点] {node['node_id']} | {node['name']}")
        print(f"chapter: {node.get('chapter')}")
        print(f"level: {node.get('level')}")
        print(f"summary: {node.get('summary')}")
        print(f"page_refs_refined: {(node.get('extra') or {}).get('page_refs_refined', [])}")
        print(f"matched_block_title: {(node.get('extra') or {}).get('matched_block_title', '')}")
        print(f"retrieval_matched_block_title: {(node.get('extra') or {}).get('retrieval_matched_block_title', '')}")

        print("\n[课程要求]")
        self._print_requirement_block(node)

        print("\n[讲解]")
        print(node.get("explanation_teacher_style", "") or "(空)")

    def _show_path(self, node_name: str) -> None:
        node = self._require_node(node_name)

        print("\n" + "=" * 100)
        print(f"[学习路径] {node['name']}")

        print("\n前置知识：")
        self._print_node_name_list(node.get("prerequisite_nodes", []))

        print("\n后继知识：")
        self._print_node_name_list(node.get("next_nodes", []))

        print("\n推荐下一步：")
        self._print_recommended_path(node)

    def _show_prerequisites(self, node_name: str) -> None:
        node = self._require_node(node_name)
        print("\n" + "=" * 100)
        print(f"[前置知识] {node['name']}")
        self._print_node_name_list(node.get("prerequisite_nodes", []))

    def _show_next_nodes(self, node_name: str) -> None:
        node = self._require_node(node_name)
        print("\n" + "=" * 100)
        print(f"[后继知识] {node['name']}")
        self._print_node_name_list(node.get("next_nodes", []))

    def _show_requirement(self, node_name: str) -> None:
        node = self._require_node(node_name)
        print("\n" + "=" * 100)
        print(f"[课程要求] {node['name']}")
        self._print_requirement_block(node)

    def _show_formulas(self, node_name: str) -> None:
        node = self._require_node(node_name)

        print("\n" + "=" * 100)
        print(f"[公式候选] {node['name']}")

        print("\nformula_candidates:")
        items = node.get("formula_candidates", [])
        if not items:
            print("(空)")
        else:
            for idx, item in enumerate(items, start=1):
                print(f"{idx}. {item}")

        print("\nformulas:")
        items = node.get("formulas", [])
        if not items:
            print("(空)")
        else:
            for idx, item in enumerate(items, start=1):
                print(f"{idx}. {item}")

    def _show_examples(self, node_name: str) -> None:
        node = self._require_node(node_name)

        print("\n" + "=" * 100)
        print(f"[例子候选] {node['name']}")

        print("\nexample_candidates:")
        items = node.get("example_candidates", [])
        if not items:
            print("(空)")
        else:
            for idx, item in enumerate(items, start=1):
                print(f"{idx}. {item}")

        print("\nexamples:")
        items = node.get("examples", [])
        if not items:
            print("(空)")
        else:
            for idx, item in enumerate(items, start=1):
                print(f"{idx}. {item}")

    def _search_nodes(self, query: str) -> None:
        print("\n" + "=" * 100)
        print(f"[节点搜索] {query}")

        hits: list[tuple[int, dict[str, Any]]] = []
        q = query.strip()

        for node in self.nodes:
            score = self._score_node(q, node)
            if score > 0:
                hits.append((score, node))

        hits.sort(key=lambda x: (-x[0], x[1]["node_id"]))

        if not hits:
            print("未找到匹配节点。")
            return

        for score, node in hits[:10]:
            print(f"{node['node_id']} | {node['name']} | score={score}")

    def _show_student_state(self) -> None:
        print("\n" + "=" * 100)
        print("[学生状态]")
        print(f"student_id: {self.student_state.student_id}")
        print(f"current_node_id: {self.student_state.current_node_id}")
        print(f"last_question: {self.student_state.last_question}")
        print(f"visited_nodes: {self.student_state.visited_nodes}")
        print(f"wrong_nodes: {self.student_state.wrong_nodes}")
        print(f"recommended_queue: {self.student_state.recommended_queue}")
        print(f"mastery_scores: {self.student_state.mastery_scores}")

    def _set_current(self, arg: str) -> None:
        node = self._require_node(arg)
        self.student_state.current_node_id = node["node_id"]
        self.state_store.save(self.student_state)
        print(f"✅ 当前学习节点已设置为: {node['node_id']} | {node['name']}")

    def _mark_visited(self, arg: str) -> None:
        node = self._require_node(arg)
        if node["node_id"] not in self.student_state.visited_nodes:
            self.student_state.visited_nodes.append(node["node_id"])
        self.state_store.save(self.student_state)
        print(f"✅ 已标记学过: {node['node_id']} | {node['name']}")

    def _mark_wrong(self, arg: str) -> None:
        node = self._require_node(arg)
        if node["node_id"] not in self.student_state.wrong_nodes:
            self.student_state.wrong_nodes.append(node["node_id"])
        self.state_store.save(self.student_state)
        print(f"✅ 已标记薄弱点: {node['node_id']} | {node['name']}")

    def _set_mastery(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("⚠️ 用法: mastery KM007 0.75")
            return

        node_key, score_text = parts
        node = self._require_node(node_key)

        try:
            score = float(score_text)
        except ValueError:
            print("⚠️ 掌握度必须是数字，比如 0.75")
            return

        self.student_state.mastery_scores[node["node_id"]] = score
        self.state_store.save(self.student_state)
        print(f"✅ 已设置掌握度: {node['node_id']} | {node['name']} = {score:.2f}")

    def _recommend_for_student(self) -> None:
        print("\n" + "=" * 100)
        print("[个性化推荐]")

        current_id = self.student_state.current_node_id
        if not current_id or current_id not in self.node_map:
            print("⚠️ 还没有设置 current_node_id，请先用 set_current。")
            return

        current_node = self.node_map[current_id]
        recommended_ids = current_node.get("recommended_next_nodes", []) or []
        visited = set(self.student_state.visited_nodes)

        results = []

        for node_id in recommended_ids:
            target = self.node_map.get(node_id)
            if not target:
                continue

            if node_id in visited:
                continue

            threshold = float(target.get("mastery_threshold", 0.7) or 0.7)
            current_score = float(self.student_state.mastery_scores.get(node_id, 0.0))
            score_gap = threshold - current_score

            reason = "推荐学习路径中的下一步"
            if node_id in self.student_state.wrong_nodes:
                score_gap += 0.2
                reason = "该节点同时是你的薄弱点，建议优先补强"

            results.append((score_gap, node_id, reason))

        results.sort(key=lambda x: (-x[0], x[1]))

        if not results:
            print("当前没有新的推荐节点，可能推荐项都已学过。")
            self.student_state.recommended_queue = []
            self.state_store.save(self.student_state)
            return

        # ✅ 关键：这里必须定义
        queue = []

        for idx, (_, node_id, reason) in enumerate(results[:5], start=1):
            node = self.node_map[node_id]
            print(f"{idx}. {node_id} | {node['name']} | {reason}")
            queue.append(node_id)

        # ✅ 写回状态
        self.student_state.recommended_queue = queue
        self.state_store.save(self.student_state)

    def _review_for_student(self) -> None:
        print("\n" + "=" * 100)
        print("[个性化复习建议]")

        candidates: list[tuple[float, str, str]] = []

        for node_id in self.student_state.wrong_nodes:
            node = self.node_map.get(node_id)
            if not node:
                continue
            score = float(self.student_state.mastery_scores.get(node_id, 0.0))
            threshold = float(node.get("mastery_threshold", 0.7) or 0.7)
            priority = (threshold - score) + 0.5
            candidates.append((priority, node_id, "薄弱点优先复习"))

        for node_id in self.student_state.visited_nodes:
            if node_id in self.student_state.wrong_nodes:
                continue
            node = self.node_map.get(node_id)
            if not node:
                continue

            score = float(self.student_state.mastery_scores.get(node_id, 0.0))
            threshold = float(node.get("mastery_threshold", 0.7) or 0.7)

            if score < threshold:
                priority = threshold - score
                candidates.append((priority, node_id, "已学过但掌握度未达标"))

        candidates.sort(key=lambda x: (-x[0], x[1]))

        if not candidates:
            print("当前没有明显需要优先复习的节点。")
            return

        shown = set()
        rank = 1
        for _, node_id, reason in candidates:
            if node_id in shown:
                continue
            shown.add(node_id)
            node = self.node_map[node_id]
            print(f"{rank}. {node_id} | {node['name']} | {reason}")
            rank += 1
            if rank > 5:
                break

    def _match_node(self, text: str) -> Optional[dict[str, Any]]:
        q = text.strip()

        # 1. 优先按 node_id 直接查
        if q in self.node_map:
            return self.node_map[q]

        # 2. 再按完整名称精确查
        if q in self.name_map:
            return self.name_map[q]

        # 3. 最后走模糊匹配
        best_node = None
        best_score = -1

        for node in self.nodes:
            score = self._score_node(q, node)
            if score > best_score:
                best_score = score
                best_node = node

        if best_score <= 0:
            return None

        return best_node

    def _score_node(self, query: str, node: dict[str, Any]) -> int:
        score = 0

        name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []

        if name and name in query:
            score += 10

        tail = self._extract_tail_name(name)
        if tail and tail in query:
            score += 4

        for tag in tags:
            tag = str(tag).strip()
            if tag and tag in query:
                score += 2

        return score

    def _require_node(self, node_key: str) -> dict[str, Any]:
        node_key = node_key.strip()

        # 1. 先按 node_id 直接查
        if node_key in self.node_map:
            return self.node_map[node_key]

        # 2. 再按 name / 关键词匹配
        node = self._match_node(node_key)
        if node is None:
            raise ValueError(f"未找到节点: {node_key}")
        return node

    def _print_requirement_block(self, node: dict[str, Any]) -> None:
        print(f"requirement_level: {node.get('requirement_level')}")
        print(f"mastery_threshold: {node.get('mastery_threshold')}")
        print(f"importance_level: {node.get('importance_level')}")
        print(f"assessment_focus: {node.get('assessment_focus')}")

    def _print_node_name_list(self, node_ids: list[str]) -> None:
        if not node_ids:
            print("(空)")
            return

        for idx, node_id in enumerate(node_ids, start=1):
            node = self.node_map.get(node_id)
            if node:
                print(f"{idx}. {node_id} | {node.get('name')}")
            else:
                print(f"{idx}. {node_id}")

    def _print_recommended_path(self, node: dict[str, Any]) -> None:
        recommended_ids = node.get("recommended_next_nodes", []) or []
        reasons = (node.get("extra") or {}).get("recommended_next_reasons", []) or []

        if not recommended_ids:
            print("(空)")
            return

        for idx, node_id in enumerate(recommended_ids, start=1):
            target = self.node_map.get(node_id, {})
            target_name = target.get("name", node_id)

            reason_text = ""
            for item in reasons:
                if item.get("target") == node_id:
                    reason_text = item.get("reason", "")
                    break

            if reason_text:
                print(f"{idx}. {node_id} | {target_name} | {reason_text}")
            else:
                print(f"{idx}. {node_id} | {target_name}")

    def _extract_tail_name(self, text: str) -> str:
        if "的" in text:
            tail = text.split("的")[-1].strip()
            if len(tail) >= 2:
                return tail
        return ""


def main() -> None:
    debugger = KnowledgeMapDebugger()
    debugger.run()


if __name__ == "__main__":
    main()