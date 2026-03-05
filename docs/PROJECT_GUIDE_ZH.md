# 项目全景与目录说明（中文）

## 1. 这个项目现在能做什么

当前系统是一个基于 LangGraph 的动态伴学闭环，已实现：

1. 多智能体闭环流程：`Tutor -> Tester -> Evaluator`。
2. 动态路由：评分达到阈值结束，不达标自动回到 Tutor 重讲。
3. 流式交互：Tutor 与 Tester 支持流式分片输出，响应快。
4. 结构化阅卷：Evaluator 输出并解析 JSON 评分结构（总分、逻辑分、概念分、反馈）。
5. 断点续学：按 `thread_id` 持久化到 SQLite，支持中断后恢复。
6. 事件化运行：节点不直接依赖终端输入输出，通过 `EventSink/AnswerProvider` 解耦，可复用于 API/SSE。

## 2. 一次完整学习会话的步骤

1. 启动 CLI（`python main.py`）。
2. 输入 `thread_id`。
3. 若命中历史状态：直接续学。
4. 若新会话：输入学习主题。
5. Tutor 讲解当前主题。
6. Tester 按讲解内容动态出题，用户作答。
7. Evaluator 结构化评分并给出错因。
8. Router 判断：
   - `pass`：结束当前闭环。
   - `fail`：带反馈回 Tutor，进入下一轮强化。

## 3. 文件夹职责（按分层）

### `ai_tutor_agent/core/`

- 纯核心契约层，不包含交付渠道逻辑。
- `events.py`：统一事件模型。
- `ports.py`：I/O 抽象协议（`EventSink`、`AnswerProvider`、`RuntimeContext`）。
- `state.py`：图状态结构。
- `text.py`：模型输出文本归一化工具。

### `ai_tutor_agent/nodes/`

- 单节点推理逻辑。
- `tutor.py`：讲解生成与流式事件。
- `tester.py`：出题与答案采集事件。
- `evaluator.py`：评分与反馈解析事件。

### `ai_tutor_agent/orchestration/`

- 图结构和路由规则。
- `workflow.py`：构建 LangGraph 工作流、挂载 checkpointer。
- `routing.py`：评分路由判定。

### `ai_tutor_agent/infrastructure/`

- 外部依赖接入层。
- `llm.py`：模型实例工厂。
- `checkpoint.py`：SQLite checkpointer 封装。

### `ai_tutor_agent/application/`

- 用例层（跨节点流程调度）。
- `session.py`：学习会话入口逻辑（新会话/续学）。

### `ai_tutor_agent/interfaces/`

- 交付接口层。
- `cli/`：终端适配。
- `sse.py`：SSE 数据帧格式化。
- `api/`：HTTP/WebSocket 预留位（待开发）。

### `ai_tutor_agent/adapters/`、`ai_tutor_agent/agents/` 和根级 `events.py` 等

- 兼容层（历史路径转发）。
- 作用是避免旧分支立即失效，便于协作者渐进迁移。

### `data/`

- 运行态数据目录（默认数据库路径：`data/tutor_memory.db`）。
- 不参与代码版本管理（数据库文件被 `.gitignore` 忽略）。

### `tests/`

- 单元与兼容测试（路由、状态、SSE、兼容导出）。

## 4. 当前已完成 vs 待完成

已完成：

1. CLI 闭环学习流程。
2. 评分驱动路由回环。
3. 事件总线与 SSE 预留。
4. 模块分层与兼容迁移机制。

待完成（高优先级）：

1. `interfaces/api/` 的 FastAPI + SSE/WebSocket 实装。
2. RAG 检索接入（Tutor 讲解前增加检索增强）。
3. 评估器多模型切换与 A/B 评测。
4. 前端会话界面 + 雷达图数据消费。
