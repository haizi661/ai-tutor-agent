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

## 输出文件

- `*_nodes.csv`：最终节点
- `*_edges.csv`：最终边
- `*.graphml`：图数据库/图工具可导入格式
- `*.json`：结构化图数据
- `*.html`：可交互可视化图

## 说明

- 默认目标节点数为 50-100，可在 UI 调整。
- 关系默认包含：
  - `same_chapter`（同章关系）
  - `subtopic_of`（词法层面的上下位关系）
- 推荐在“人工审核”步骤中删除低质量节点与边，再生成最终图谱。
