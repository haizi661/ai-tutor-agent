# AI Tutor 三天工作总结

## 文档说明

这份总结基于当前分支已经落地的代码、目录结构和前后端联动结果整理，目的是让组内成员快速理解这三天到底做成了什么、系统现在能怎么工作、以及主要改动集中在哪些文件。

这份内容不按 commit 时间逐条罗列，而是按“功能演进阶段”来讲，因为这几天的改动不是零散补丁，而是在把课程数据、后端状态机、教学节点、前端界面和测试一起拉通。

---

## 一、先看结论：这三天把项目推进到了什么程度

### 初步总结

这三天最重要的结果，不是单独做了一个新页面，或者单独补了一条后端链路，而是把 AI Tutor 从“能对话、能回答问题”的原型，推进成了一个更接近真实学习产品的“图谱驱动伴学系统”。

现在这个系统已经具备以下几个关键特征：

1. 有课程骨架，不再只是资料堆。
   你把“自动控制原理”整理成了结构化课程图谱，节点之间有前置关系、学习目标、常见误区和后续路径。

2. 有学习起点判断，不再一上来就直接讲。
   系统会先识别主题，在必要时做主题确认，然后进入对话式摸底测评，确定用户当前适合从哪个节点开始学。

3. 有知识状态记录，不再只是临时聊天。
   测评结果和学习过程会沉淀到用户知识图谱里，系统能够知道哪些点已经掌握、哪些点在学习中、哪些点被跳过。

4. 有图谱驱动教学，不再只是依赖 RAG 回答。
   Tutor 的每轮输出已经和当前图谱节点、前置缺口、常见误区、下一步路径绑定在一起。

5. 有完整前端承接，不再只是“接口能跑”。
   前端已经能消费后端事件、呈现测评流程、显示图谱状态、恢复历史会话、管理资料和配置项。

6. 有测试兜底，不只是样式层改动。
   这次改动覆盖了课程图谱、状态字段、工作流、检索、历史恢复和多轮教学节点，并补了一轮对应测试。

### 一句话概括

这三天做成的核心，不是把 Tutor “变好看了”，而是把“课程结构、教学决策、用户状态、交互界面、资料证据链”整合成了一套可以持续带着用户往前学的系统。

---

## 二、整体演进脉络

### 阶段一：先把课程图谱和课程资料底座搭起来

第一阶段的重点，是先把“自动控制原理”从一堆散落资料，变成可以驱动教学的课程知识图谱。

这一阶段新增了完整的课程目录：

- [a2-control-theory/graph.json](../a2-control-theory/graph.json)
- [a2-control-theory/curriculum.json](../a2-control-theory/curriculum.json)
- [a2-control-theory/notes.jsonl](../a2-control-theory/notes.jsonl)
- [a2-control-theory/summary.json](../a2-control-theory/summary.json)
- [a2-control-theory/GRAPH_SCHEMA.md](../a2-control-theory/GRAPH_SCHEMA.md)
- [a2-control-theory/README.md](../a2-control-theory/README.md)
- [a2-control-theory/source-notes](../a2-control-theory/source-notes)

这一步的意义非常大，因为它不只是把课程内容“存起来”，而是建立了一个后续所有教学流程都能复用的数据底座：

1. 每个知识点不再只是标题或一段说明，而是带有节点标识、分类、前置、邻接、学习目标、必会点、常见误区和目标掌握层级。
2. 课程资料不再只是给检索系统抓文本，而是可以作为图谱节点的讲解依据和证据来源。
3. 后面测评为什么能决定起点、Tutor 为什么能围绕当前节点讲、为什么能做下一步推荐，本质上都建立在这套图谱数据上。

在这一阶段里，你还做了一个独立知识图谱 viewer：

- [a2-control-theory/viewer/index.html](../a2-control-theory/viewer/index.html)
- [a2-control-theory/viewer/app.js](../a2-control-theory/viewer/app.js)
- [a2-control-theory/viewer/style.css](../a2-control-theory/viewer/style.css)
- [a2-control-theory/viewer/data.js](../a2-control-theory/viewer/data.js)

这个 viewer 的意义不是“多了个可视化页面”这么简单，而是把知识图谱从后端内部结构，变成了一个人可以直接浏览、搜索、点击、跳转学习的界面。

另外，API 层已经把这个 viewer 挂到应用里：

- [ai_tutor_agent/interfaces/api/app.py](../ai_tutor_agent/interfaces/api/app.py)

现在系统会通过 `/knowledge-graph/a2` 提供这套图谱静态资源，这让图谱和主应用不再是分离的两套东西，而是一个整体产品中的两个视角。

### 阶段一的结果

这一阶段完成后，项目第一次拥有了“课程骨架”。

这意味着后续的主题确认、测评起点、教学锚定、下一步推荐、图谱联动 UI，都有了统一的数据源，不再需要靠 prompt 临时猜结构。

---

### 阶段二：把后端学习流程改成完整闭环

第二阶段的重点，是把原来偏单轮问答的 Tutor，改造成一个有状态、有阶段、有调度逻辑的学习流程。

首先，你扩展了全局状态定义：

- [ai_tutor_agent/core/state.py](../ai_tutor_agent/core/state.py)

这里新增了一批非常关键的状态字段，包括：

1. `assessment_state`：记录对话式测评当前处于哪个阶段、做到第几题、答案收集到什么程度。
2. `user_knowledge_graph`：记录用户对各个知识点的掌握状态，比如未开始、学习中、已掌握、已跳过。
3. `graph_anchor_id` / `graph_anchor_title` / `graph_anchor_filename`：表示当前教学锚点落在哪个图谱节点。
4. `graph_prerequisites` / `graph_common_errors` / `graph_next_steps`：把图谱中的前置、误区和推荐路径直接带进每轮教学上下文。
5. `affect_signals`：为后续教学策略切换提供情绪线索，比如受挫、自信、好奇、被动等。

这一步的意义是，系统开始拥有“持续状态”而不是“即时回答”。

然后，你把主工作流重新编排了：

- [ai_tutor_agent/orchestration/workflow.py](../ai_tutor_agent/orchestration/workflow.py)
- [ai_tutor_agent/orchestration/routing.py](../ai_tutor_agent/orchestration/routing.py)

当前工作流已经覆盖了较完整的学习闭环，大致包含：

1. 主题入口和收束。
2. 对话式测评生成与逐题测评。
3. 用户画像与知识图谱初始化。
4. Tutor 正式讲解。
5. 下一步选择。
6. 练习、评估、反馈和 post-eval 收束。
7. 中断问答后的主线回桥。

在入口阶段，你强化了主题收束和确认能力：

- [ai_tutor_agent/nodes/greeting.py](../ai_tutor_agent/nodes/greeting.py)
- [ai_tutor_agent/nodes/topic_confirm.py](../ai_tutor_agent/nodes/topic_confirm.py)

现在系统不再一上来就强行进入固定流程，而是会先判断用户到底是要开始一门课、继续已有主题，还是只是问一个点，然后在必要时弹出 topic confirmation。

在测评阶段，你重写了测评逻辑：

- [ai_tutor_agent/nodes/assessment.py](../ai_tutor_agent/nodes/assessment.py)

这里最重要的变化，是把原来更像一次性表单的测评改成了逐题对话式测评。它不是一次把题全扔给用户，而是按概念对分组推进，每组包含自评和客观题，再根据二者差异校准用户掌握度。

测评结束后，系统不只是输出一段“你大概会什么”的文字，而是直接把结果写入 `user_knowledge_graph`，并确定当前图谱起点。

为了让图谱真正参与决策，你新增了图谱服务：

- [ai_tutor_agent/core/graph_service.py](../ai_tutor_agent/core/graph_service.py)

这个模块的作用，是把图谱从“展示结构”变成“决策工具”。它目前支持的方向包括：

1. 前置链查询和前置缺口检测。
2. 当前节点后续路径查找。
3. 盲点检测。
4. 基于卡点和学习阶段给出复习或继续推进建议。

有了这个模块之后，系统在遇到用户卡住、准备切换节点、或者需要判断下一步时，不再只是让 LLM 凭感觉决定，而是能参考显式的图谱结构做判断。

在教学节点上，你强化了 Tutor：

- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)

现在 Tutor 不是泛泛回答问题，而是会把这些内容纳入当前 prompt 和输出逻辑：

1. 当前图谱锚点。
2. 前置知识和相邻节点。
3. 当前节点的学习目标、必会点和常见误区。
4. 用户当前知识图谱状态。
5. 情绪信号和教学语气策略。
6. 证据引用和资料支撑。

更重要的是，Tutor 输出里已经支持隐藏教学标记，例如：

1. `[MASTERY_ACHIEVED: ...]`
2. `[SKIPPED: ...]`
3. `[→ 下一概念: ...]`

这些标记不会原样给用户看，而是会被后端和前端识别成真实状态变化，驱动用户知识图谱和图谱提示更新。

你还补上了“讲完之后怎么办”的节点：

- [ai_tutor_agent/nodes/next_step.py](../ai_tutor_agent/nodes/next_step.py)

这一步很关键，因为很多 Tutor 系统的问题不在“讲得出来”，而在“讲完之后不会带路径”。

现在系统在一轮讲解后，已经能够决定：

1. 继续当前节点。
2. 先补前置。
3. 转到相关或下游节点。
4. 做一道练习题。
5. 做阶段性收束。

另外你还增强了两个重要配套节点：

- [ai_tutor_agent/nodes/interruption.py](../ai_tutor_agent/nodes/interruption.py)
- [ai_tutor_agent/nodes/affect.py](../ai_tutor_agent/nodes/affect.py)

前者解决“学生中途插问后如何回桥”，后者解决“学生明显受挫或很自信时，Tutor 是否需要切换策略”。

### 阶段二的结果

这一阶段完成后，系统已经不再是“用户问一句，模型答一句”的结构。

它开始具备一个伴学系统最核心的几件能力：

1. 知道用户大概在学什么。
2. 知道用户当前应该从哪里开始。
3. 知道用户学到哪一步了。
4. 知道卡住时要不要补前置。
5. 知道一轮讲完后应该怎么带用户往下走。

换句话说，系统开始拥有教学流程，而不仅仅是回答能力。

---

### 阶段三：把前端做成真正可用的学习产品

第三阶段的重点，是让前端真正承接后端状态机，而不是只把消息打印出来。

你重写了主界面结构和整体样式：

- [frontend/index.html](../frontend/index.html)
- [frontend/assets/styles.css](../frontend/assets/styles.css)
- [frontend/assets/app.js](../frontend/assets/app.js)

新的界面已经不是简单聊天窗口，而是更像一个完整学习产品：

1. 左侧承接目录、资料和历史。
2. 中间是对话主舞台。
3. 下方是统一输入区。
4. 额外有知识图谱弹层、学习画像弹层、用户菜单和设置入口。

在会话层，你补全了 SSE 事件消费：

- [frontend/assets/js/session.js](../frontend/assets/js/session.js)

当前前端已经能接住并处理的关键事件包括：

1. `topic.confirmation_needed`
2. `assessment.question`
3. `graph.node_update`
4. `user_knowledge_graph.sync`
5. `session.awaiting_input`

这意味着前端已经不是“等一条最终文本回来再渲染”，而是能根据后端流程状态逐步更新界面。

在 UI 渲染层，你做了统一消息和状态呈现：

- [frontend/assets/js/ui.js](../frontend/assets/js/ui.js)

它承接了很多产品化能力，例如：

1. 普通消息与系统消息的统一渲染。
2. topic confirmation 卡片。
3. 逐题测评卡片。
4. 流程 chip 和阶段状态展示。
5. 当前图谱节点和掌握状态展示。
6. 证据卡、评估卡等信息压缩呈现。

在历史恢复方面，你做的不是简单恢复聊天文本，而是恢复“状态”：

- [frontend/assets/js/history.js](../frontend/assets/js/history.js)

现在恢复旧会话时，前端可以一起恢复：

1. 当前是否还在等待输入。
2. 测评是否进行到一半。
3. 图谱当前节点是什么。
4. 用户知识图谱和学习画像状态。
5. 对应消息时间线。

这一步很关键，因为对于伴学产品来说，恢复的不是“说过什么”，而是“学到哪了”。

在资料管理上，你补全了上传、删除和清空：

- [frontend/assets/js/knowledge.js](../frontend/assets/js/knowledge.js)

用户上传的资料现在已经能进入资料区，并支持删除和清空，同时和后端索引同步。

在设置层，你重做了本地配置面板：

- [frontend/assets/js/config.js](../frontend/assets/js/config.js)

现在设置不再是零散表单，而是更像一个完整产品的设置页，覆盖：

1. 通知。
2. 个性化。
3. 账户信息。
4. 本地模型 profile 配置。
5. 网络代理。
6. 资料索引设置。

你还在主壳层把更多交互串起来了：

- [frontend/assets/app.js](../frontend/assets/app.js)

这里包括：

1. 图谱 viewer 弹层。
2. 学习画像弹层。
3. 用户账户菜单。
4. 侧栏开合。
5. 模型 profile 选择。
6. 设置入口。

最有产品感的一点，是你把独立图谱 viewer 和主应用联动起来了。viewer 里点击“学习该节点”后，会通过消息机制把节点回传给主页面，主页面再据此继续学习。这一步让图谱真正成了学习入口，而不是一个旁观型展示页。

### 阶段三的结果

这一阶段完成后，系统已经从“后端流程能跑”变成“前端能把整套学习流程承接住”。

也就是说，用户已经可以看到：

1. 当前处在哪个学习阶段。
2. 现在系统在问什么、等什么。
3. 当前图谱节点是什么。
4. 自己掌握状态如何变化。
5. 关闭页面之后，下次怎么接回来。

所以第三阶段不是简单 UI 美化，而是产品壳层的完成。

---

## 三、这三天实际实现和完善的核心能力

为了方便组员横向理解，这里把核心能力按功能块单独列一下。

### 1. 主题确认与入口收束

系统能够先判断用户是在开启课程、继续学习、还是提出局部问题，并在必要时弹出主题确认，而不是直接硬切固定流程。

相关文件：

- [ai_tutor_agent/nodes/greeting.py](../ai_tutor_agent/nodes/greeting.py)
- [ai_tutor_agent/nodes/topic_confirm.py](../ai_tutor_agent/nodes/topic_confirm.py)

### 2. 对话式逐题测评

测评从一次性表单改成了对话式推进，每轮只推进当前题组，并结合自评和客观题来校准掌握度。

相关文件：

- [ai_tutor_agent/nodes/assessment.py](../ai_tutor_agent/nodes/assessment.py)
- [ai_tutor_agent/core/state.py](../ai_tutor_agent/core/state.py)

### 3. 用户知识图谱 UKG

用户的测评结果和学习推进，会沉淀为 `user_knowledge_graph`，后端和前端都能基于这个状态做判断和呈现。

相关文件：

- [ai_tutor_agent/core/state.py](../ai_tutor_agent/core/state.py)
- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)
- [frontend/assets/js/session.js](../frontend/assets/js/session.js)
- [frontend/assets/js/history.js](../frontend/assets/js/history.js)

### 4. 图谱锚定教学

Tutor 的每轮讲解已经围绕当前图谱节点展开，而不是把整个课程当成一坨资料去答。

相关文件：

- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)
- [ai_tutor_agent/core/graph_service.py](../ai_tutor_agent/core/graph_service.py)

### 5. 掌握度门控和隐藏标记

LLM 可以声明“掌握”“跳过”“下一概念”，但状态更新不是直接信任文案，而是通过后端逻辑和前端事件去消费这些隐藏标记。

相关文件：

- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)
- [frontend/assets/js/session.js](../frontend/assets/js/session.js)
- [frontend/assets/js/ui.js](../frontend/assets/js/ui.js)

### 6. 下一步决策器

讲完后，系统已经可以决定接下来该继续讲、补前置、转节点、练习还是收束，而不是只能继续自由对话。

相关文件：

- [ai_tutor_agent/nodes/next_step.py](../ai_tutor_agent/nodes/next_step.py)
- [ai_tutor_agent/orchestration/workflow.py](../ai_tutor_agent/orchestration/workflow.py)

### 7. 中断问答与主线回桥

学生中途插问时，系统可以先回答问题，再自然回到当前学习主线，不会直接断掉学习流程。

相关文件：

- [ai_tutor_agent/nodes/interruption.py](../ai_tutor_agent/nodes/interruption.py)

### 8. 情绪感知与教学策略信号

系统已经开始记录基本情绪线索，后续可以用于放慢节奏、加强鼓励、增加挑战或调整解释方式。

相关文件：

- [ai_tutor_agent/nodes/affect.py](../ai_tutor_agent/nodes/affect.py)
- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)

### 9. 图谱 viewer 与主应用联动

图谱不只是可视化，还能把用户点击的节点直接回带到主学习页面，成为真实学习入口。

相关文件：

- [a2-control-theory/viewer/index.html](../a2-control-theory/viewer/index.html)
- [a2-control-theory/viewer/app.js](../a2-control-theory/viewer/app.js)
- [frontend/assets/app.js](../frontend/assets/app.js)
- [ai_tutor_agent/interfaces/api/app.py](../ai_tutor_agent/interfaces/api/app.py)

### 10. 证据链检索

课程主资料、上传资料、图谱锚点和外部搜索已经开始组成一条更完整的证据链，让 Tutor 的讲解不只来自大模型常识。

相关文件：

- [ai_tutor_agent/infrastructure/retriever.py](../ai_tutor_agent/infrastructure/retriever.py)
- [ai_tutor_agent/infrastructure/web_search.py](../ai_tutor_agent/infrastructure/web_search.py)

### 11. 资料管理与索引同步

用户资料已经支持上传、删除、清空，且删除后不再只删文件，还考虑索引同步。

相关文件：

- [frontend/assets/js/knowledge.js](../frontend/assets/js/knowledge.js)
- [ai_tutor_agent/interfaces/api/knowledge.py](../ai_tutor_agent/interfaces/api/knowledge.py)
- [ai_tutor_agent/infrastructure/retriever.py](../ai_tutor_agent/infrastructure/retriever.py)

### 12. 历史恢复

恢复的是完整学习状态，而不是仅恢复聊天记录文本。

相关文件：

- [frontend/assets/js/history.js](../frontend/assets/js/history.js)
- [ai_tutor_agent/interfaces/api/history.py](../ai_tutor_agent/interfaces/api/history.py)
- [ai_tutor_agent/interfaces/api/session.py](../ai_tutor_agent/interfaces/api/session.py)

---

## 四、知识图谱、后端和 UI 现在是怎么协同工作的

这一部分是理解系统当前架构最关键的一段。

### 1. 图谱数据层

[a2-control-theory](../a2-control-theory) 目录定义课程结构、节点关系和课程资料。

这里负责回答的问题是：

1. 这门课有哪些知识点。
2. 它们之间是什么关系。
3. 每个知识点的目标、误区和路径是什么。

### 2. 检索层

- [ai_tutor_agent/infrastructure/retriever.py](../ai_tutor_agent/infrastructure/retriever.py)
- [ai_tutor_agent/infrastructure/web_search.py](../ai_tutor_agent/infrastructure/web_search.py)

这里负责把“当前图谱节点”映射到“应该拿什么证据讲”。

它大致会优先考虑：

1. 图谱锚点对应的课程主资料。
2. 用户上传资料。
3. 必要时补充外部搜索结果。

### 3. 决策层

- [ai_tutor_agent/core/graph_service.py](../ai_tutor_agent/core/graph_service.py)

这里负责把知识图谱结构变成教学决策，例如：

1. 当前点的前置是否有缺口。
2. 当前点的下游路径是什么。
3. 有没有盲点需要补。
4. 下一步适合继续还是转向。

### 4. 教学层

- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)

这里负责把图谱上下文、用户状态和资料证据真正写进 Tutor 这一轮的讲解里，并输出掌握标记和下一概念标记。

### 5. SSE 事件层

- [frontend/assets/js/session.js](../frontend/assets/js/session.js)

这里负责把后端状态机的变化实时发给前端，让前端知道当前该显示什么卡片、更新什么图谱状态、什么时候等待用户输入。

### 6. 渲染层

- [frontend/assets/js/ui.js](../frontend/assets/js/ui.js)

这里负责把流程状态、图谱节点变化、用户知识图谱同步结果和证据卡变成实际界面。

### 7. viewer 联动层

- [a2-control-theory/viewer/app.js](../a2-control-theory/viewer/app.js)
- [frontend/assets/app.js](../frontend/assets/app.js)

这里负责把“看图谱”变成“继续学习某个节点”，打通独立图谱页和主学习页。

### 协同结果

这几层协同起来后，知识图谱已经不只是展示层，而是：

1. 决定起点。
2. 提供教学上下文。
3. 参与下一步决策。
4. 驱动前端状态展示。
5. 影响历史恢复和学习路径连续性。

这也是这次改动里最核心的架构提升。

---

## 五、现在系统大致怎么用

从用户视角看，当前系统的典型使用流程已经变成：

1. 用户输入“我要学自动控制原理”或提出某个控制理论问题。
2. 系统识别主题和焦点，必要时弹出主题确认。
3. 主题确认后，进入对话式测评或接续已有学习状态。
4. 测评完成后，系统生成用户知识图谱并选择当前图谱锚点。
5. Tutor 围绕当前节点结合课程主资料、上传资料和图谱误区讲解。
6. 前端根据隐藏标记和 SSE 事件更新当前节点、掌握状态和学习画像。
7. 用户可以继续、做题、切换节点，或者中途插问。
8. 如果插问，系统先解答，再回到主线。
9. 用户也可以打开知识图谱 viewer，点击某个节点继续学习。
10. 关闭页面后，下次恢复会话时，系统会继续接回原来的学习状态。

---

## 六、主要改动文件索引

这一部分方便组员后续按模块读代码。

### 1. 课程图谱与 viewer

- [a2-control-theory/graph.json](../a2-control-theory/graph.json)
- [a2-control-theory/curriculum.json](../a2-control-theory/curriculum.json)
- [a2-control-theory/notes.jsonl](../a2-control-theory/notes.jsonl)
- [a2-control-theory/summary.json](../a2-control-theory/summary.json)
- [a2-control-theory/GRAPH_SCHEMA.md](../a2-control-theory/GRAPH_SCHEMA.md)
- [a2-control-theory/README.md](../a2-control-theory/README.md)
- [a2-control-theory/source-notes](../a2-control-theory/source-notes)
- [a2-control-theory/viewer/index.html](../a2-control-theory/viewer/index.html)
- [a2-control-theory/viewer/app.js](../a2-control-theory/viewer/app.js)
- [a2-control-theory/viewer/style.css](../a2-control-theory/viewer/style.css)
- [a2-control-theory/viewer/data.js](../a2-control-theory/viewer/data.js)

### 2. 全局状态与图谱服务

- [ai_tutor_agent/core/state.py](../ai_tutor_agent/core/state.py)
- [ai_tutor_agent/core/graph_service.py](../ai_tutor_agent/core/graph_service.py)

### 3. 工作流编排

- [ai_tutor_agent/orchestration/workflow.py](../ai_tutor_agent/orchestration/workflow.py)
- [ai_tutor_agent/orchestration/routing.py](../ai_tutor_agent/orchestration/routing.py)

### 4. 教学与测评节点

- [ai_tutor_agent/nodes/greeting.py](../ai_tutor_agent/nodes/greeting.py)
- [ai_tutor_agent/nodes/topic_confirm.py](../ai_tutor_agent/nodes/topic_confirm.py)
- [ai_tutor_agent/nodes/assessment.py](../ai_tutor_agent/nodes/assessment.py)
- [ai_tutor_agent/nodes/tutor.py](../ai_tutor_agent/nodes/tutor.py)
- [ai_tutor_agent/nodes/next_step.py](../ai_tutor_agent/nodes/next_step.py)
- [ai_tutor_agent/nodes/tester.py](../ai_tutor_agent/nodes/tester.py)
- [ai_tutor_agent/nodes/evaluator.py](../ai_tutor_agent/nodes/evaluator.py)
- [ai_tutor_agent/nodes/coach.py](../ai_tutor_agent/nodes/coach.py)
- [ai_tutor_agent/nodes/post_eval.py](../ai_tutor_agent/nodes/post_eval.py)
- [ai_tutor_agent/nodes/interruption.py](../ai_tutor_agent/nodes/interruption.py)
- [ai_tutor_agent/nodes/affect.py](../ai_tutor_agent/nodes/affect.py)

### 5. 检索与资料管理

- [ai_tutor_agent/infrastructure/retriever.py](../ai_tutor_agent/infrastructure/retriever.py)
- [ai_tutor_agent/infrastructure/web_search.py](../ai_tutor_agent/infrastructure/web_search.py)

### 6. API 与运行时

- [ai_tutor_agent/interfaces/api/app.py](../ai_tutor_agent/interfaces/api/app.py)
- [ai_tutor_agent/interfaces/api/runtime.py](../ai_tutor_agent/interfaces/api/runtime.py)
- [ai_tutor_agent/interfaces/api/session.py](../ai_tutor_agent/interfaces/api/session.py)
- [ai_tutor_agent/interfaces/api/history.py](../ai_tutor_agent/interfaces/api/history.py)
- [ai_tutor_agent/interfaces/api/config.py](../ai_tutor_agent/interfaces/api/config.py)
- [ai_tutor_agent/interfaces/api/adapter.py](../ai_tutor_agent/interfaces/api/adapter.py)

### 7. 前端主界面

- [frontend/index.html](../frontend/index.html)
- [frontend/assets/styles.css](../frontend/assets/styles.css)
- [frontend/assets/app.js](../frontend/assets/app.js)
- [frontend/assets/js/ui.js](../frontend/assets/js/ui.js)
- [frontend/assets/js/session.js](../frontend/assets/js/session.js)
- [frontend/assets/js/history.js](../frontend/assets/js/history.js)
- [frontend/assets/js/config.js](../frontend/assets/js/config.js)
- [frontend/assets/js/knowledge.js](../frontend/assets/js/knowledge.js)
- [frontend/assets/js/state.js](../frontend/assets/js/state.js)

### 8. 配置与测试

- [ai_tutor_agent/config.py](../ai_tutor_agent/config.py)
- [tests/test_assessment.py](../tests/test_assessment.py)
- [tests/test_tutor.py](../tests/test_tutor.py)
- [tests/test_workflow.py](../tests/test_workflow.py)
- [tests/test_history.py](../tests/test_history.py)
- [tests/test_retriever.py](../tests/test_retriever.py)
- [tests/test_graph_service.py](../tests/test_graph_service.py)
- [tests/test_next_step.py](../tests/test_next_step.py)
- [tests/test_post_eval.py](../tests/test_post_eval.py)

---

## 七、这三天工作的核心价值

如果从“做了哪些功能”上看，这三天改了很多地方。

但如果从“真正提升了项目什么能力”来看，核心价值其实可以压缩成三点：

### 1. 把知识图谱从展示层推进成教学控制层

之前图谱最多是个辅助结构；现在图谱已经参与起点选择、前置判断、教学锚定、下一步推荐和前端状态展示。

### 2. 把 Tutor 从问答原型推进成伴学流程系统

现在系统已经具备主题收束、测评定起点、持续记录掌握状态、教学推进、插问回桥和历史恢复这些真正属于“伴学”的能力。

### 3. 把前后端真正拉通成一个可用产品

这次不是后端自己跑通，前端单独美化，而是状态字段、事件流、恢复流、图谱状态和学习界面被一起打通了。

所以从产品层面看，这三天最大的提升是：

项目的核心竞争力已经不再只是“能回答”，而是开始具备“能判断用户起点、能带着用户走路径、能持续接住上下文”的能力。

---

## 八、后续组内沟通建议

如果这份文档用于组内同步，建议阅读顺序如下：

1. 先看“先看结论”和“整体演进脉络”，快速建立全局理解。
2. 再看“知识图谱、后端和 UI 怎么协同工作”，理解当前系统架构。
3. 最后根据自己负责的方向，到“主要改动文件索引”里定位对应代码。

如果后续需要继续对外汇报，这份内容可以进一步整理成更正式的“周报版 / 汇报版 / 导师沟通版”，重点会更偏成果表达和阶段价值，而不是代码结构说明。