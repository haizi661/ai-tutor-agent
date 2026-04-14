# AI Tutor Agent

`AI Tutor Agent` 是一个围绕“讲解 -> 出题 -> 评估 -> 补讲”闭环构建的自适应伴学系统。当前主入口是 Web 端，支持上传资料做 RAG 检索，也支持在正式流程中临时追问，再回到原来的主线。

## 核心能力

- 闭环教学：`Tutor -> Tester -> Evaluator`
- 临时提问不中断主线：支持“继续追问 / 回到主线”
- Web 会话恢复：支持历史恢复、等待输入恢复、状态横幅恢复
- RAG 资料检索：支持上传 PDF / Markdown / 文本，向量库存储默认在 `data/chroma_db`
- 本地运维配置：Web 本地设置页与 `.env` 一致

## 运行要求

- 推荐 Python `3.9+`
- 如果要跑在 Python `3.8`，需要额外维护一套旧版本依赖约束；默认依赖矩阵不保证即装即用

安装：

```bash
cd /home/haizi/ai-tutor-agent
python -m pip install -r requirements.txt
```

或：

```bash
cd /home/haizi/ai-tutor-agent
python -m pip install -e .
```

### 知识图谱解析失败排查（GitHub 拉取后常见）

如果你能启动服务，但提示课程图谱解析失败或课程节点为空，优先检查下面三项：

1. 安装方式是否正确：
	- 推荐在仓库根目录执行 `python -m pip install -r requirements.txt`。
	- 仅使用旧的最小依赖或不完整环境，可能缺少 `pymupdf`、`rank-bm25` 等解析依赖。
2. 图谱数据目录是否存在：
	- 默认读取 `a2-control-theory/source-notes`，并在同级目录读取 `notes.jsonl` / `graph.json`。
	- 若目录不在默认位置，请设置 `COURSE_PRIMARY_DIR=/你的路径/source-notes`。
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

说明：当 `notes.jsonl` 缺失时，系统会自动回退尝试从 `graph.json` 加载节点。

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
```

行为说明：

- `PDF_PARSE_BACKEND=auto`：先试 MinerU，失败回退本地 PyMuPDF
- `MINERU_PROXY_MODE=direct`：只让 MinerU 直连，其他模型和 HuggingFace 继续走代理
- Web 端“清空书架”会删除知识文件和当前知识向量，但 `data/chroma_db` 目录本身可能保留为空数据库目录

## Web 使用方式

1. 先输入主题，系统可能先做主题确认和学前小测
2. 正式流程按“讲解 -> 出题 -> 作答 -> 评估”推进
3. 中途如果只想问当前卡点，直接输入问题即可
4. 临时问题回答后，页面会出现“回到主线 / 继续追问”确认卡
5. 选择“回到主线”后，会回到刚才那一道题，而不是重新开始

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
cd /home/haizi/ai-tutor-agent
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
