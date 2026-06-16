# Standalone Knowledge Graph Builder

独立于原伴学项目的知识图谱生成功能：

1. 上传教材 PDF（支持大文件）
2. 自动生成候选知识点节点与关系边
3. 人工审核（编辑/勾选保留）
4. 生成最终知识图谱
5. 可视化所有节点（HTML 图谱）

## Quick Start

```bash
pip install -r kg_builder_standalone/requirements.txt
streamlit run kg_builder_standalone/app.py
```

## 调试程序（无界面）

```bash
python -m kg_builder_standalone.debug_kg_pipeline --pdf "data/knowledge/your_book.pdf" --out kg_builder_standalone/outputs --name textbook_graph --open
```

## 权重标注调试程序（教材 + 课程大纲）

```bash
python -m kg_builder_standalone.debug_weighted_kg_pipeline \
  --textbook-pdf "data/knowledge/配套资料1：自动控制原理（第八版） (胡寿松、姜斌、张绍杰) .pdf" \
  --outline-pdf "data/knowledge/自动控制原理课程大纲-上海交通大学.pdf" \
  --out kg_builder_standalone/outputs \
  --name sjtu_auto_control_weighted_graph
```

说明：

- 节点初始权重默认取 `confidence`。
- 当课程大纲中出现知识点并伴随关键词（如“理解”“掌握”“熟练掌握”）时，提升该节点 `weight`。
- 未被大纲涉及或未命中权重关键词的节点，保持初始权重。

## 输出文件

- `*_nodes.csv`：最终节点
- `*_edges.csv`：最终边
- `*.graphml`：图数据库/图工具可导入格式
- `*.json`：结构化图数据
- `*.html`：可交互可视化图
- `*_weight_summary.json`：权重标注统计摘要（仅权重调试程序生成）

## 说明

- 默认目标节点数为 50-100，可在 UI 调整。
- 关系默认包含：
  - `same_chapter`（同章关系）
  - `subtopic_of`（词法层面的上下位关系）
- 推荐在“人工审核”步骤中删除低质量节点与边，再生成最终图谱。
