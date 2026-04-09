# knowledge_map 模块需求说明（Requirement）

## 1. 项目背景

`knowledge_map` 模块的最终目标不是只做一个课程知识图谱，而是作为“自动控制原理伴学智能体”的知识底座。  
因此，本模块需要同时支持：

1. 课程知识结构表达  
2. 教材内容接入与节点内容增强  
3. 节点级检索与问答  
4. 课程要求约束  
5. 学生学习状态记录  
6. 学习路径推荐与伴学决策

当前已完成第一阶段：知识图谱基础构建 + 节点内容增强 + 节点级 RAG 原型。  
后续需求将在此基础上逐步扩展。

---

## 2. 当前系统已满足的需求

### 2.1 图谱结构需求
- 支持一级知识点、二级知识点建模
- 支持节点基础字段与边字段
- 支持包含、前后继等基础关系
- 支持节点和边导出

### 2.2 内容接入需求
- 支持教材 PDF 输入
- 支持节点页码范围定位
- 支持候选文本抽取
- 支持节点教学属性生成

### 2.3 检索与问答需求
- 支持节点内向量检索
- 支持不同候选类型的证据池
- 支持检索结果重排
- 支持 DeepSeek 问答生成

---

## 3. 当前模块的核心需求拆分

## 3.1 知识图谱层需求

### 必须支持
- 节点唯一标识
- 节点名称
- 所属章节
- 节点层级
- 节点摘要
- 标签
- 节点教学属性
- 节点关系属性

### 当前已落实的主要字段
- `node_id`
- `name`
- `chapter`
- `level`
- `summary`
- `tags`
- `explanation_raw`
- `explanation_teacher_style`
- `core_concepts`
- `key_points`
- `formulas`
- `examples`
- `page_refs`
- `prerequisite_nodes`
- `next_nodes`
- `part_of`

---

## 3.2 教材处理层需求

### 必须支持
- 教材 PDF 路径配置
- 教材文本读取
- 页码定位
- 节点锚点页确定
- 候选页精细范围确定
- OCR 基础清洗

### 当前已完成
- `page_refs`
- `anchor_page`
- `page_refs_refined`
- explanation_raw / key_points 初步生成

### 当前不足
- 公式 OCR 质量一般
- 图表未纳入主流程
- 扫描文本仍有脏字符

---

## 3.3 候选池层需求

### 必须支持
- 定义类候选
- 重点类候选
- 公式类候选
- 例子类候选

### 当前字段
- `definition_candidates`
- `key_point_candidates`
- `formula_candidates`
- `example_candidates`

### 作用
- 为节点属性生成提供证据
- 为节点级 RAG 提供证据池

---

## 3.4 向量检索层需求

### 必须支持
- 节点内检索
- 候选类型过滤
- 向量索引持久化
- 检索结果重排

### 当前已完成
- Chroma 向量库存储
- 按 `node_id` 限定检索
- 按 `candidate_type` 过滤
- rule-based rerank

---

## 3.5 LLM 生成层需求

### 必须支持
- 老师风格讲解生成
- RAG 问答生成

### 当前已完成
- `teacher_style_generator.py`
- `rag_answer_generator.py`

### 当前不足
- 依赖外部 API
- OCR 污染会影响生成质量
- 还没有专门针对公式/例题的独立生成模板

---

## 4. 后续必须补充的需求

## 4.1 课程大纲接入需求（最高优先级）

### 目标
将课程大纲真正变成系统的规则层，而不是只做教材图谱。

### 必须新增的节点属性
- `requirement_level`
  - 了解
  - 理解
  - 掌握
  - 熟练应用
- `mastery_threshold`
  - 节点过关阈值
- `importance_level`
  - 一般 / 重点 / 核心
- `assessment_focus`
  - 概念 / 公式 / 分析 / 应用

### 业务意义
- 不同知识点采用不同掌握门槛
- 不同知识点采用不同答题评价标准
- 为伴学智能体做“通过/未通过”判断提供规则依据

---

## 4.2 关系层增强需求（高优先级）

### 当前关系不够
目前只有基本包含和顺序关系，不足以支撑伴学路径。

### 需要补的关系
- `PRE_REQUIRES`
  - 学当前节点前必须先掌握什么
- `LEADS_TO`
  - 学完当前节点后通常接什么
- `RELATED_TO`
  - 容易一起混淆或一起学习的节点
- `APPLIED_IN`
  - 当前知识点会在哪些方法/题型/场景中应用

### 业务意义
- 支持先修判断
- 支持学习路径推荐
- 支持薄弱点回补

---

## 4.3 学生状态层需求（高优先级）

### 目标
使系统不仅知道“知识是什么”，还知道“学生学到哪了”。

### 需要新增的学生状态字段
建议单独做 student_state，不直接写进节点模板：
- `student_id`
- `node_id`
- `is_learned`
- `mastery_score`
- `correct_rate`
- `error_count`
- `last_review_time`
- `recommended_next_action`

### 业务意义
- 形成个性化学习记录
- 根据掌握度判断是否通过
- 支持复习提醒与下一步推荐

---

## 4.4 题目映射需求（中高优先级）

### 目标
使图谱与题库形成闭环。

### 需要支持
- 题目与知识点映射
- 主知识点 / 次知识点标注
- 难度标注
- 根据答题结果更新掌握度

### 业务意义
- 能基于知识点出题
- 能根据错题回退知识点
- 能构建完整伴学闭环

---

## 4.5 多模态增强需求（中优先级）

### 目标
解决扫描教材导致的图表与公式信息损失问题。

### 需要支持
- 图像候选池
- 表格候选池
- 公式图像候选池
- 图文联合检索

### 当前状态
- 暂未真正接入主流程
- 当前系统以文本 RAG 为主

---

## 5. 功能扩展规范

后续新增字段、逻辑或能力时，必须按以下规范：

### 5.1 字段扩展规范
新增节点字段时必须同步修改：
1. `schema/node_schema.py`
   - `NODE_FIELD_GROUPS`
   - `NODE_DEFAULT_TEMPLATE`
2. 对应 builder
   - 负责填充该字段的文件
3. debug 文件
   - 需要时打印该字段

### 5.2 配置扩展规范
新增课程结构、文档路径、检索配置时必须放在：
- `config/course_graph_config.py`
- `config/document_config.py`
- `config/retrieval_config.py`

不要把配置硬编码进 builder。

### 5.3 新能力扩展规范
如果新增独立能力，例如：
- 大纲解析器
- 学生状态管理器
- 题目映射器
- 多模态检索器

建议统一放在：
- `builders/xxx_builder.py`
- 或新建独立 service 文件

---

## 6. 接下来开发优先级建议

### 第一优先级
课程大纲接入：
- requirement_level
- mastery_threshold
- importance_level
- assessment_focus

### 第二优先级
关系增强：
- PRE_REQUIRES
- RELATED_TO
- APPLIED_IN

### 第三优先级
学生状态层：
- mastery_score
- correct_rate
- next recommendation

### 第四优先级
题目映射与评测闭环

### 第五优先级
多模态增强与公式优化

---

## 7. 阶段性结论

`knowledge_map` 模块当前已经具备作为伴学智能体知识底座的基础能力，完成了：

- 图谱结构搭建
- 教材接入
- 候选池构建
- 向量检索
- 检索重排
- 节点级 RAG 问答
- 老师风格讲解生成

后续工作的核心重点，不再是单纯丰富节点文字内容，而是把**课程规则、学生状态、学习路径和题目反馈**接入系统，最终形成真正的伴学智能体能力闭环。
