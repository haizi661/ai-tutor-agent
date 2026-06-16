# AI Tutor Agent 文档索引

> **唯一说明书**: `docs/AI-TUTOR-AGENT-说明书.md` — 系统概述、启动、完整流程、算法、架构、视频、验证命令的单一入口。

## 当前文档

| 文档 | 用途 | 何时读 |
|------|------|--------|
| `docs/AI-TUTOR-AGENT-说明书.md` | **完整说明书**（系统概述→启动→14步流程→算法→架构→视频→验证） | 首次了解、汇报、新人上手 |
| `docs/next-iteration-plan.md` | 下一步迭代计划、任务清单、优先级 | 制定工作计划 |
| `docs/knowledge-map-runtime-assets.md` | 图谱 B 运行资产同步、检查命令 | 迁移环境、资产异常排查 |
| `docs/question-bank-mainflow-homework-integration.md` | 题库加工并入主流程的技术细节 | 修改题库 Provider 或作业生成 |
| `docs/learning-path-complete-flow.md` | 完整流程详细描述 + 学习路径生成算法 | 深入理解路径算法 |
| `docs/current-status-and-usage.md` | 详细完成情况、使用方式、自检命令 | 查看历史完成记录 |
| `docs/RUNBOOK_ZH.md` | 运维排障手册（代理配置、常见报错处理） | 启动失败、网络问题排查 |
| `CONTRIBUTING.md` | 贡献指南（分支命名、本地设置） | 首次参与开发 |

## 项目规范

| 文件 | 说明 |
|------|------|
| `CONTRIBUTING.md` | 分支命名规范、本地设置、PR 清单 |
| `requirements-dev.txt` | 开发依赖（pytest, ruff） |
| `ai_tutor_agent/interfaces/api/README.md` | API 接口说明与约束 |

## 设计文档

| 文档 | 内容 |
|------|------|
| `docs/plans/2026-04-30-interaction-artifact-validation-contract.md` | 交互卡片/历史恢复三层验收契约 |
| `docs/plans/2026-05-29-teaching-optimization-plan.md` | 教学能力优化计划（部分已实施） |

## 演示视频

| 文件 | 说明 |
|------|------|
| `scripts/phase_recordings/PHASE_VIDEOS.md` | 分阶段演示视频映射（8 阶段 + 完整视频） |
| `scripts/record_phases_v2.py` | 分阶段录制脚本 |
| `scripts/record_demo_flow.py` | 全流程录制脚本 (9 节点轮转) |
| `scripts/real_e2e_verify.py` | 真实 LLM API E2E 验证 |

## 历史文档（仅溯源）

`docs/reports/` 和 `docs/plans/` 下的旧计划/报告仅作历史参考，当前权威口径以说明书为准。
