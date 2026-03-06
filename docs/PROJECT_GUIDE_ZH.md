# 项目全景与目录说明（中文）

## 1. 项目现在到底能做什么

当前系统已经是一个可运行的 Web 伴学系统，而不是早期的单纯 CLI Demo。

它目前可以：

1. 区分用户是在开始学习、问系统问题，还是只想简单闲聊。
2. 对学习主题做二次确认，避免把“你好”“额”误当成学习内容。
3. 生成学前测评表单并暂停，等待前端提交答案。
4. 用规则化方式生成能力画像雷达图。
5. 进入 Tutor -> Tester -> Evaluator 闭环，并按评分决定通过或回炉。
6. 记录历史会话并按 `thread_id` 恢复。
7. 上传本地知识文件，做轻量 RAG 检索增强。
8. 在网页端切换不同聊天模型档案并保存到本机 `.env`。

## 2. 一次完整会话的真实步骤

1. 用户输入一句话。
2. `intake_router` 先判断意图：
   - 学习主题
   - 系统问题
   - 轻闲聊
3. 如果是系统问题：先回答，再等用户下一条输入。
4. 如果是轻闲聊：短聊一句，再等用户下一条输入。
5. 如果是学习主题：
   - `greeting` 提取候选主题
   - `topic_confirmer` 让用户确认主题
   - 生成学前测评
   - 用户提交测评
   - 生成规则化画像
   - 进入教学闭环

## 3. 目录职责（按现在的真实结构）

### `ai_tutor_agent/core/`

放核心契约，不能有具体交付逻辑。

- `events.py`：统一事件结构
- `ports.py`：输入输出协议
- `state.py`：LangGraph 状态结构
- `text.py`：文本归一化工具

### `ai_tutor_agent/nodes/`

放单一职责节点。

- `intake.py`：入口意图判断
- `meta.py`：系统问题回答
- `smalltalk.py`：轻闲聊
- `greeting.py`：学习主题识别
- `topic_confirm.py`：主题确认
- `assessment.py`：学前测评与画像
- `tutor.py`：讲解
- `tester.py`：出题
- `evaluator.py`：评分与反馈

### `ai_tutor_agent/orchestration/`

放图结构和路由。

- `workflow.py`
- `routing.py`

### `ai_tutor_agent/infrastructure/`

放外部依赖和实现细节。

- `llm.py`
- `checkpoint.py`
- `retriever.py`

### `ai_tutor_agent/application/`

放会话用例层。

- `session.py`

### `ai_tutor_agent/interfaces/`

放交付层。

- `api/`：FastAPI + Web 路由
- `cli/`：终端调试适配
- `sse.py`：SSE 格式化

### `data/`

放运行时数据，不是源码。

- `tutor_memory.db`
- `knowledge/` 本地知识资料

这些默认都不应提交到远端仓库。

## 4. 当前哪些文档最重要

协作者推荐阅读顺序：

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PROJECT_GUIDE_ZH.md`
4. `docs/ROLE_ONBOARDING_ZH.md`
5. `docs/REPO_HYGIENE_ZH.md`
6. `CONTRIBUTING.md`

## 5. 当前哪些点已经不是待开发，而是已实现

以下内容已经不是“未来规划”，而是已经落在代码里：

1. FastAPI API 模块
2. 会话历史读取/删除/恢复
3. 前测表单与画像生成
4. 本地配置页
5. 多厂商聊天档案目录

## 6. 还需要持续优化的点

1. 前端已完成 HTML/CSS/JS 拆分，当前脚本位于 `frontend/assets/js/`，后续仍应继续细分职责和组件边界。
2. 各厂商模型目录目前是后端维护的静态目录，不是实时联网拉取。
3. `custom` 模式只适合高级用户，不应该作为主要使用路径。
4. 需要增加“测试连接”能力，明确提示 key 无效、模型不可用或网络错误。
