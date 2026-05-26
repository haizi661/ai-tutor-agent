# Knowledge Map

本目录维护课程知识图谱、GraphRAG 检索、媒体证据索引和学习内容 HTML 渲染。当前系统同时支持两套课程资产：

- 自动控制原理，默认主流程课程。
- 人工智能，AI path 课程。

两者共享同一套图谱/媒体基础设施，但入口、运行状态和资产目录不同。

## 模块职责

`knowledge_map` 主要负责四件事：

1. 读取课程节点和边。
2. 基于图谱做节点选择、子图遍历和上下文组织。
3. 将节点映射到教材中的公式、图表、表格。
4. 生成前端可安全渲染的学习 HTML。

典型链路：

```text
nodes.csv / edges.csv
-> GraphRAGPipeline
-> NodeSelector
-> GraphTraverser
-> GraphContextBuilder
-> GraphMediaEnricher
-> GraphAnswerGeneratorV2
-> build_learning_answer_html()
-> frontend sanitizeLearningHtml()
```

## 关键文件

- `graph_rag_pipeline.py`
  - GraphRAG 主入口。
  - 支持通过 `course_id` 选择课程资产。
- `builders/`
  - 图谱问答和上下文构造组件。
  - `graph_media_enricher.py` 是公式、图表、表格映射的核心。
- `media_index/`
  - 扫描 MinerU 输出、生成候选媒体、链接节点。
- `build_media_index_batch.py`
  - 批量构建媒体证据索引。
- `debug_graph_rag.py`
  - GraphRAG 调试输出和学习 HTML 渲染工具。
  - `build_learning_answer_html()` 被自控主流程和人工智能路径共同使用。
- `runtime_assets.py`
  - 检查媒体证据索引是否可用。
- `runtime_defaults.py`
  - 默认媒体索引目录，目前默认指向自控 vision pilot 资产。
- `student_state.py`
  - 自控主流程的图谱学习状态存储模型。
- `map_README.md`
  - 历史说明文档，仅作参考；当前维护以本 README 和 `docs/current-status-and-usage.md` 为准。

## 课程资产配置

课程资产统一在：

```text
ai_tutor_agent/course_assets.py
```

### 自动控制原理

```text
course_id: auto_control
nodes: data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv
edges: data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv
mineru cache: data/mineru_cache
media index: data/media_evidence_index_vision_pilot
student state: data/student_states/default.json
```

常见别名：

```text
a2-control-theory
control
auto-control
auto_control
automatic_control
```

### 人工智能

```text
course_id: artificial_intelligence
nodes: data/knowledge_map_outputs/artificial_intelligence/ai_nodes.csv
edges: data/knowledge_map_outputs/artificial_intelligence/ai_edges.csv
mineru cache: data/mineru_cache/artificial_intelligence
media index: data/media_evidence_index/artificial_intelligence
student state: data/student_states/artificial_intelligence/student_state.json
```

常见别名：

```text
ai
artificial-intelligence
artificial_intelligence
```

## 自控和人工智能的相同点

两门课共享这些设计：

- 都用节点 CSV 和边 CSV 表示课程图谱。
- 都用 `node_id` 作为图谱、媒体、状态之间的主要连接键。
- 都支持前置关系、相关关系、并列关系等图谱边。
- 都可以使用 `GraphMediaEnricher` 从媒体索引中找公式、图表、表格。
- 都可以用 `build_learning_answer_html()` 输出 `learning-answer-content`。
- 前端都通过 `sanitizeLearningHtml()` 做 allowlist 清洗，并通过 `renderMath()` 渲染公式。

媒体卡片的统一数据结构是 `media_items`，常见字段包括：

```text
reference
asset_type
display_label
source_doc_id
image_paths_abs
latex
caption
is_primary
```

## 自控和人工智能的不同点

### 入口不同

自控默认走 LangGraph 主教学流：

```text
topic confirmation
-> assessment
-> graph node selection
-> tutor lesson
-> post lesson choice
-> objective test / temporary question
-> mastery update
```

人工智能走独立 AI path：

```text
goal input
-> AI path planning
-> current node lesson
-> free-form question or next node
-> path advance
```

对应代码：

```text
自控: ai_tutor_agent/nodes/ + ai_tutor_agent/orchestration/
人工智能: ai_tutor_agent/ai_learning_path/
```

### 图谱资产来源不同

自控图谱是当前主教学 Graph B 运行资产，主要由既有构建链路和图谱资产同步得到。

人工智能图谱来自 AI 课程种子和离线构建脚本：

```text
data/ai_knowledge_seed/**
ai_tutor_agent/ai_learning_path/build_ai_nodes_from_seed.py
ai_tutor_agent/ai_learning_path/build_ai_edges_from_nodes.py
ai_tutor_agent/ai_learning_path/build_ai_course_assets.py
```

### 媒体目录不同

自控媒体索引：

```text
data/media_evidence_index_vision_pilot/
```

人工智能媒体索引：

```text
data/media_evidence_index/artificial_intelligence/
```

自控 MinerU 缓存：

```text
data/mineru_cache/
```

人工智能 MinerU 缓存：

```text
data/mineru_cache/artificial_intelligence/
```

### 节点字段差异

两者都包含节点名、章节、说明、公式、示例、页码和图表引用，但人工智能节点更依赖 `extra` 字段中的检索来源：

```json
{
  "retrieval_source_pdf": "...",
  "retrieval_matched_block_title": "...",
  "retrieval_formula_line_count": 0,
  "retrieval_figure_line_count": 2
}
```

`GraphMediaEnricher` 会优先利用 `retrieval_source_pdf` 把节点限制到同一份教材文档，避免跨章节误配。

### 前端行为不同

自控会在主教学流中展示知识图谱可视化卡。

人工智能路径不应该自动弹出自控图谱卡；AI path 由自己的路线卡和侧边路径面板表达进度。

## 媒体索引如何工作

媒体索引构建分三步：

```text
MinerU cache
-> media_asset_scanner
-> filtered_candidates.jsonl
-> media_node_linker
-> linked_candidates.jsonl
-> annotated_assets.jsonl
```

运行时 `GraphMediaEnricher` 会：

1. 读取节点信息和当前问题。
2. 在 `annotated_assets.jsonl` 中找直接链接到节点的资产。
3. 如果标注资产不足，回退到 MinerU 文档中的公式、图、表。
4. 为资产分配 `display_label`，例如 `图一`、`式一`。
5. 选出主媒体和补充媒体。
6. 返回给回答生成器或学习 HTML 渲染器。

## 学习 HTML 渲染

`build_learning_answer_html(result)` 接收：

```python
{
    "answer": "...",
    "media_items": [...],
    "evidence_items": [...]
}
```

它会输出：

```html
<div class="learning-answer-content">...</div>
```

支持：

- 行内公式和块级公式。
- Markdown 标题、加粗、斜体、行内代码和简单列表。
- `[[MEDIA:reference]]` 媒体插入标记。
- 未被正文引用的相关媒体补充区。
- 表格和长公式的局部滚动容器。

前端必须用学习 HTML 通道渲染，不能直接把这段 HTML 当普通 Markdown 或普通文本插入。

## 调试命令

检查自控媒体索引：

```powershell
python -m ai_tutor_agent.knowledge_map.runtime_assets --media-index data/media_evidence_index_vision_pilot
```

检查人工智能节点媒体映射：

```powershell
.\venv\Scripts\python.exe -B scripts\debug_ai_path_media.py --node-id AI001 --out data\debug_outputs\ai_path_media_AI001.html
.\venv\Scripts\python.exe -B scripts\debug_ai_path_media.py --node-id AI060 --out data\debug_outputs\ai_path_media_AI060.html
```

直接测试 GraphRAGPipeline：

```powershell
.\venv\Scripts\python.exe -B -c "from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline; p=GraphRAGPipeline(course_id='artificial_intelligence', enable_llm=False); r=p.ask('线性回归 图2.5'); print(len(r['media_items']), [x['asset_type'] for x in r['media_items'][:5]])"
```

## 常见问题

### 图片只显示名称，不显示图片

优先检查：

- `media_items` 是否为空。
- `image_paths_abs` 是否存在且路径真实。
- 节点 `extra.retrieval_source_pdf` 是否和媒体索引的 `source_doc_id` 一致。
- 前端是否按 `learning-answer-content` 渲染。
- 服务是否重启。

### 公式显示 LaTeX 原码

可能原因：

- 静态调试 HTML 没加载主页面 MathJax。
- 前端没有调用 `app.renderMath()`。
- 公式没有被包成 `formula-render` 或 `inline-formula-render`。

### 媒体跨章节误配

优先检查：

- 节点的 `retrieval_source_pdf`。
- `GraphMediaEnricher` 的同源文档过滤。
- `media_node_linker.py` 的节点匹配规则。

## 维护原则

- 不要在 Web runtime 中自动跑 MinerU 或重建大索引。
- 新课程应先在 `course_assets.py` 注册资产路径，再接入 `GraphRAGPipeline(course_id=...)`。
- 媒体索引和 MinerU 图片文件必须一起迁移；只有索引没有图片，前端无法显示图表。
- 历史 `map_README.md` 和 `Code explanation.md` 只作背景参考，当前实现以本 README、`AGENTS.md`、`docs/current-status-and-usage.md` 和 `docs/knowledge-map-runtime-assets.md` 为准。
