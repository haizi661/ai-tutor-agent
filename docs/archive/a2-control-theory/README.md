# A2 Control Theory Knowledge Graph

这个目录是从 `Atlas-of-Control-and-AI` 项目中抽取出来的 A2 控制理论专用知识图谱，目标是为后续“自动控制原理”教学智能体提供可直接读取的数据底座。

## 文件说明

- `graph.json`
  - 完整知识图谱
  - 包含 `meta`、`nodes`、`edges`、`adjacency`、`external_references`
- `notes.jsonl`
  - 一行一篇笔记的机器可读语料
  - 包含元数据、内部链接、外部链接、原始 Markdown 内容、纯文本内容
- `summary.json`
  - 数据集摘要统计
- `curriculum.json`
  - 按 A2 目录顺序整理的课程骨架
- `source-notes/`
  - A2 控制理论原始 Markdown 快照
- `viewer/`
  - 独立静态可视化页面
  - 打开 `viewer/index.html` 即可浏览知识图谱

## 当前数据规模

- A2 笔记数：`85`
- 内部边数：`240`
- 外部引用总数：`117`
- 其中超出 A2 但项目内存在的引用：`83`
- 其中当前仓库缺失的引用：`34`

## 推荐读取方式

1. 用 `graph.json` 做知识关系导航、先修关系分析、主题聚类。
2. 用 `notes.jsonl` 做检索、问答、切片、向量化。
3. 如需保留原始上下文和 Markdown 结构，直接读取 `source-notes/`。
4. 如需人工查看关系网络，打开 `viewer/index.html`。

## 数据边界

- 仅保留 `dg-path` 以 `A2- 控制理论` 开头的笔记。
- 图谱内部边仅统计 A2 笔记之间的 wiki 链接。
- 指向 A2 之外但项目内存在的 wiki 链接，会被标记为 `out_of_scope`。
- 当前仓库中没有对应笔记的 wiki 链接，会被标记为 `missing`。
- 这两类链接都会保留在 `external_references` 以及每篇笔记的外部链接字段中，但不会作为本子图节点写入。
