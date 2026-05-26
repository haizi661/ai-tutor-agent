# Artificial Intelligence Learning Path

本目录实现“人工智能”课程的独立学习路径模式。它和默认的自控 LangGraph 主流程不同：这里更像一个轻量的 AI 课程路径规划与节点讲解服务，围绕 `ai_nodes.csv` / `ai_edges.csv` 运行，并复用知识图谱媒体索引来展示公式、图表和表格。

## 入口文件

- `ai_path_routes.py`
  - FastAPI 路由，挂载在 `/api/ai-path/*`。
  - 主要接口：`/chat`、`/teach`、`/next`、`/node/{node_id}`、`/reload`。
- `ai_path_service.py`
  - AI path 的核心服务。
  - 负责意图理解、路径生成、当前节点讲解、追问回答、进度推进、学生状态读写。
- `config.py`
  - 从 `course_assets.py` 读取人工智能课程资产路径。
- `build_ai_course_assets.py`
  - 离线构建入口，用于生成或刷新 AI 课程资产。
- `build_ai_nodes_from_seed.py`
  - 从 `data/ai_knowledge_seed/` 的种子文件生成 AI 节点。
- `build_ai_edges_from_nodes.py`
  - 从节点生成边关系。
- `normalize_ai_nodes.py`
  - 清洗、归一化节点字段。

## 运行资产

人工智能课程运行时依赖这些文件：

```text
data/knowledge_map_outputs/artificial_intelligence/ai_nodes.csv
data/knowledge_map_outputs/artificial_intelligence/ai_edges.csv
data/mineru_cache/artificial_intelligence/**
data/media_evidence_index/artificial_intelligence/**
data/student_states/artificial_intelligence/student_state.json
```

其中：

- `ai_nodes.csv` 是节点知识库，包含节点说明、公式、例子、页码、图表引用和 `extra.retrieval_source_pdf`。
- `ai_edges.csv` 是节点关系图，主要包含前置关系、相关关系等。
- `data/mineru_cache/artificial_intelligence/**` 保存 MinerU 解析结果和真实图片文件。
- `data/media_evidence_index/artificial_intelligence/**` 保存公式、图、表到节点的映射索引。
- `student_state.json` 是 AI path 的轻量学习状态。

课程资产统一由 `ai_tutor_agent/course_assets.py` 管理。人工智能课程的 `course_id` 是：

```text
artificial_intelligence
```

别名包括：

```text
ai
artificial-intelligence
artificial_intelligence
```

## 主流程

前端选择人工智能模式后，流程大致是：

```text
用户输入学习目标
-> /api/ai-path/chat
-> AILearningPathService.chat()
-> 识别目标节点或生成路径
-> 展示 AI path 路线
-> 用户点击开始学习
-> /api/ai-path/teach
-> teach_current_node()
-> 生成当前节点讲解
-> 映射公式/图表媒体
-> 输出 learning-answer-content HTML
```

当前节点追问走：

```text
/api/ai-path/chat
-> answer_current_node_question()
-> 结合当前节点回答
-> 映射公式/图表媒体
-> 输出 learning-answer-content HTML
```

## 图表和公式渲染

AI path 不直接把 `figures_refs` 当正文显示。现在的正确链路是：

```text
当前 node
-> extra.retrieval_source_pdf
-> GraphMediaEnricher
-> data/media_evidence_index/artificial_intelligence/**
-> data/mineru_cache/artificial_intelligence/**/extracted/images/**
-> media_items
-> build_learning_answer_html()
-> learning-answer-content
-> frontend sanitizeLearningHtml + renderMath
```

关键代码：

- `AILearningPathService._collect_node_media_items()`
- `AILearningPathService._render_learning_message()`
- `GraphMediaEnricher.collect_for_nodes()`
- `build_learning_answer_html()`

如果图片只出现在“参考资料”里，而没有真实卡片，优先检查：

1. `data/media_evidence_index/artificial_intelligence/` 是否存在。
2. 对应节点的 `extra.retrieval_source_pdf` 是否能和媒体索引的 `source_doc_id` 对上。
3. `data/mineru_cache/artificial_intelligence/.../extracted/images/` 下图片是否真实存在。
4. 前端消息是否包含 `learning-answer-content`。
5. 是否重启了 `python main.py`，避免仍在跑旧进程。

## 调试命令

不走 `main.py`，只调试“节点 -> 媒体映射 -> HTML 输出”：

```powershell
.\venv\Scripts\python.exe -B scripts\debug_ai_path_media.py --node-id AI001 --out data\debug_outputs\ai_path_media_AI001.html
.\venv\Scripts\python.exe -B scripts\debug_ai_path_media.py --node-id AI060 --out data\debug_outputs\ai_path_media_AI060.html
```

打开输出 HTML，确认：

```text
render_has_learning_answer_content: yes
render_has_figure_card: yes
render_has_img_tag: yes
```

AI060 还应看到：

```text
render_has_formula_card: yes
```

## 离线构建

运行时不应该触发 MinerU。人工智能课程 PDF 处理是离线步骤。

常用命令：

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --dry-run
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --split-only
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --mineru-only
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --skip-edge-llm
```

相关说明见：

```text
docs/artificial-intelligence-offline-assets.md
```

## 和自控主流程的关系

AI path 复用了一部分通用能力：

- `course_assets.py` 的课程资产配置。
- `GraphMediaEnricher` 的媒体映射。
- `build_learning_answer_html()` 的学习内容 HTML 渲染。
- 前端 `sanitizeLearningHtml()` 与公式渲染。

但它不复用自控的完整 LangGraph 学习状态机：

- AI path 使用 `AILearningPathService` 自己的 `chat/teach/next` 流程。
- AI path 状态存在 `data/student_states/artificial_intelligence/student_state.json`。
- AI path 前端由 `frontend/assets/js/ai_path.js` 控制。
- 恢复人工智能会话时，不应自动展示自控知识图谱可视化卡。

## 维护注意事项

- 不要在 Web runtime 中自动运行 MinerU 或重建大资产。
- 修改节点 CSV 字段时，要确认 `_format_node()` 仍能解析列表字段和 `extra`。
- 媒体渲染问题优先用 `scripts/debug_ai_path_media.py` 定位，不要先猜前端。
- AI path 的输出如果包含 HTML，必须继续走 `learning-answer-content` 和前端 allowlist sanitizer。
- `data/debug_outputs/` 只是调试产物，可以删除。
