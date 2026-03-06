# 协作分工与推进方向（当前版）

## 当前阶段判断

当前项目已经完成了：

1. Web API 主链路
2. SSE 流式交互
3. 学前测评与画像
4. 历史恢复
5. 多厂商聊天档案
6. RAG-Lite

因此接下来的团队任务不再是“从零搭建 API”，而是继续做稳定性、体验和可维护性。

## 建议四人分工

### A 组：编排与状态机

职责：

1. 稳定 `intake -> confirm -> assessment -> tutor/tester/evaluator` 全流程。
2. 维护状态字段、路由条件和错误恢复。
3. 补充集成测试。

### B 组：API 与配置管理

职责：

1. 维护 `/api/config`、`/api/config/local`、`/api/history`、`/api/knowledge`。
2. 增加“测试连接”能力。
3. 管理模型目录、厂商映射、错误提示。

### C 组：RAG 与知识增强

职责：

1. 优化检索效果与召回质量。
2. 评估持久化向量库方案。
3. 给 Tutor 注入更稳定的检索上下文。

### D 组：前端与协作体验

职责：

1. 拆分 `frontend/index.html`。
2. 优化配置页、模型切换、历史恢复、阶段面板。
3. 补 CI、前端 smoke checks、PR 门禁。

## 推荐推进顺序

1. 先做稳定性：连接测试、错误提示、历史恢复体验。
2. 再做前端拆分和配置页优化。
3. 最后做 RAG 升级和多模型验证。

## 每次发版前必须确认

1. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` 通过。
2. `.env`、数据库、知识库原文件未进入 commit。
3. README 和关键文档已同步当前实现。
