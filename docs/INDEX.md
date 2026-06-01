# AI Tutor Agent 文档索引

更新时间：2026-05-29

## 权威入口（当前状态与下一步）

| 文档 | 用途 | 何时读 |
|------|------|--------|
| `docs/current-status-and-usage.md` | 当前完成情况、使用方式、自检命令；包含错题本、题目答疑、客观题复盘的现状与边界 | 首次了解项目、汇报当前状态 |
| `docs/next-iteration-plan.md` | 下一步迭代计划、任务清单 | 制定工作计划、验收标准 |
| `docs/plans/2026-04-30-interaction-artifact-validation-contract.md` | 交互卡片/历史恢复三层验收契约 | 做前端验收、浏览器测试时 |

## 功能说明文档

| 文档 | 用途 |
|------|------|
| `docs/question-bank-mainflow-homework-integration.md` | 题库加工并入主流程与作业题调用 |
| `docs/knowledge-map-runtime-assets.md` | 运行资产同步、图谱 B 说明 |
| `docs/ai-tutor-summary.md` | 已完成改进详细说明（知识图谱、向量库、教学改进） |
| `docs/agent-capability-structure.md` | 智能体能力结构草案（独立草案，未接入生产） |

## 当前设计文档

| 文档 | 内容 |
|------|------|
| `docs/plans/2026-05-28-learning-plan-design.md` | 学习路径与节点学习分离设计（v1） |
| `docs/plans/2026-05-29-learning-path-algorithm-v2.md` | 学习路径 v2 算法设计（ZPD 驱动 + 拓扑约束） |
| `docs/plans/2026-05-29-learning-path-v2-implementation-plan.md` | 学习路径 v2 实施计划 |
| `docs/plans/2026-05-29-teaching-optimization-plan.md` | 教学能力优化计划（待审核） |

## 历史计划（已归档）

| 文档 | 内容 |
|------|------|
| `docs/graph-mainflow-task-plan.md` | 图谱 2.2 与主流程重构任务计划（已被 current-status 取代） |
| `docs/plans/2026-04-28-strict-kg-mastery-mainflow-plan.md` | 严格主流程设计长计划 |
| `docs/plans/2026-04-27-main-learning-flow-redesign.md` | 主学习流程重设计 |

## 历史报告（已归档）

| 文档 | 内容 |
|------|------|
| `docs/reports/2026-04-28-langgraph-mainflow-completion-report.md` | 2026-04-28 主流程完成报告 |
| `docs/reports/2026-04-28-langgraph-final-closure-report.md` | 2026-04-28 最终闭合报告（88 项聚焦回归） |

## 归档资料

| 目录 | 内容 |
|------|------|
| `docs/archive/a2-control-theory/` | 历史 Graph A / A2 资料（source-notes、viewer） |
| `docs/archive/README.md` | 归档说明 |

## 其他

| 文件 | 说明 |
|------|------|
| `docs/GEMINI_CONTEXT.md` | Gemini 上下文（已 gitignore，本地生成） |

## 阅读顺序建议

1. `README.md` — 项目概述
2. `docs/current-status-and-usage.md` — 当前状态
3. `docs/next-iteration-plan.md` — 下一步计划
4. 按需阅读功能说明文档
5. 历史计划/报告仅作溯源参考
