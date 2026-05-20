# A2 控制理论知识图谱字段说明

本文档说明 `graph.json` 的数据结构，重点介绍节点属性，方便后续教学智能体、检索系统或可视化工具直接读取。

## 顶层结构

- `meta`
  图谱元信息与统计信息。
- `nodes`
  节点数组，每个节点对应一篇 A2 控制理论笔记。
- `edges`
  边数组，表示节点之间的 wiki 链接关系。
- `adjacency`
  邻接表，便于程序快速查找入边和出边。
- `external_references`
  指向 A2 子图外部的概念引用，包括项目内已有概念和当前仓库缺失概念。
- `curriculum`
  按课程目录整理出的课程骨架。

## 节点属性

### 身份与路径信息

- `id`
  节点唯一标识。
- `title`
  节点标题。
- `file_name`
  原始 Markdown 文件名。
- `source_path`
  原始笔记在项目中的路径。
- `raw_copy_path`
  导出后在 `source-notes/` 中的快照路径。
- `permalink`
  原网站中的访问路径。
- `dg_path`
  原始知识体系路径。
- `path_segments`
  `dg_path` 拆分后的数组形式。

### 分类与组织信息

- `category`
  一级分类，例如 `1. 经典控制理论`。
- `subcategory`
  二级分类。
- `pinned`
  是否为主干节点。
- `level`
  原始笔记中的 `Level` 字段。

### 语义与内容信息

- `tags`
  标签数组。
- `aliases`
  别名数组。
- `terminology`
  英文术语或术语说明。
- `summary`
  自动抽取的摘要。
- `headings`
  笔记标题列表。
- `created`
  创建时间。
- `updated`
  更新时间。

### 图谱关系信息

- `outbound_internal_ids`
  指向 A2 子图内部其他节点的链接列表。
- `outbound_external_links`
  指向 A2 子图外部的所有链接列表。
- `outbound_out_of_scope_links`
  指向项目内已有、但不属于 A2 子图的链接列表。
- `outbound_missing_links`
  指向当前仓库中尚无对应笔记的概念列表。
- `inbound_internal_ids`
  A2 子图内部有哪些节点链接到了当前节点。

### 内容文件定位

- `content_markdown_file`
  当前节点对应的 Markdown 快照路径。

### 教学元数据字段

这些字段是根据 `table.csv` 的建议，以增量方式补充到每个节点上的：

- `prerequisites`
  必须先学的前置知识列表。
- `neighbors`
  强相关但非必须先修的并行知识点列表。
- `learning_objectives`
  学完该节点后学生应达到的学习目标列表。
- `must_know`
  本节点最核心、必须掌握的概念、公式、结论或主线提示。
- `teaching_modes`
  推荐教学方式对象，包含 `analogy`、`derivation`、`example`、`visualization`、`practice`。
  每个键都包含：
  - `priority`
  - `reason`
- `assessment_modes`
  推荐考察方式对象，包含 `conceptual`、`calculation`、`judgment`、`application`。
  每个键都包含：
  - `priority`
  - `reason`
- `target_mastery_level`
  目标掌握层级，当前取值为 `Understand / Apply / Master / Advanced`。
- `common_errors`
  常见错误数组，每项都包含：
  - `error`
  - `cause`
  - `correction`
- `difficulty`
  难度标签，当前取值为 `easy / medium / hard / advanced`。

## 边属性

- `source`
  起点节点 `id`。
- `target`
  终点节点 `id`。
- `type`
  当前固定为 `wikilink`。
- `relation_label`
  从原笔记上下文中抽取出的关系标签。
- `relation_candidates`
  候选关系标签及出现次数。
- `weight`
  从 `source` 指向 `target` 的链接出现次数。
- `mentions`
  该边在原文中的部分上下文片段。

## 说明

- `prerequisites`、`neighbors`、`learning_objectives`、`must_know` 等字段目前是依据知识点标题、分类、章节结构、关系标签和课程主线自动推断生成的。
- 它们已经可以直接用于教学智能体、推荐系统和评测系统，但仍然适合在后续版本中继续人工微调。
