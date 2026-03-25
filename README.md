# AI Tutor Agent

动态自适应伴学多智能体系统。当前主干版本已经从早期 CLI MVP 演进为一个可协作的 `Web UI + FastAPI + SSE + 前测画像 + RAG-Lite + SQLite 断点续传` 项目。

## 当前真实能力

当前系统已实现以下能力：

- 入口意图分流：区分 `学习主题`、`系统问题`、`轻闲聊`。
- 学习主题确认：不会把 `你好`、`额`、`在吗` 这类输入直接误判成知识主题。
- 学前测评：生成量表、暂停等待提交、恢复继续执行。
- 规则化画像：固定维度雷达图，不再由 LLM 自由打分。
- 教学闭环：`Tutor -> Tester -> Evaluator -> pass/fail 路由`。
- 历史恢复：按 `thread_id` 存入 SQLite，支持读取摘要、删除、恢复。
- RAG-Lite：本地知识文件切块、向量化、检索增强 Tutor。
- Web 本地配置：选择厂商、模型、API Key，写入本机 `.env`。
- 多厂商聊天档案：`gemini / qwen / deepseek / openai / minimax / glm / custom`。

当前学习流大致如下：

```text
intake_router
  -> meta_qa | smalltalk | greeting
  -> topic_confirmer
  -> assessment_generator
  -> user_profiler
  -> tutor
  -> tester
  -> evaluator
  -> pass | fail -> tutor
```

## Quick Start

1. 安装依赖

```bash
cd /home/haizi/ai-tutor-agent
pip install -e .
# 或者：pip install -r requirements.txt
```

2. 配置环境变量

```bash
cp .env.example .env
```

然后编辑 `.env`，至少填入你准备使用的一个厂商 API Key，例如：

- `GEMINI_API_KEY=...`
- `QWEN_API_KEY=...`
- `DEEPSEEK_API_KEY=...`
- `OPENAI_API_KEY=...`
- `MINIMAX_API_KEY=...`
- `GLM_API_KEY=...`

如果你不确定，最稳的起步配置是：

```env
CHAT_PROFILE=gemini
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
LOCAL_CONFIG_ENABLED=true
```

如果你的网络不能直接访问模型 API 或 HuggingFace，再补：

```env
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

注意：

1. 代理不是项目硬依赖
2. 但如果你所在网络无法直连模型厂商 API，或本地 embedding 第一次下载失败，就必须配置代理
3. 详细说明见 [docs/RUNBOOK_ZH.md](docs/RUNBOOK_ZH.md)

3. 启动 Web 端（默认入口）

```bash
python main.py
```

打开：`http://127.0.0.1:8000/`

4. 如需 CLI 调试

```bash
python main.py --cli
```

5. 如需 RAG 检索调试（结构化调试工具）

```bash
python main.py --debug-rag
# 或安装后使用: ai-tutor-debug-rag

# 单次检索并导出报告
python main.py --debug-rag --mode hybrid --once "PID 控制是什么" --export data/debug_rag_report.json

# 比较不同模式
python main.py --debug-rag --mode raw
python main.py --debug-rag --mode rerank --recall-k 10 --final-k 3

# 禁用 query rewrite
python main.py --debug-rag --no-rewrite
```

6. 运行测试

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

## 运行与代理说明

推荐启动方式：

```bash
python main.py
```

如果你需要自定义端口，请使用当前环境的 Python 启动：

```bash
python -m uvicorn ai_tutor_agent.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

不要优先使用系统裸命令 `uvicorn ...`，否则可能走错解释器环境。

如果你使用 `EMBEDDING_PROVIDER=local`：

1. 第一次启动可能会下载本地 embedding 模型
2. 第一次启动会比后续更慢
3. 如果网络受限，可能需要配置代理
4. 如果加载失败，当前版本会回退到无 RAG 模式

完整运行说明见：

- [docs/RUNBOOK_ZH.md](docs/RUNBOOK_ZH.md)

## Web API 概览

- `GET /api/health`：健康检查。
- `GET /api/config` / `POST /api/config`：读取与快速切换当前聊天档案。
- `GET /api/config/local` / `POST /api/config/local`：读取与写入本机 `.env`。
- `GET /api/history`：列出最近会话。
- `GET /api/history/{thread_id}`：读取状态摘要与可恢复信息。
- `DELETE /api/history/{thread_id}`：删除会话历史。
- `POST /api/start`：启动新会话。
- `POST /api/sessions/{thread_id}/resume`：恢复暂停会话。
- `GET /api/stream?thread_id=...`：SSE 事件流。
- `POST /api/answer`：提交普通输入。
- `POST /api/submit_assessment`：提交学前测评答案。
- `POST /api/confirm_topic`：确认或改写候选学习主题。
- `POST /api/upload`：上传知识库文件。
- `GET /api/knowledge`：查看知识库状态。

## 目录结构

```text
ai-tutor-agent/
├── ai_tutor_agent/
│   ├── application/
│   ├── core/
│   ├── infrastructure/
│   ├── interfaces/
│   │   ├── api/
│   │   └── cli/
│   ├── nodes/
│   └── orchestration/
├── data/
│   ├── .gitkeep
│   └── knowledge/
│       └── .gitkeep
├── docs/
├── frontend/
├── tests/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── AI_DEVELOPER_GUIDE.md
├── pyproject.toml
└── requirements.txt
```

## 上传与仓库卫生

以下内容不要提交到远端仓库：

- `.env`
- `data/*.db`
- `data/*.db-wal`
- `data/*.db-shm`
- `data/knowledge/*` 中的本地知识文件
- `*.log`
- `.pytest_cache/`、`__pycache__/`、`.coverage` 等缓存

提交前建议执行：

```bash
git status -sb
git diff
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

如果你在本地运行过服务，SQLite 可能生成 `tutor_memory.db-wal` / `tutor_memory.db-shm`，它们属于临时文件，不需要提交。

## 配置说明

### 1. 聊天模型档案

`CHAT_PROFILE` 控制当前启用的聊天档案，支持：

- `gemini`
- `qwen`
- `deepseek`
- `openai`
- `minimax`
- `glm`
- `custom`

普通使用建议通过网页“本地配置”页选择：

1. 厂商
2. 模型
3. 对应 API Key

然后让系统自动匹配 `provider` 与 `base_url`。

### 2. Custom 模式

`custom` 只用于手动模式。只有在你明确知道自己要接哪个兼容接口时，才需要自行填写：

- `LLM_PROVIDER`
- `OPENAI_API_BASE`
- `MODEL_NAME`
- 对应 API Key

### 3. RAG 配置

- `EMBEDDING_PROVIDER`：`local / google / openai / dashscope`
- `EMBEDDING_MODEL_NAME`
- `KNOWLEDGE_CHUNK_SIZE`
- `KNOWLEDGE_CHUNK_OVERLAP`
- `KNOWLEDGE_TOP_K`
- `CHROMA_DIR`
- `DASHSCOPE_API_KEY`（当 `EMBEDDING_PROVIDER=dashscope` 时需要）
- `MINERU_API_TOKEN`（可选，开启 MinerU PDF 解析时需要）
- `RAG_HYBRID_ENABLED`（默认 false，开启向量+BM25 混合召回）
- `RAG_MINERU_ENABLED`（默认 false，开启 MinerU 优先 PDF 解析）

小团队默认推荐：

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

RAG 2.0 推荐灰度顺序：

```env
RAG_HYBRID_ENABLED=true
RAG_MINERU_ENABLED=false
```

当你确认外部网络与配额稳定后，再开启：

```env
RAG_MINERU_ENABLED=true
MINERU_API_TOKEN=your_token_here
```

### 4. 本地配置页

网页里的“本地配置”页，本质上是把配置写回本机 `.env`。这适合：

- 个人本地开发
- 自己单机试验不同模型

不适合：

- 共享部署
- 多人共用一台服务端

如果你不想让网页修改 `.env`，可以设置：

```env
LOCAL_CONFIG_ENABLED=false
```

## 当前验证状态

本仓库当前应满足：

```bash
python -m py_compile $(rg --files -g '*.py')
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

## 必读文档

- [docs/RUNBOOK_ZH.md](docs/RUNBOOK_ZH.md)
- [docs/PROJECT_MEMORY_ZH.md](docs/PROJECT_MEMORY_ZH.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PROJECT_GUIDE_ZH.md](docs/PROJECT_GUIDE_ZH.md)
- [docs/TEAM_PLAN_ZH.md](docs/TEAM_PLAN_ZH.md)
- [docs/ROLE_ONBOARDING_ZH.md](docs/ROLE_ONBOARDING_ZH.md)
- [docs/GITHUB_NEWBIE_GUIDE_ZH.txt](docs/GITHUB_NEWBIE_GUIDE_ZH.txt)
- [docs/REPO_HYGIENE_ZH.md](docs/REPO_HYGIENE_ZH.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
