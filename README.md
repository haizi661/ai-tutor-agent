# AI Tutor Agent

`AI Tutor Agent` 是一个围绕“讲解 -> 出题 -> 评估 -> 补讲”闭环构建的自适应伴学系统。当前主入口是 Web 端，支持上传资料做 RAG 检索，也支持在正式流程中临时追问，再回到原来的主线。

## 核心能力

- 知识图谱节点制掌握学习：主题确认 -> 学前诊断 -> 图谱节点选择 -> 节点讲解 -> 节点测试 -> 错题补救 -> 下一节点/作业
- 图谱 2.1 主线推进：负责学习路径、当前节点、前置关系、学习目标、必会点和常见误区
- 图谱 2.2 / RAG 证据增强：负责临时问题、图表/公式/资料证据检索与补充回答
- 节点后客观题批量测试：支持 answer_key 确定性评分，避免把客观题评分交给 LLM 自由判断
- 学生状态与作业恢复：支持学习记录、作业生成、二次登录恢复和继续学习
- Web 会话恢复：支持历史恢复、等待输入恢复、状态横幅恢复
- 资料库检索：支持上传 PDF / Markdown / 文本，向量库存储默认在 `data/chroma_db`
- 本地运维配置：Web 本地设置页与 `.env` 一致

## 运行要求

- 推荐 Python `3.9+`
- 如果要跑在 Python `3.8`，需要额外维护一套旧版本依赖约束；默认依赖矩阵不保证即装即用

安装：

```bash
python -m pip install -r requirements.txt
```

或：

```bash
python -m pip install -e .
```

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
PDF_PARSE_BACKEND=auto
MINERU_PROXY_MODE=inherit
VECTOR_STORE_DIR=data/chroma_db
HF_ENDPOINT_FALLBACK_ENABLED=true
HF_MIRROR_ENDPOINT=https://hf-mirror.com
```

行为说明：

- `PDF_PARSE_BACKEND=auto`：先试 MinerU，失败回退本地 PyMuPDF
- `MINERU_PROXY_MODE=direct`：只让 MinerU 直连，其他模型和 HuggingFace 继续走代理
- 本地 embedding 首次下载 HuggingFace 模型时，如果默认源不可达，会自动改用 `HF_MIRROR_ENDPOINT`，默认是 `https://hf-mirror.com`
- Web 端“清空书架”会删除知识文件和当前知识向量，但 `data/chroma_db` 目录本身可能保留为空数据库目录

## Web 使用方式

当前推荐从 Web UI 使用，主流程已经升级为知识图谱节点制掌握学习：

1. 先输入学习主题，例如“自动控制原理中的根轨迹法”。
2. 主题确认后，推荐选择先做学前诊断，不要直接跳过测评。
3. 系统会根据诊断结果选择图谱 2.1 初始节点，并加载当前节点内容开始讲解。
4. 讲解后可以选择“我还有临时问题”或“没有问题，开始测试”。
5. 临时问题走图谱 2.2 / RAG 检索回答，回答后回到讲解后选择。
6. 开始测试后进入节点客观题批量测试；通过则规划下一节点，未通过则进入错题讲解与变式题。
7. 节点通过后可以继续下一个节点，也可以今天结束并生成作业。
8. 二次登录/恢复会优先检查作业和学习进度，尽量接着原状态继续。

更详细的当前状态、使用命令、缺口与下一步计划见：

- `docs/current-status-and-usage.md`
- `docs/next-iteration-plan.md`

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

开发后至少跑一遍：

```bash
pytest -q
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
