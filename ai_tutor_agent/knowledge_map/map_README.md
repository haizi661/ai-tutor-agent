# knowledge_map + companion 模块 README（历史参考）

> 2026-04-30 状态：本文记录 `knowledge_map` 模块早期 2.0 设计。当前主教学图谱是 2026-04-27 Graph B 运行资产，权威运行说明请看 `AGENTS.md`、`docs/current-status-and-usage.md` 和 `docs/knowledge-map-runtime-assets.md`。

## 1. 模块目标

本模块用于构建自动控制原理知识图谱 + 伴学智能体原型系统，实现：

- 知识结构化（教材 → 图谱）
- 检索增强生成（RAG）
- 学生建模与学习路径推荐

最终目标是构建一个：

👉 图谱驱动 + RAG 支撑 + 个性化学习路径的智能伴学系统

---

## 2. 系统整体架构

系统分为三层：

### 1）知识层（Knowledge Layer）
- PDF → MinerU → Markdown
- 构建知识图谱（节点 + 网状关系）
- 候选池生成（definition / formula / example）

### 2）检索层（Retrieval Layer）
- Chroma 向量检索
- BM25 关键词检索
- rerank 重排
- 节点级 RAG

### 3）学生层（Student Layer）
- student_state
- 学习记录 / 掌握度
- 个性化推荐路径

---

## 3. 知识图谱设计（核心升级）

### 从树结构 → 网状结构

旧版本：
- level + parent-child

新版本：
- 去层级
- 节点平权
- 用关系表达结构

---

### 关系体系

统一格式：

relation_type + relation_strength + direction_type

核心关系：
- prerequisite_of（前置）
- parallel_to（并列）
- extends_to（拓展）
- related_to（关联）
- weak_related_to（弱关联）
- easy_to_confuse_with（易混淆）

---

## 4. 学生状态

字段：

- student_id
- current_node_id
- visited_nodes
- wrong_nodes
- mastery_scores
- recommended_queue

路径：

data/student_states/

---

## 5. debug_companion

用于统一调试系统：

知识类：ask / node / search  
结构类：prereq / next / path  
内容类：formulas / examples  
学生类：student / mastery  
决策类：recommend / review  

---

## 6. 图谱可视化调试工具

文件：

knowledge_graph_debug_viewer.html

功能：
- 图谱可视化
- 筛选关系
- 搜索节点
- 查看详情
- 统计孤立点

运行：

cd debug_tools
python -m http.server 8080

浏览器打开：

http://localhost:8080/knowledge_graph_debug_viewer.html

---

## 7. 当前已实现

✔ 知识图谱（网状结构）  
✔ 候选池  
✔ RAG 问答  
✔ 前置推理  
✔ 学生模型  
✔ 可视化调试  

---

## 8. 当前问题

- 推荐路径弱
- LearningPathBuilder 未完全适配
- embedding 维度冲突（1536 vs 384）
- 部分内容缺失
- 关系强度规则化

---

## 9. 下一步

- 学习路径优化
- 个性化推荐
- 向量库统一
- 图谱前端联动

---

## 10. 节点结构

包含：

基础信息：
- node_id / name / chapter / source_type

路径：
- prerequisite_nodes / next_nodes / related_nodes / recommended_next_nodes

教材：
- page_refs / anchor_page / section_title

候选池：
- definition / key_point / formula / example

生成：
- explanation / formulas / examples

教学：
- tags / importance / requirement / mastery_threshold

---

## 11. 总结

系统已从：

静态知识点列表

升级为：

图谱 + RAG + 学生建模的学习系统雏形

---

## 项目亮点

本项目实现了从教材解析 → 知识图谱 → RAG → 学生建模 → 可视化调试的完整闭环，
并将树状结构升级为支持关系强度的网状知识图谱。
