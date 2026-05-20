# 题库加工并入主流程与作业题调用说明

更新时间：2026-05-19  
项目根目录：本文所有路径、命令、接口示例均以仓库根目录为基准，统一使用项目内相对路径。

## 1. 文档目的

本文说明两项已经落地并联动的能力：

1. 题库加工功能如何从原始 `error_correction` 分步工作流，收束为适合伴学智能体使用的“题库加工工作台”。
2. 学习主线在结束本轮学习时，如何不再让大模型凭空出作业，而是优先从加工后的题库中抽取 1-2 道相关题目作为作业。

本文侧重当前实现，不讨论历史旧方案的完整演进过程。

## 2. 一句话结论

当前系统已经形成下面这条闭环：

```text
上传 PDF
-> 在题库加工工作台选择单份 PDF 作为加工对象
-> OCR
-> AI 分割题目
-> 保存到 runtime 题库
-> 主线学习结束时进入 homework_generator
-> 优先从 runtime 题库按当前学习上下文抽取 1-2 道相关题
-> 以前端独立作业题卡形式展示
```

其中 runtime 题库存储路径是：

```text
data/error_correction_runtime/question_bank/questions.json
```

这份题库既服务“已有题库”页面，也服务学习结束后的作业抽题。

## 3. 背景与改造目标

### 3.1 原始问题

最初系统里有两条相互割裂的链路：

1. 题库加工链路偏向“工具页”，包含 OCR、分割结果等中间工作态，不适合直接挂到伴学主界面。
2. 作业链路虽然在主流程中已经闭合，但 `homework_generator` 默认更多依赖模型生成或旧本地题库，无法稳定复用新加工出来的题库题。

这会导致两个问题：

- 用户辛苦上传、加工好的 PDF 题目，不能自然进入主线作业流程。
- 学习结束时，作业题和本轮学习内容之间缺乏稳定、可追溯的题源关系。

### 3.2 当前改造目标

本轮改造的目标不是“单独做一个题库工具”，而是让题库成为主学习流程的一部分：

- 前端上，题库加工从复杂工具页收束为“工作台 / 已上传文件 / 已有题库”三视图。
- 数据上，加工后的题目沉淀为可复用的 runtime question bank。
- 主流程上，`continue_or_homework_selector -> homework_generator` 改为优先从 runtime question bank 抽题。
- 展示上，题库题作业不再只显示一段摘要，而要保留渲染后的题面、图片、标签和独立题卡结构。

## 4. 题库加工功能并入主流程的实现

## 4.1 前端交互目标

题库加工功能现在不再把 OCR 结果页、分割结果页暴露给用户当成主要入口，而是收束成：

- `工作台`
- `已上传文件`
- `已有题库`

对应入口位于：

- `frontend/index.html`
- `frontend/assets/js/error_correction.js`
- `frontend/assets/styles.css`

### 当前三视图职责

#### 工作台

只承担主流程说明与关键入口：

- 上传 PDF
- 开始执行
- 查看已有题库
- 展示当前加工对象、当前 OCR/模型配置摘要

#### 已上传文件

只展示本批次上传的 PDF 清单，并支持：

- 查看文件
- 移除文件
- 指定“当前加工对象”

#### 已有题库

只展示已经入库的题库成品卡片，不再展示中间 OCR/分割工作态。

每道题：

- 相互独立
- 保留渲染后的题面
- 保留图片
- 保留知识标签
- 默认不在题库浏览时展示中间 LaTeX 垃圾文本或流程调试信息

## 4.2 单文件加工对象机制

为了解决“当前批次只能一起加工，不能只处理某一份 PDF”的问题，现在前后端都支持显式的单文件目标。

### 前端侧

前端本地状态新增：

- `selectedUploadFilename`

实现位置：

- `frontend/assets/js/error_correction.js`

核心行为：

1. 刷新工作台后，如果当前选中对象仍存在，则保留。
2. 如果当前对象不存在，则自动回退到第一份 PDF。
3. 在“已上传文件”中，用户可以点击“设为加工对象”切换目标 PDF。
4. `开始执行`、单独 `OCR`、单独 `分割`、保存入库，都会把这个文件名一并带到后端。

### 后端侧

`ErrorCorrectionService` 增加了按文件名筛选上传文件的逻辑：

- `ai_tutor_agent/infrastructure/error_correction_bridge.py`

关键方法：

- `_select_uploads(selected_filename)`

作用：

- 若未指定文件名，保留兼容行为，可取全部上传文件。
- 若指定文件名，只返回这一份 PDF。
- 若文件不存在，直接报错，避免误跑批次。

在此基础上，下面几个动作都已支持 `selected_filename`：

- `run_ocr(...)`
- `run_split(...)`
- `/api/error-correction/ocr`
- `/api/error-correction/split`

保存入库时还会把来源文件写入题目记录：

- `source_files`

这使得后续作业题、题库题都能追溯来源 PDF。

## 4.3 题库存储结构

加工后的 runtime 题库存储在：

```text
data/error_correction_runtime/question_bank/questions.json
```

相关资源文件存储在：

```text
data/error_correction_runtime/question_bank/assets/
```

保存时做了两件关键事：

1. 题目图片、选项图片、引用图片会被持久化复制到 `question_bank/assets/<batch_id>/...`，避免清理工作台后资源丢失。
2. 知识标签会被标准化，优先级是：
   - `knowledge_tags`
   - `section_title`
   - `待补充知识板块`

对应实现位于：

- `ai_tutor_agent/infrastructure/error_correction_bridge.py`

这保证了“已有题库”页和主线作业题都能稳定显示标签与图片。

## 4.4 题库加工相关接口

### 工作台状态

```http
GET /api/error-correction/status
```

返回：

- 已上传文件
- 当前 OCR 预览
- 当前分割结果
- 工作台摘要
- OCR/LLM 配置能力

### OCR

```http
POST /api/error-correction/ocr
Content-Type: application/json

{
  "selected_filename": "paper-a.pdf"
}
```

作用：

- 只对指定 PDF 执行 OCR
- 返回页级预览、答案版式判断

### 分割

```http
POST /api/error-correction/split
Content-Type: application/json

{
  "confirmed_answer_layout": "mixed_inline",
  "selected_page_indices": [],
  "selected_filename": "paper-a.pdf"
}
```

作用：

- 只对指定 PDF 做 AI 分割

### 保存到题库

```http
POST /api/knowledge/question-bank
Content-Type: application/json

{
  "selected_ids": ["0", "1", "2"],
  "source_files": ["paper-a.pdf"]
}
```

作用：

- 把分割结果写入 runtime question bank
- 给每道题写入来源文件

## 5. 作业题改为调用题库的实现

## 5.1 真实主线入口

当前用户完成小测、并决定“今天先到这里”后，主流程路由是：

```text
objective_test_scorer
-> next_node_planner
-> continue_or_homework_selector
-> stop_today
-> homework_generator
```

关键文件：

- `ai_tutor_agent/orchestration/workflow.py`
- `ai_tutor_agent/nodes/continue_or_homework_selector.py`
- `ai_tutor_agent/nodes/homework_generator.py`

其中 `continue_or_homework_selector` 已显式支持下面这些自然语言触发：

- `今天不学了`
- `今天先到这里`
- `生成作业`
- `作业`
- `stop_today`

这保证用户直接输入“今天不学了，生成作业”时，也能进入正确分支。

## 5.2 runtime 题库接入点

学习主线运行时通过：

- `LocalQuestionBankProvider`

加载 runtime 题库：

- `ai_tutor_agent/infrastructure/question_bank.py`

关键方法：

- `list_runtime_question_bank_items()`

它会读取：

```text
data/error_correction_runtime/question_bank/questions.json
```

并把图片路径统一转成：

```text
/api/error-correction/assets/...
```

这样主流程里发作业时，前端可以直接访问这些图片资源。

## 5.3 作业题抽取策略

当前作业抽题逻辑集中在：

- `ai_tutor_agent/core/homework_bank.py`

### 抽题输入上下文

系统不会盲目随机选题，而是汇总以下信息做匹配：

- `current_node_id`
- `graph_anchor_id`
- 当前节点标题
- 当前学习目标
- 当前 topic / turn goal / topic focus
- 学生历史学习快照中的：
  - `wrong_nodes`
  - `visited_nodes`
  - `daily_learning_records`

也就是说，作业题不只是“匹配当前节点”，还会参考近期学过和错过的节点。

### 匹配方法

当前是“规则打分 + 可选 LLM 精筛”的组合：

1. 先根据当前节点、错题节点、最近学习节点，构造候选节点上下文。
2. 对 runtime question bank 中每道题按以下信息计算相关性：
   - `knowledge_tags`
   - `section_title`
   - 渲染后题干摘要
3. 如果当前运行时有可用 LLM，则让 LLM 只在候选题中挑最相关的 1-2 道。
4. 如果没有可用 LLM，则直接使用本地规则排序结果。

这和旧逻辑最大的区别是：

- LLM 不再直接凭空出题；
- LLM 只负责在“已有题库候选集”里做选择。

### 抽题结果格式

runtime question bank 题会被适配成主流程统一作业结构，保留：

- `content_blocks`
- `options`
- `option_images`
- `knowledge_tags`
- `source_refs`
- `media_refs`
- `source = processed_question_bank`

这样后续作业展示、恢复、批改都能沿用主流程已有结构。

## 5.4 回退策略

当前 `homework_generator` 的优先级是：

1. 优先尝试 runtime question bank
2. 若无可用题，再尝试旧本地作业题库 / 其他兜底源
3. 最后才退到模板化生成题

因此当前口径是：

- 新加工题库已经进入主线优先路径；
- 不是所有情况下都绝对只会使用 runtime question bank；
- 当 runtime question bank 没有匹配题时，系统仍允许降级，保证不会因为“题库为空”而直接无法出作业。

## 6. 题库题作业的前端展示方式

## 6.1 为什么之前会出现“格式乱、没图片、题目混在一起”

这部分之前遇到过两个层级的问题：

1. 后端已经生成了作业 HTML，但前端把它按普通文本流处理，导致结构丢失。
2. 前端 HTML sanitize 白名单过严，把题卡用到的 `<article>`、`<figure>` 等标签过滤掉了，导致图片和卡片结构被抹平。

现在已经统一处理为：

- 后端流式事件使用 `kind = homework_learning_html`
- 前端 `session.js` / `ui.js` 对这类内容按学习卡片 HTML 渲染
- sanitize 白名单允许题目卡片所需标签

相关文件：

- `ai_tutor_agent/nodes/homework_generator.py`
- `frontend/assets/js/session.js`
- `frontend/assets/js/ui.js`

## 6.2 当前展示结构

每次布置作业时，后端会渲染：

- 一个“今日作业”容器
- 若干个独立 `<article class="homework-item-card">`

每道题卡片内部包含：

- 作业题号
- 题目标题 / 题源 id
- 知识标签
- 题面内容块
- 题面图片
- 选项与选项图片

对来自 runtime question bank 的题目：

- 布置阶段默认隐藏参考答案区，避免一发作业就泄露答案
- 重点展示“完整题面 + 标签 + 图片 + 独立结构”

## 7. 数据流与关键文件总览

## 7.1 题库加工链

前端：

- `frontend/index.html`
- `frontend/assets/js/error_correction.js`
- `frontend/assets/styles.css`

后端接口：

- `ai_tutor_agent/interfaces/api/error_correction.py`
- `ai_tutor_agent/interfaces/api/knowledge.py`

后端服务：

- `ai_tutor_agent/infrastructure/error_correction_bridge.py`

runtime 存储：

- `data/error_correction_runtime/uploads/`
- `data/error_correction_runtime/results/`
- `data/error_correction_runtime/struct/`
- `data/error_correction_runtime/question_bank/questions.json`
- `data/error_correction_runtime/question_bank/assets/`

## 7.2 作业抽题链

主流程路由：

- `ai_tutor_agent/orchestration/workflow.py`
- `ai_tutor_agent/nodes/continue_or_homework_selector.py`

作业生成：

- `ai_tutor_agent/nodes/homework_generator.py`

题库题适配与筛选：

- `ai_tutor_agent/core/homework_bank.py`
- `ai_tutor_agent/infrastructure/question_bank.py`

会话恢复与历史显示：

- `ai_tutor_agent/interfaces/api/history.py`
- `frontend/assets/js/session.js`
- `frontend/assets/js/ui.js`

## 8. 当前用户可见行为

### 8.1 题库加工页

用户现在能看到的行为是：

1. 点击“题库加工”打开工作台。
2. 上传多份 PDF。
3. 在“已上传文件”里指定某一份 PDF 作为加工对象。
4. 点击“开始执行”。
5. 系统只处理当前选中的这 1 份 PDF。
6. 处理完成后，题目出现在“已有题库”。

### 8.2 主流程作业

用户现在能看到的行为是：

1. 完成当前节点小测。
2. 系统询问是继续学习还是今天先到这里。
3. 用户选择“今天不学了，生成作业”。
4. 系统优先从 runtime question bank 抽取 1-2 道相关题。
5. 页面显示为独立作业题卡，而不是一段混杂文本。

## 9. 验证方式

## 9.1 题库加工相关

本轮已验证的重点是：

- 前端脚本语法可通过：

```bash
node --check frontend/assets/js/error_correction.js
```

- 后端相关文件可通过编译检查：

```bash
python -m py_compile \
  ai_tutor_agent/interfaces/api/error_correction.py \
  ai_tutor_agent/interfaces/api/knowledge.py \
  ai_tutor_agent/infrastructure/error_correction_bridge.py
```

- API 回归测试可通过：

```bash
conda run -n dreamerv3 env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_error_correction_api.py
```

重点覆盖：

- `selected_filename` 是否从 `/ocr` 传入服务层
- `selected_filename` 是否从 `/split` 传入服务层
- `source_files` 是否从保存接口写入题库保存逻辑

## 9.2 主流程作业相关

题库作业调用相关的回归主要集中在：

- `tests/test_homework_generator.py`
- `tests/test_post_eval.py`
- `tests/test_next_node_and_continue_flow.py`
- `tests/test_history.py`
- `tests/test_homework_learning_ui_contract.py`

其中重点验证：

- `stop_today` 是否路由到 `homework_generator`
- `homework_generator` 是否优先选择 `processed_question_bank`
- 返回内容是否以 `homework_learning_html` 形式进入前端渲染链

## 9.3 应用健康检查

在本地 `dreamerv3` 环境中，推荐使用：

```bash
conda activate dreamerv3
python main.py
curl http://127.0.0.1:8000/api/health
```

健康返回应为：

```json
{"status":"ok"}
```

## 10. 已知边界与后续建议

### 10.1 当前已解决的问题

- 题库加工页已经收束成适合伴学主界面的形态。
- 单文件 PDF 加工对象已经支持。
- 加工后题目能进入 runtime question bank。
- 主线作业已经能优先从 runtime question bank 抽题。
- 作业展示已经支持独立题卡、图片和知识标签。

### 10.2 当前仍然存在的边界

- runtime question bank 的相关性匹配已经可用，但仍属于启发式方案，不是完整的学习诊断式编排。
- 当 runtime question bank 为空或匹配不足时，系统仍可能回退到旧本地题库或模板题，这是当前设计上的容错行为。
- 题库加工后的知识标签目前依赖已有字段和回退策略，尚未建立更严格的课程章节标准化体系。
- 浏览器端真实 E2E 仍建议继续补自动化覆盖，尤其是“上传多份 PDF -> 切换对象 -> 开始执行 -> 入库 -> 主流程抽题”的整链回归。

### 10.3 下一步建议

1. 给 runtime question bank 增加更稳定的章节 / 节点映射字段，而不只依赖文本匹配。
2. 补一条浏览器级 E2E，用真实页面验证“单文件加工 + 主线作业抽题”整链。
3. 后续如果 runtime question bank 足够丰富，可以进一步收紧回退逻辑，减少非题库来源的作业题占比。
4. 如果要做运营或教学追踪，建议把“题库题被哪位学生在哪个节点被抽为作业”的记录单独结构化落库。

## 11. 推荐阅读顺序

如果后续要继续维护这条能力链，建议按下面顺序阅读代码：

1. `frontend/assets/js/error_correction.js`
2. `ai_tutor_agent/interfaces/api/error_correction.py`
3. `ai_tutor_agent/infrastructure/error_correction_bridge.py`
4. `ai_tutor_agent/infrastructure/question_bank.py`
5. `ai_tutor_agent/core/homework_bank.py`
6. `ai_tutor_agent/nodes/homework_generator.py`
7. `ai_tutor_agent/orchestration/workflow.py`

这条顺序基本对应：

```text
前端工作台
-> OCR/分割/入库接口
-> runtime 题库存储
-> 主流程题库读取
-> 主流程作业抽题
-> 作业题卡展示
-> 工作流路由
```
