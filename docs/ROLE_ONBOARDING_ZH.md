# 角色上手清单（发给协作者）

## 0. 所有人先做

1. 阅读顺序：
   - `README.md`
   - `docs/PROJECT_GUIDE_ZH.md`
   - `docs/ARCHITECTURE.md`
   - `CONTRIBUTING.md`
2. 本地启动与验证：
   - `pip install -e .` 或 `pip install -r requirements.txt`
   - `cp .env.example .env` 并填入 `GOOGLE_API_KEY`
   - `pytest -q`
3. 开发规范：
   - 新功能走分层目录，不改兼容层（`agents/`、`adapters/`、根级转发文件）。
   - 每个 PR 只做一个主题。

## 1. 人员A（后端编排）

### 先看哪些文件

- `ai_tutor_agent/core/*`
- `ai_tutor_agent/nodes/*`
- `ai_tutor_agent/orchestration/*`
- `tests/test_routing.py`, `tests/test_state.py`

### 第一阶段任务

1. 固化 `AgentState` 和事件字段契约。
2. 增加整链路集成测试（mock LLM，覆盖 pass/fail 两条路径）。
3. 输出“状态/事件变更说明模板”。

### 完成标准

1. `pytest -q` 全绿。
2. 新增集成测试可稳定复现路由行为。
3. 契约文档可供 API/前端直接消费。

## 2. 人员B（API）

### 先看哪些文件

- `ai_tutor_agent/application/session.py`
- `ai_tutor_agent/interfaces/sse.py`
- `ai_tutor_agent/core/events.py`
- `ai_tutor_agent/core/ports.py`
- `ai_tutor_agent/interfaces/api/README.md`

### 第一阶段任务

1. 在 `ai_tutor_agent/interfaces/api/` 实装 FastAPI。
2. 先落地 3 个端点：
   - `GET /health`
   - `POST /sessions`
   - `GET /sessions/{id}/stream`（SSE）
3. 使用 `CallbackEventSink` 推送事件流。

### 完成标准

1. curl 可发起会话并收到流式事件。
2. 端点错误码和输入校验可用。
3. 不改节点业务逻辑，只做接口适配。

## 3. 人员C（RAG）

### 先看哪些文件

- `ai_tutor_agent/infrastructure/llm.py`
- `ai_tutor_agent/nodes/tutor.py`
- `ai_tutor_agent/config.py`
- `docs/TEAM_PLAN_ZH.md`（RAG职责）

### 第一阶段任务（RAG-Lite）

1. 新建 `ai_tutor_agent/infrastructure/retrieval/`：
   - 文档切分
   - embedding
   - FAISS 检索 top-k
2. 在 Tutor 节点注入检索上下文。
3. 加一个开关（环境变量）控制是否启用 RAG。

### 完成标准

1. Tutor prompt 中可观察到检索片段注入。
2. 无 RAG 时系统行为不退化。
3. 给出 5-10 条样例问题的效果对比。

## 4. 人员D（前端 + 质量）

### 先看哪些文件

- `ai_tutor_agent/core/events.py`
- `ai_tutor_agent/interfaces/sse.py`
- `docs/PROJECT_GUIDE_ZH.md`（事件与流程）
- `tests/*`（当前质量基线）

### 第一阶段任务

1. 前端消费 SSE，渲染聊天流与评分卡片。
2. 根据 `assessment.result` 渲染雷达图。
3. 增加 GitHub Actions（至少 `pytest -q`）。

### 完成标准

1. 页面可实时显示 Tutor/Tester 流。
2. 评分事件可稳定驱动图表更新。
3. PR 自动跑测试并阻止失败合并。
