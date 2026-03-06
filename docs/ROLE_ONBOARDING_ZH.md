# 角色上手清单（发给协作者）

## 0. 所有人先做

1. 阅读顺序：
   - `README.md`
   - `docs/PROJECT_MEMORY_ZH.md`
   - `docs/RUNBOOK_ZH.md`
   - `docs/ARCHITECTURE.md`
   - `docs/PROJECT_GUIDE_ZH.md`
   - `docs/REPO_HYGIENE_ZH.md`
   - `CONTRIBUTING.md`
2. 本地启动：
   - `pip install -e .`
   - `cp .env.example .env`
   - 选择一个你实际要用的厂商 key 填入 `.env`
   - 如果网络受限，按 `docs/RUNBOOK_ZH.md` 配置 `HTTP_PROXY / HTTPS_PROXY`
   - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
   - `python main.py`
3. 提交前：
   - 检查 `git status -sb`
   - 不要提交 `.env`、数据库、知识库文件、日志

## 1. 人员 A：后端编排

### 先看

- `ai_tutor_agent/core/*`
- `ai_tutor_agent/nodes/*`
- `ai_tutor_agent/orchestration/*`
- `tests/test_intake.py`
- `tests/test_assessment.py`

### 重点任务

1. 稳定 `AgentState` 与事件契约。
2. 管理学习流与路由逻辑。
3. 增加更强的整链路测试。

## 2. 人员 B：API / Web 后端

### 先看

- `ai_tutor_agent/interfaces/api/*`
- `ai_tutor_agent/interfaces/sse.py`
- `ai_tutor_agent/application/session.py`

### 重点任务

1. 完善配置接口、历史接口、知识库接口。
2. 增加“测试连接”接口，验证当前厂商、模型、key 是否可用。
3. 保持前端与 API 文档同步。

## 3. 人员 C：RAG / 检索

### 先看

- `ai_tutor_agent/infrastructure/retriever.py`
- `ai_tutor_agent/nodes/tutor.py`
- `ai_tutor_agent/config.py`

### 重点任务

1. 优化 chunk / top-k / 召回质量。
2. 评估是否从 `InMemoryVectorStore` 升级到持久化向量库。
3. 提供有/无 RAG 对比样例。

## 4. 人员 D：前端 / 体验

### 先看

- `frontend/index.html`
- `ai_tutor_agent/core/events.py`
- `docs/PROJECT_GUIDE_ZH.md`

### 重点任务

1. 在现有 `frontend/index.html + frontend/assets/js/` 基础上继续细分前端模块。
2. 优化模型选择和本地配置交互。
3. 优化历史恢复、阶段提示、错误提示。

## 5. 所有人共识

1. 新代码优先写在分层结构里，不再继续堆兼容层。
2. 改动 `AgentState`、事件格式、公开接口时，必须更新文档。
3. 本地运行态文件不要进 Git。
