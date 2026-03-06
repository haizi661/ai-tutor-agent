# AI Developer Guide

这份文档给参与本项目的 AI 编程助手使用。目标不是描述历史版本，而是准确反映当前主干实现。

## 1. 当前系统定位

本项目是一个动态伴学系统，而不是通用聊天机器人。它支持：

- 有限闲聊
- 系统问题回答
- 学习主题确认
- 学前测评与规则化画像
- Tutor / Tester / Evaluator 闭环
- 历史恢复
- RAG-Lite
- 多厂商聊天档案

## 2. 当前真实流转

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

## 3. 分层约束

- `core/`: 契约与状态，禁止具体 I/O。
- `nodes/`: 单节点逻辑，职责必须单一。
- `orchestration/`: 图组装与条件路由。
- `infrastructure/`: LLM、检索、持久化等外部接入。
- `application/`: 会话级流程入口。
- `interfaces/`: CLI / API / SSE 适配层。

## 4. 绝对约束

1. 节点内禁止直接 `print()` / `input()`。
2. 所有外部交互都必须通过 `EventSink` / `AnswerProvider` / `KnowledgeProvider`。
3. `.env` 不能被提交。
4. 运行态数据库和知识文件不能混进 PR。
5. 改动 `AgentState`、事件类型或公开接口时，必须同步更新文档和测试。
6. 改动项目阶段、完成度、验证结论或下一步目标时，必须同步更新 `docs/PROJECT_MEMORY_ZH.md`。

## 5. 当前模型配置约定

普通使用路径：

- 选厂商
- 选模型
- 填 API Key

系统自动匹配：

- `provider`
- `base_url`
- 默认模型

支持的聊天档案：

- `gemini`
- `qwen`
- `deepseek`
- `openai`
- `minimax`
- `glm`
- `custom`

## 6. 当前优先改进方向

1. 增加“测试连接”接口，验证 key / model / network。
2. 优化前端模型切换和本地配置交互。
3. 在 `frontend/assets/js/` 目录下继续按 `config / history / session / ui` 细化前端职责。
4. 提升 RAG 的可维护性与持久化能力。
