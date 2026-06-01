# AI Tutor Agent

`AI Tutor Agent` 是一个围绕“讲解 -> 出题 -> 评估 -> 补讲”闭环构建的自适应伴学系统。当前主入口是 Web 端，支持上传资料做 RAG 检索，也支持在正式流程中临时追问，再回到原来的主线。

## 核心能力

- 知识图谱节点制掌握学习：主题确认 -> 学前诊断 -> 图谱节点选择 -> 节点讲解 -> 节点测试 -> 错题补救 -> 下一节点/作业
- 图谱 2.1 主线推进：负责学习路径、当前节点、前置关系、学习目标、必会点和常见误区
- 学习路径面板：聊天右侧独立面板，显示多步学习路径进度、当前 Step 节点列表和完成状态
- 图谱 2.2 / RAG 证据增强：负责临时追问、图表/公式/资料证据检索与补充回答，并把公式/图表/表格渲染为学习者可读的证据卡片
- 临时问答证据布局：正文引用的公式、图表、表格会绑定在对应解释段落附近；未被正文引用的补充媒体只作为限量参考，避免重复堆叠
- 节点后客观题批量测试：支持 answer_key 确定性评分，避免把客观题评分交给 LLM 自由判断
- 客观题复盘界面：提交后按题展示所选答案、正确答案、判断依据、所选项问题、常见误区和下一步动作，选项使用整行可读布局
- 错题本：按知识节点分组，支持全部/待复习/已掌握筛选、展开讲解、标记已掌握/取消掌握，并保留后端排序接口
- 题目答疑：支持粘贴题干或上传图片题，选择快速解答/深度解析/图片题专用模式，保留近期解答记录
- 本地 Markdown/公式渲染：前端直接加载本地 `marked` 与 `katex` vendor 资源，题目答疑和复盘解释可渲染 Markdown 与 LaTeX
- 最小本地题库 Provider：支持 `data/question_bank/<course_id>/*.jsonl`，题库不足时 fallback 到 AI/内置题
- 学生状态与作业恢复：支持学习记录、作业生成、二次登录恢复和继续学习
- 用户画像与学情原型：学前诊断生成概念差距、起始难度和教学策略；学习过程记录节点掌握、错题节点、题目作答和作业历史
- 前端交互卡片恢复：支持讲解后选择、批量题卡、继续/作业选择、作业复习等 pending/locked 状态
- Web 会话恢复：支持历史恢复、等待输入恢复、状态横幅恢复，并在恢复后定位到当前待处理卡片
- 资料库检索：支持上传 PDF / Markdown / 文本，向量库存储默认在 `data/chroma_db`
- 本地运维配置：Web 本地设置页与 `.env` 一致

## 运行要求

- 推荐 Python `3.9+`
- 如果要跑在 Python `3.8`，需要额外维护一套旧版本依赖约束；默认依赖矩阵不保证即装即用

安装：

```bash
python -m pip install -r requirements.txt
```

中国大陆网络建议使用镜像安装依赖：

```bash
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果后续需要安装 npm 依赖，先固定 npm 镜像：

```bash
npm config set registry https://registry.npmmirror.com
```

也可以一次性写入本机 pip/npm 镜像配置：

```bash
bash scripts/setup_cn_mirrors.sh
```

或：

```bash
python -m pip install -e .
```

前端没有打包流水线；浏览器直接加载 `frontend/` 下的静态文件。`package.json` 当前只用于固定 `marked` 与 `katex` 版本，本地运行不需要 `npm run build`。

### 知识图谱解析失败排查（GitHub 拉取后常见）

如果你能启动服务，但提示课程图谱解析失败或课程节点为空，优先检查下面三项：

1. 安装方式是否正确：
	- 推荐在仓库根目录执行 `python -m pip install -r requirements.txt`。
	- 仅使用旧的最小依赖或不完整环境，可能缺少 `pymupdf`、`rank-bm25` 等解析依赖。
2. 图谱数据目录是否存在：
	- 当前主教学流程默认读取 2026-04-27 图谱 B 运行资产：`data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv`、`data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv`、`data/mineru_cache` 与 `data/media_evidence_index`。
	- 历史 Graph A / A2 资料已归档到 `docs/archive/a2-control-theory/`，不作为当前主教学图谱。
3. 快速自检：

```bash
python - <<'PY'
from ai_tutor_agent.config import get_settings
from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider

s = get_settings()
kp = LocalFileKnowledgeProvider(s)
print('course_primary_dir =', s.course_primary_dir)
print('course_graph_nodes =', len(getattr(kp, 'course_graph_nodes', {}) or {}))
print('initialization_error =', kp.initialization_error)
PY
```

说明：旧 `notes.jsonl` / `graph.json` course_primary 逻辑仅保留为兼容路径；默认关闭，避免误把归档 Graph A 当成当前主教学图谱。

## 快速启动

1. 复制配置模板

```bash
cp .env.example .env
```

2. 在 `.env` 里至少配置一组可用模型 Key

- `GOOGLE_API_KEY`
- `QWEN_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `MINIMAX_API_KEY`
- `GLM_API_KEY`

3. 启动服务

```bash
python main.py
```

说明：

- Web UI 端口固定为 `8000`；如果已被旧进程占用，启动会直接报错，而不是偷偷切到别的端口
- `AI_TUTOR_HOST` 只控制绑定地址，不控制端口；例如 `AI_TUTOR_HOST=127.0.0.1 python main.py`

当前项目在作者本地常用的启动方式如下：

```bash
GRAPH_RAG_ENABLE_LLM=true \
GRAPH_RAG_LLM_PROFILE=deepseek \
CHAT_PROFILE=deepseek \
LLM_PROVIDER=openai \
MODEL_NAME=deepseek-v4-flash \
python main.py
```

如果要切换到千问配置，可使用：

```bash
GRAPH_RAG_ENABLE_LLM=true \
GRAPH_RAG_LLM_PROFILE=qwen \
CHAT_PROFILE=qwen \
LLM_PROVIDER=openai \
MODEL_NAME=qwen-plus \
python main.py
```

说明：

- 以上命令默认都在项目根目录执行，不依赖任何机器上的绝对路径
- 项目内路径统一写成 `data/...`、`docs/...`、`frontend/...` 这类相对路径
- Linux、macOS、Windows、WSL 都应保持这个口径；若 shell 语法不同，只调整环境变量写法，不修改项目路径
- 当前临时问答链路在 Windows 环境下仍有部分兼容问题未完全收敛，跨系统联调时请优先检查模型配置和 shell 写法

4. 浏览器访问

```text
http://127.0.0.1:8000
```

## 日常运维只看这几项

最常改的配置只有下面四类：

- `PROXY_PORT`：你的本地代理端口，例如 `7897` 或 `7892`
- `PDF_PARSE_BACKEND`：`auto` / `mineru` / `local`
- `MINERU_PROXY_MODE`：`inherit` / `direct`
- `VECTOR_STORE_DIR`：推荐保持 `data/chroma_db`

推荐默认值：

```env
PROXY_HOST=127.0.0.1
PROXY_PORT=7897
PROXY_SCHEME=http
NO_PROXY=
PDF_PARSE_BACKEND=auto
MINERU_PROXY_MODE=inherit
VECTOR_STORE_DIR=data/chroma_db
HF_ENDPOINT_FALLBACK_ENABLED=true
HF_MIRROR_ENDPOINT=https://hf-mirror.com
```

行为说明：

- 启用 `PROXY_HOST` / `PROXY_PORT` 后，国外 API 默认走代理；国内模型端点和镜像域名会自动合并进 `NO_PROXY`，直接连接
- 国内直连域名包括 Qwen/DashScope、DeepSeek、MiniMax、GLM、MinerU/OpenXLab、`hf-mirror.com`、ModelScope、常见 PyPI 和 npm 镜像
- `PDF_PARSE_BACKEND=auto`：先试 MinerU，失败回退本地 PyMuPDF
- `MINERU_PROXY_MODE=direct`：只让 MinerU 直连，其他模型和 HuggingFace 继续走代理
- 本地 embedding 首次下载 HuggingFace 模型时，如果默认源不可达，会自动改用 `HF_MIRROR_ENDPOINT`，默认是 `https://hf-mirror.com`
- Web 端“清空书架”会删除知识文件和当前知识向量，但 `data/chroma_db` 目录本身可能保留为空数据库目录

## Web 使用方式

当前推荐从 Web UI 使用，主流程已经升级为知识图谱节点制掌握学习：

1. 先输入学习主题，例如“自动控制原理中的根轨迹法”。
2. 主题确认后，推荐选择先做学前诊断，不要直接跳过测评。
3. 测评完成后，系统进入图谱 2.1 初始节点选择，并加载当前节点内容开始讲解。
4. 讲解后进入“课后停顿”：可以直接打一整句追问或卡点，也可以点击“继续追问”或“我懂了，进入小测”。
5. 临时追问走图谱 2.2 / RAG 检索回答；回答按问题复杂度自适应，不机械套固定模板，结束后回到“继续追问 / 我懂了，进入小测”。
6. 开始小测后进入节点客观题批量测试；通过则规划下一节点，未通过则进入错题讲解与变式题。
7. 提交小测后查看逐题复盘；每题会显示判断依据、所选项问题、常见误区和下一步动作。
8. 错题会进入侧边栏“错题本”，默认先看待复习题，可展开讲解并标记已掌握。
9. 遇到独立题目时，可打开侧边栏“题目答疑”，粘贴文字或上传图片，并选择解答模式。
10. 节点通过后可以继续下一个节点，也可以结束本轮学习并生成作业。
11. 二次登录/恢复会优先检查作业和学习进度，尽量接着原状态继续。

恢复历史时，页面应显示当前学习主题和图谱节点，并自动滚动到当前待处理卡片。长公式、宽表格和图表必须留在自己的局部滚动/预览容器中，不应撑破聊天区域或被底部输入框遮挡。

## 用户画像与学情状态

当前画像由两层组成：

1. 学前诊断画像：`user_profiler` 根据测评答案计算 `assessment_concept_gaps`、`assessment_radar`、`difficulty_level`、`teaching_strategy` 和初始 `user_knowledge_graph`。
2. 学习过程状态：`StudentStateStore` 在 `data/student_states/*.json` 中保存当前节点、掌握分、已学节点、错题节点、错题本、题目答疑记录、客观题作答记录、作业批次和作业历史。

这套状态已经能支撑恢复、继续学习和作业布置，但仍是轻量原型。后续产品化时应把它升级为明确的长期学习者模型：统一掌握分尺度，记录每次测验/追问/作业的证据事件，沉淀错因标签和复习时间，并让节点选择同时参考画像信号与知识图谱前置关系。

更详细的当前状态、使用命令、缺口与下一步计划见：

- `docs/current-status-and-usage.md`
- `docs/next-iteration-plan.md`
- `docs/knowledge-map-runtime-assets.md`
- `docs/plans/2026-04-30-interaction-artifact-validation-contract.md`：交互卡片、历史恢复与浏览器验收契约

## 项目结构

当前目录按职责拆分，后续扩展优先在现有层次上加，不要继续横向堆脚本：

- `ai_tutor_agent/application/`：会话协调与跨节点流程控制
- `ai_tutor_agent/core/`：状态、事件、协议
- `ai_tutor_agent/nodes/`：教学节点实现
- `ai_tutor_agent/orchestration/`：LangGraph 编排和路由
- `ai_tutor_agent/infrastructure/`：模型、RAG、存储、外部集成
- `ai_tutor_agent/interfaces/`：Web API / CLI 入口适配
- `frontend/`：前端页面与交互
- `tests/`：回归测试

## 扩展约定

为了后续可扩张，新增功能尽量遵守下面这套边界：

- 新教学步骤：优先加到 `ai_tutor_agent/nodes/`，再在 `orchestration/` 接线
- 新模型或 embedding：优先加到 `ai_tutor_agent/infrastructure/`
- 新 API：优先加到 `ai_tutor_agent/interfaces/api/`
- 不要在仓库根目录继续增加临时调试脚本、重复说明文档、一次性分析文件

## 验证

开发后至少跑一遍聚焦回归。当前本地建议禁用 pytest 插件自动加载，避免无关插件影响：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

涉及 GraphRAG HTML、前端交互卡片、历史恢复或临时追问时，还要补对应契约测试；只跑字符串级单测不能宣称 UI/流程完整闭合。

2026-05-01 对历史恢复、交流框高度、公式图表去重/限量与布局做过一次完整回归：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 452 passed, 5 warnings
```

2026-05-02 用户知识图谱、evidence 架构统一后完整回归：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
# 452 passed, 5 warnings
```

2026-05-29 错题本、题目答疑、客观题复盘、公式渲染与历史恢复相关聚焦回归：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_frontend_learning_content_layout.py \
  tests/test_frontend_question_help_ui.py \
  tests/test_frontend_objective_test_ui.py \
  tests/test_objective_learning_flow.py \
  tests/test_question_help_api.py \
  tests/test_objective_remediation_flow.py \
  tests/test_objective_remediation_regressions.py \
  tests/test_graph_rag_learning_answer_html.py \
  tests/test_history.py \
  tests/test_session_resume_router.py \
  tests/test_frontend_wrong_book_ui.py \
  tests/test_wrong_questions_api.py \
  tests/test_objective_history_and_remediation_timeline.py \
  tests/test_frontend_html_safety.py
# 128 passed, 5 warnings
```

## 离线检索评测（Recall@k / MRR / nDCG）

用于做 RAG 检索回归对比：

```bash
python scripts/evaluate_retrieval.py \
	--eval-file data/retrieval_eval/sample_eval.jsonl \
	--k-values 1,3,5 \
	--recall-k 12 \
	--output data/retrieval_eval/latest_report.json
```

评测集支持 `JSON` 或 `JSONL`，每条至少包含：

```json
{
	"query": "什么是闭环控制",
	"relevant": [
		{"filename": "控制系统导论.pdf", "chunk_id": 12},
		{"filename": "lecture_notes.md"}
	],
	"relevant_filenames": ["控制系统导论.pdf"]
}
```

说明：

- `relevant` 支持 chunk 级标签（`filename + chunk_id`）和文件级标签（仅 `filename`）。
- `relevant_filenames` 是可选文件级补充标签。
- 输出会给出汇总指标（Recall@k / MRR@k / nDCG@k）和逐 query 明细，适合做周度回归。

## License

项目使用 [MIT License](LICENSE)。
