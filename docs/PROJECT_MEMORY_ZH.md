# 项目记忆文档（持续维护）

最后更新：2026-03-06

这份文档是项目当前状态的长期记忆，不是一次性的交接稿。它的作用是：

1. 记录项目已经做了什么。
2. 明确当前主干真正完成到哪里。
3. 记录还没做完的目标与技术债。
4. 给后续协作者一个统一的“当前事实来源”。

如果后续有人修改了核心流程、状态结构、公开接口、前端交互、模型配置方式或验证结论，这份文档必须同步更新。

## 1. 项目目标

项目定位：动态自适应伴学多智能体系统。

核心目标不是做一个通用聊天机器人，而是做一个有闭环、有记忆、有前测、有画像、有动态回炉的伴学系统。

当前主线目标：

1. 先确认用户到底要学什么。
2. 先摸底，而不是直接讲。
3. 根据前测生成学习画像。
4. 进入 Tutor -> Tester -> Evaluator 的闭环。
5. 根据评估结果决定通过还是回炉。
6. 支持历史恢复、本地知识检索和多模型切换。

## 2. 当前主干快照

截至 2026-03-06，主干版本已经从早期 CLI MVP 演进为：

- `Web UI + FastAPI + SSE`
- `前测 + 规则化画像`
- `Tutor / Tester / Evaluator` 教学闭环
- `SQLite` 历史恢复
- `RAG-Lite`
- `多厂商聊天档案`
- `本地配置页`
- `有限闲聊 + 系统问答 + 学习入口分流`

当前已经不是“只有想法的项目”，而是一个可以启动、可以演示、可以继续协作开发的可运行原型。

## 3. 已完成里程碑

### 3.1 底层架构

已完成：

1. 从单文件脚本重构为分层结构：
   - `core`
   - `nodes`
   - `orchestration`
   - `infrastructure`
   - `application`
   - `interfaces`
2. 节点 I/O 已解耦，统一走 `EventSink / AnswerProvider / KnowledgeProvider`。
3. LangGraph 状态机已稳定为多阶段流转，而不是单轮问答。

### 3.2 学习流程

已完成：

1. 入口意图分流：
   - 学习主题
   - 系统问题
   - 轻闲聊
2. 学习主题确认：
   - 不会把 `你好 / 额 / 在吗` 直接当学习主题
   - 增加候选主题确认步骤
3. 学前测评：
   - 生成题目
   - 暂停等待提交
   - 恢复继续执行
4. 规则化画像：
   - 固定 6 维
   - 自评与客观得分分开
   - LLM 负责解释，不再直接自由打分
5. Tutor -> Tester -> Evaluator 闭环：
   - 及格结束
   - 不及格回 Tutor 重讲

### 3.3 Web 与恢复能力

已完成：

1. FastAPI Web API
2. SSE 实时事件流
3. 历史会话读取 / 删除 / 恢复
4. 对“未确认主题的旧会话”做了特殊恢复处理：
   - 不再错误自动 resume
   - 新一句话会被当成新的用户回合处理

### 3.4 配置与模型

已完成：

1. 聊天档案：
   - `gemini`
   - `qwen`
   - `deepseek`
   - `openai`
   - `minimax`
   - `glm`
   - `custom`
2. 本地配置页：
   - 选择厂商
   - 选择模型
   - 填对应 API Key
3. 已知厂商自动匹配：
   - `provider`
   - `base_url`
   - 默认模型
4. 本地配置接口已改为脱敏返回，不再把完整 API Key 原样发给前端。

### 3.5 RAG

已完成：

1. 本地知识文件注入
2. 文本切块
3. 向量化
4. Top-K 检索
5. Tutor 注入检索结果

当前默认推荐仍是 `RAG-Lite`，而不是重型向量平台。

### 3.6 前端工程

已完成：

1. `frontend/index.html` 不再承载所有前端逻辑
2. 样式已拆到 `frontend/assets/styles.css`
3. 脚本已拆到：
   - `frontend/assets/js/state.js`
   - `frontend/assets/js/ui.js`
   - `frontend/assets/js/config.js`
   - `frontend/assets/js/history.js`
   - `frontend/assets/js/session.js`
   - `frontend/assets/app.js`

这意味着前端已经进入“可继续模块化”的状态，不再是单文件堆积。

## 4. 当前真实可运行闭环

当前可以稳定跑通的闭环是：

1. 用户进入网页。
2. 输入内容。
3. 入口判断：
   - 学习
   - 系统问题
   - 轻闲聊
4. 若是学习主题：
   - 候选主题确认
   - 学前测评
   - 提交测评
   - 生成画像
   - Tutor -> Tester -> Evaluator
   - pass / fail 回路
5. 过程中支持：
   - 历史恢复
   - 本地知识库检索
   - 聊天档案切换

## 5. 当前验证结论

截至最后一次整理，已经验证：

### 5.1 静态验证

1. `python -m py_compile $(rg --files -g '*.py')` 通过
2. 前端脚本 `node --check` 通过

### 5.2 测试验证

1. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
2. 当前结果：`34 passed`

### 5.3 真实启动探活

已验证：

1. Web 服务可启动
2. `/api/health` 可返回
3. `/` 首页可返回
4. `/api/config/local` 可返回
5. Qwen 配置已能被正确识别为已配置
6. Qwen key 在接口里只显示脱敏结果，不再暴露完整值

### 5.5 当前运行条件说明

当前运行条件应准确理解为：

1. 聊天模型必须能访问你所选厂商的 API
2. 如果使用 `EMBEDDING_PROVIDER=local`，第一次启动可能需要下载 HuggingFace 模型
3. 代理不是总是必须，但在受限网络下通常必须配置
4. 运行与代理说明统一以 `docs/RUNBOOK_ZH.md` 为准

### 5.4 已特别修复的交互问题

已修复：

1. 旧会话恢复时把系统问题误当学习主题摘要
2. 未确认主题的旧会话被错误自动 resume
3. 在旧会话里继续输入系统问题时，新输入被旧状态吞掉
4. 本地配置接口把完整 key 回传给前端

## 6. 当前目录判断

当前目录已经整理到“可扩展、可协作”的状态。

### 6.1 源码目录

- `ai_tutor_agent/core/`: 契约、状态、事件
- `ai_tutor_agent/nodes/`: 单节点逻辑
- `ai_tutor_agent/orchestration/`: 图和路由
- `ai_tutor_agent/infrastructure/`: LLM / 检索 / checkpoint
- `ai_tutor_agent/application/`: 会话流程入口
- `ai_tutor_agent/interfaces/`: API / CLI / SSE

### 6.2 前端目录

- `frontend/index.html`: 页面骨架
- `frontend/assets/styles.css`: 样式
- `frontend/assets/js/`: 逻辑模块
- `frontend/assets/app.js`: 前端启动入口

### 6.3 运行态目录

- `data/tutor_memory.db*`
- `data/knowledge/*`

这些属于运行数据，不属于源码，不应提交。

## 7. 当前还没完成的事

这部分不是“已经坏了”，而是“还没做到长期产品级”。

### 7.1 仍需补的能力

1. 配置页“测试连接”
   - 验证 key 是否有效
   - 模型是否有权限
   - 网络或代理是否有问题
2. 多厂商模型目录实时同步
   - 现在是后端静态维护，不是在线拉取
3. 更细粒度的前端组件化
   - 当前是职责拆分，还不是组件化工程
4. 更强的 RAG 持久化能力
   - 目前仍是轻量方案

### 7.2 技术债

1. Python 仍是 3.9，Google 相关依赖会持续告警
2. 各厂商模型“真实在线调用验证”还没有全部做一遍
3. `custom` 模式仍然偏开发者兜底，不适合普通用户

## 8. 当前建议优先级

后续最值得做的顺序：

1. 增加“测试连接”接口和前端按钮
2. 继续优化模型选择和配置页交互
3. 优化前端体验提示和历史回放
4. 继续增强 RAG 可维护性

## 9. 协作者最短阅读路径

新成员建议按这个顺序读：

1. `README.md`
2. `docs/PROJECT_MEMORY_ZH.md`
3. `docs/RUNBOOK_ZH.md`
4. `docs/ARCHITECTURE.md`
5. `docs/PROJECT_GUIDE_ZH.md`
6. `docs/ROLE_ONBOARDING_ZH.md`
7. `docs/REPO_HYGIENE_ZH.md`

## 10. 更新规则

以后每次有人改了下面任一项，必须同步更新本文件：

1. 学习流转阶段
2. `AgentState`
3. 公开 API
4. 聊天档案与配置方式
5. 前端交互主路径
6. 验证结果
7. 当前优先目标

建议更新方式：

1. 修改“当前主干快照”
2. 修改“已完成里程碑”
3. 修改“当前验证结论”
4. 修改“当前还没完成的事”
5. 更新顶部日期
