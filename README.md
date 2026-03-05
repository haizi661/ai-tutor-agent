# AI Tutor Agent

动态自适应伴学多智能体系统（MVP）。当前版本基于 LangGraph 构建 `Tutor -> Tester -> Evaluator` 闭环，支持打分路由、重修干预和 SQLite 断点续传。

详细分层设计见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## Quick Start

1. 安装依赖

```bash
cd /home/haizi/ai-tutor-agent
# 方式 A（推荐，按 pyproject 安装）
pip install -e .

# 方式 B（requirements）
# pip install -r requirements.txt
```

2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入真实 GOOGLE_API_KEY
```

3. 启动 CLI

```bash
python main.py
```

4. 运行测试

```bash
pytest -q
```

## 当前目录结构

```text
ai-tutor-agent/
├── ai_tutor_agent/
│   ├── application/
│   │   └── session.py
│   ├── config.py
│   ├── core/
│   │   ├── events.py
│   │   ├── ports.py
│   │   ├── state.py
│   │   └── text.py
│   ├── infrastructure/
│   │   ├── checkpoint.py
│   │   └── llm.py
│   ├── interfaces/
│   │   ├── api/
│   │   │   └── README.md
│   │   ├── cli/
│   │   │   ├── adapter.py
│   │   │   └── app.py
│   │   └── sse.py
│   ├── nodes/
│   │   ├── evaluator.py
│   │   ├── tester.py
│   │   └── tutor.py
│   ├── orchestration/
│   │   ├── routing.py
│   │   └── workflow.py
│   ├── adapters/            # 兼容层
│   ├── agents/              # 兼容层
│   ├── cli.py               # 兼容层
│   ├── events.py            # 兼容层
│   ├── ports.py             # 兼容层
│   ├── routing.py           # 兼容层
│   ├── sse.py               # 兼容层
│   ├── state.py             # 兼容层
│   ├── text.py              # 兼容层
│   └── workflow.py          # 兼容层
├── docs/
│   └── ARCHITECTURE.md
├── .env.example
├── .gitignore
├── main.py
└── pyproject.toml
```

## 协作约定

- 机密信息只放 `.env`，不要写入代码或明文文本文件。
- 所有新功能优先落在 `ai_tutor_agent/` 包内，`main.py` 只保留启动入口。
- 新开发默认使用分层路径：`core -> nodes -> orchestration -> application -> interfaces`。
- 节点职责保持单一：`nodes/tutor.py` 负责讲解，`nodes/tester.py` 负责出题与收答，`nodes/evaluator.py` 负责结构化评分。
- 节点禁止直接 `print/input`，统一通过 `RuntimeContext` 注入的 `EventSink/AnswerProvider` 与外部交互。
- API 层复用 `interfaces/sse.py` 把 `AgentEvent` 转成 SSE 数据帧返回前端。
- `core/ports.py` 提供 `CallbackEventSink`，可直接把事件推入 FastAPI 流式响应。
- 如需历史分支兼容，继续可用 `ai_tutor_agent.<旧路径>` 导入；新代码请不要再依赖兼容层。

## 标准事件接口（SSE 预留）

- `node.start`：节点开始执行。
- `node.stream`：流式分片（Tutor/Tester）。
- `node.complete`：节点执行完成。
- `answer.received`：用户回答已接收。
- `assessment.result`：结构化评分输出。
- `route.decision`：路由决策（`pass/fail`）。
- `session.info/session.warning`：会话级提示。

## 分层说明

- `core`：契约与状态模型，必须无 I/O 副作用。
- `nodes`：单节点推理逻辑。
- `orchestration`：图拓扑和路由规则。
- `application`：跨节点会话流程。
- `interfaces`：CLI/API/SSE 适配层。
- `infrastructure`：LLM 与持久化等外部依赖。

## 下一步建议

- 接入 RAG 检索层：在 `infrastructure/` 新增检索客户端，并在 `nodes/tutor.py` 注入召回结果。
- 引入 API 层：在 `interfaces/api/` 新增 FastAPI，复用 `application/session.py + interfaces/sse.py`。
- 拆分存储层：将学习画像与题目历史落到独立表，降低 checkpoint 二进制调试成本。
