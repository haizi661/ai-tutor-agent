# 比较老了但可以看看

## 快速上手看结果

切分pdf文件python ai_tutor_agent\split_pdf_by_chapters.py

调试图谱用
第一步python -m ai_tutor_agent.knowledge_map.debug_pipeline_v2
第二步python -m ai_tutor_agent.knowledge_map.debug_vector_retrieval
第三步python -m ai_tutor_agent.knowledge_map.debug_rag_qa

调试图谱问答用python -m ai_tutor_agent.knowledge_map.debug_companion
输入help就会弹出推荐用的问题


# knowledge_map 模块 README

## 1. 模块目标

本模块用于构建《自动控制原理》课程的知识图谱，并在知识图谱基础上实现节点级检索、向量检索、重排、以及基于 DeepSeek 的问答与“老师风格”讲解生成能力。

当前版本已经不是单纯的“知识点列表”，而是一个面向后续“伴学智能体”使用的知识底座。它包含：

1. 课程知识图谱骨架构建
2. 教材 PDF 页码定位与内容增强
3. 节点候选池构建
4. 向量索引与节点内检索
5. 检索结果重排
6. 基于 DeepSeek 的讲解生成
7. 基于知识图谱的 RAG 问答原型

---

## 2. 今天完成了什么
所有知识图谱相关代码全在ai_tutor_agent\knowledge_map里面 结果文件全在ai-tutor-agent\data\knowledge_map_outputs里面。
rag最新版已经融合 但rag的多模态能力还没用上

今天主要完成了 knowledge_map 模块“图谱驱动问答”的第一版闭环，具体包括以下内容：

### 2.1 知识图谱结构搭建完成
- 新建了独立的 `knowledge_map` 模块目录
- 按“配置 / schema / builders / pipeline / debug”方式重新组织代码
- 实现了一级节点、二级节点的静态骨架构建
- 支持按重点章节展开二级节点，非重点章节可简化
- 实现了基础关系构建：
  - `HAS_SUBTOPIC`
  - `PRE_REQUIRES`
  - `LEADS_TO`

### 2.2 节点字段体系搭建完成
- 统一了节点默认字段模板
- 统一了边默认字段模板
- 支持后续扩展节点字段，不需要到处改逻辑
- 节点已包含基础标识属性、教学属性、关系属性和 meta 属性

### 2.3 教材 PDF 接入完成
- 已接入教材 PDF
- 已实现章节页码范围配置
- 已实现节点页码粗定位 `page_refs`
- 已实现锚点页 `anchor_page`
- 已实现精细页码收缩 `page_refs_refined`

### 2.4 节点内容增强完成第一版
- 能根据教材候选页提取：
  - `explanation_raw`
  - `core_concepts`
  - `key_points`
  - `summary`
- 已加入 OCR 基础清洗逻辑，能处理一部分乱码符号

### 2.5 候选池构建完成
- 已为每个节点建立候选池：
  - `definition_candidates`
  - `key_point_candidates`
  - `formula_candidates`
  - `example_candidates`
- 候选池已成为后续 RAG 的检索证据来源

### 2.6 向量检索层完成
- 已将候选池摊平写入 Chroma
- 已支持按 `node_id` 做节点内检索
- 已支持按候选类型过滤检索
- 已实现检索结果重排器 `retrieval_reranker.py`

### 2.7 DeepSeek 生成能力接入
- 已支持基于候选池生成 `explanation_teacher_style`
- 已支持基于节点内检索结果生成问答答案
- 已验证：关闭代理后，DeepSeek 可正常调用
- 已形成第一版“老师风格讲解”和“知识图谱问答”

### 2.8 问答原型完成
- 已完成：
  - 问题 → 节点选择
  - 节点内向量检索
  - 检索结果重排
  - DeepSeek 生成回答
- 已能针对问题输出：
  - 匹配节点
  - 检索证据
  - 最终答案

---

## 3. 当前模块目录与作用说明

```text
knowledge_map/
│  debug_pipeline_v2.py
│  debug_rag_qa.py
│  debug_vector_retrieval.py
│  pipeline_v2.py
│  rag_qa_pipeline.py
│
├─builders
│  │  graph_relation_builder.py
│  │  graph_skeleton_builder.py
│  │  node_content_enricher.py
│  │  node_property_generator.py
│  │  node_retrieval_builder.py
│  │  node_selector.py
│  │  rag_answer_generator.py
│  │  retrieval_reranker.py
│  │  teacher_style_generator.py
│  │  vector_index_builder.py
│  │  vector_retriever.py
│
├─config
│  │  course_graph_config.py
│  │  document_config.py
│  │  retrieval_config.py
│
├─schema
│  │  node_schema.py
```

---

## 4. 各文件内容与作用说明

### 4.1 根目录文件

#### `pipeline_v2.py`
主构建流程入口。负责把各个 builder 串起来，完成：
- 图谱骨架生成
- 关系生成
- 节点内容增强
- 候选池构建
- 向量索引构建
- 节点属性生成
- 输出 CSV / JSON / GraphML

可以理解为：**知识图谱离线构建总管道**。

#### `debug_pipeline_v2.py`
用于调试知识图谱构建流程。
主要功能：
- 运行 `pipeline_v2`
- 打印 metadata
- 打印节点预览
- 打印 refined page
- 打印生成后的内容字段
- 导出最终节点表和边表

适合调试：
- 图谱结构是否对
- 页码是否定位正确
- explanation / formulas / examples 是否生成

#### `rag_qa_pipeline.py`
图谱驱动的 RAG 问答流程。
主要功能：
- 读取节点表
- 选择最相关节点
- 节点内向量检索
- 调用 DeepSeek 生成问答答案

可以理解为：**伴学智能体后续问答能力的核心原型**。

#### `debug_rag_qa.py`
用于调试问答流程。
主要输出：
- question
- question_type
- matched_node
- retrieval evidence
- final answer

适合调试：
- 节点选择是否正确
- 检索证据是否合理
- DeepSeek 回答是否靠谱

#### `debug_vector_retrieval.py`
用于调试候选池向量检索。
主要作用：
- 测试某个节点内的检索效果
- 对比 raw retrieval 和 reranked retrieval
- 观察 definition / formula / example 的排序效果

适合调试：
- 向量检索质量
- 重排逻辑是否有效

---

### 4.2 builders 目录

#### `graph_skeleton_builder.py`
根据课程配置生成图谱骨架节点。
作用：
- 构建一级节点
- 构建二级节点
- 按重点章节决定是否展开二级节点

#### `graph_relation_builder.py`
根据骨架节点生成第一版规则关系。
当前主要支持：
- `HAS_SUBTOPIC`
- `PRE_REQUIRES`
- `LEADS_TO`

#### `node_content_enricher.py`
节点内容增强器。
作用：
- 教材 PDF 读取
- 页码粗匹配
- 锚点页选择
- refined page 生成
- explanation_raw / key_points / summary 初步生成
- OCR 基础清洗

#### `node_retrieval_builder.py`
候选池构建器。
作用：
- 在 refined pages 中抽取候选句
- 按不同用途构建候选池：
  - 定义候选
  - 重点候选
  - 公式候选
  - 例子候选

#### `vector_index_builder.py`
向量索引构建器。
作用：
- 把节点候选池摊平成文档
- 写入 Chroma 向量库

#### `vector_retriever.py`
节点内向量检索器。
作用：
- 按 `node_id` 限定范围检索
- 支持按 `candidate_type` 过滤
- 支持接入重排器

#### `retrieval_reranker.py`
检索重排器。
作用：
- 对向量检索结果二次排序
- 根据问题类型和候选类型加权
- 提升定义型 / 公式型 / 例子型问题的命中效果

#### `node_selector.py`
问题对应节点选择器。
作用：
- 根据用户问题从节点表中粗选最相关节点
- 用于问答流程的第一步节点定位

#### `teacher_style_generator.py`
基于 DeepSeek 的老师风格讲解生成器。
作用：
- 把候选池内容重写为更像老师上课的讲解
- 生成 `explanation_teacher_style`

#### `node_property_generator.py`
节点属性生成器。
作用：
- 调用向量检索拿回候选证据
- 生成：
  - `explanation_teacher_style`
  - `formulas`
  - `examples`
- 当前是“属性生成总控”

#### `rag_answer_generator.py`
问答答案生成器。
作用：
- 接收节点内检索证据
- 调用 DeepSeek
- 输出最终回答

---

### 4.3 config 目录

#### `course_graph_config.py`
课程图谱配置文件。
作用：
- 定义课程章节结构
- 定义一级/二级节点
- 定义 page_range
- 定义 retrieval_keywords
- 控制章节是否重点展开

这是**整个图谱结构的最核心配置源**。

#### `document_config.py`
文档路径配置文件。
作用：
- 配置教材 PDF
- 配置大纲 PDF
- 后续还可以继续扩展题库路径

#### `retrieval_config.py`
检索配置文件。
作用：
- 配置向量库目录
- 配置 collection 名称
- 配置候选字段权重

---

### 4.4 schema 目录

#### `node_schema.py`
节点与边的 schema 定义文件。
作用：
- 定义节点默认模板
- 定义边默认模板
- 定义字段分组
- 负责保证字段完整性和可扩展性

这个文件是后续**字段扩展的核心位置**。

---

### 4.5 结果文件

#### `auto_control_knowledge_map_v2_nodes.csv`
这是节点表。每一行是一个知识点节点，里面有节点名称、章节、层级、summary、page_refs、候选内容等。它最适合你直接打开检查“每个节点现在长啥样”。

#### `auto_control_knowledge_map_v2_edges.csv`
这是关系表。每一行是一条边，比如谁是前置、谁包含谁。它最适合检查图谱结构是不是对的。

#### `auto_control_knowledge_map_v2.graphml`
这是图数据库/图可视化更常用的格式。后面如果你想用 Gephi、yEd、Neo4j 周边工具、NetworkX 之类去看图结构，这个比较方便。

#### `auto_control_knowledge_map_v2.json`
这是更通用的程序交换格式。后面如果你要接前端、接接口、接别的脚本，JSON 最方便。


---


## 5. 队友如果要拓展字段，应该怎么做

这一部分非常重要，后续扩展新字段时尽量按下面流程来，不要直接到处乱加。

### 5.1 第一步：先去 `schema/node_schema.py`
这个文件里有两个关键位置：

#### 位置 1：`NODE_FIELD_GROUPS`
如果你新增字段，希望它在逻辑上归类明确，就先把字段名放进对应分组。

例如想加：
- `requirement_level`
- `mastery_threshold`

可以放到：
- basic
- teaching
- meta

根据实际含义决定。

#### 位置 2：`NODE_DEFAULT_TEMPLATE`
这里必须新增默认值，不然后面 DataFrame / CSV / JSON 导出时容易缺列。

例如新增：

```python
"requirement_level": "",
"mastery_threshold": 0.0,
```

---

### 5.2 第二步：去对应 builder 里补生成逻辑

新增字段不是只在 schema 里加完就结束了，还要看这个字段由谁负责填充。

例如：

#### 如果是课程配置类字段
比如：
- `requirement_level`
- `importance_level`

应去：
- `config/course_graph_config.py`
- `builders/graph_skeleton_builder.py`

做法：
1. 在配置中为章节或节点新增字段
2. 在 `graph_skeleton_builder.py` 中把它写进节点记录

#### 如果是 PDF / 内容抽取类字段
比如：
- `page_refs`
- `definition_candidates`
- `formula_candidates`

应去：
- `node_content_enricher.py`
- `node_retrieval_builder.py`

#### 如果是生成类字段
比如：
- `explanation_teacher_style`
- `common_mistakes`
- `quiz_suggestions`

应去：
- `node_property_generator.py`
- 或新建新的 generator

---

### 5.3 第三步：如果字段要导出或调试，要改 debug 文件

例如你新增了：
- `requirement_level`

那么调试时想看到它，就去：
- `debug_pipeline_v2.py`

在 preview 输出里加上它。

---

### 5.4 示例：新增 `requirement_level`

#### 第一步，在 `schema/node_schema.py` 增加
```python
"requirement_level": "",
```

#### 第二步，在 `course_graph_config.py` 的节点配置里增加
```python
"requirement_level": "掌握",
```

#### 第三步，在 `graph_skeleton_builder.py` 构建节点时写入
```python
"requirement_level": chapter_cfg.get("requirement_level", ""),
```

#### 第四步，在 `debug_pipeline_v2.py` 中打印查看

这样就是一套完整扩展流程。

---

## 6. 当前已使用到的技术与方法

当前模块已经使用到的核心技术包括：

### 6.1 图谱构建
- 静态课程骨架配置
- 节点/边结构化生成
- GraphML / JSON / CSV 导出

### 6.2 文本处理
- PDF 文本读取
- OCR 清洗
- 句子切分
- 候选句抽取

### 6.3 检索
- 节点级候选池
- Chroma 向量库
- 向量相似度检索
- 检索结果规则重排

### 6.4 RAG
当前已经实际用到了 RAG 思路，主要体现在：
- 节点约束检索
- 节点内证据召回
- 将检索证据交给 DeepSeek 生成回答或讲解

这已经不是纯规则系统，而是**图谱约束下的局部 RAG 系统**。

### 6.5 大模型生成
- DeepSeek 生成老师风格讲解
- DeepSeek 生成问答答案

---

## 7. 当前仍存在的问题

### 7.1 大纲尚未真正接入
- 目前知识点还没有 requirement_level
- 没有掌握门槛
- 没有把“了解/理解/掌握/应用”落实到节点

### 7.2 学习路径关系还不够丰富
- 目前只有基础前后关系
- 还缺：
  - 更细的前置知识
  - 相关知识点
  - 应用知识点
  - 推荐学习路径

### 7.3 学生状态模型还未接入
- 还不能记录学生是否学过
- 还不能记录掌握度和正确率
- 还没有个性化推荐能力

### 7.4 OCR 噪声仍然存在
- 扫描版教材导致候选池有脏文本
- 公式抽取质量一般
- LaTeX 级别公式恢复尚未实现

### 7.5 多模态尚未真正接入
- 图、表、公式图像目前还没有进入问答主流程
- 当前主要还是文本版知识图谱 + 文本 RAG

---

## 8. 接下来需要做什么

后续建议按这个优先级推进：

### 第一优先级：接入课程大纲
目标：
- 给每个节点加课程要求等级
- 给每个节点设置不同掌握门槛

建议新增字段：
- `requirement_level`
- `mastery_threshold`
- `importance_level`
- `assessment_focus`

### 第二优先级：完善关系层
目标：
- 真正支持学习路径推荐

建议继续补：
- `PRE_REQUIRES`
- `LEADS_TO`
- `RELATED_TO`
- `APPLIED_IN`

### 第三优先级：接入学生状态
目标：
- 从“会讲知识”升级成“会陪学生学”

建议新增学生状态字段：
- `is_learned`
- `mastery_score`
- `correct_rate`
- `error_count`
- `last_review_time`

### 第四优先级：做题目映射与评测闭环
目标：
- 根据知识点和掌握度推荐题目
- 根据题目反馈更新学生状态

### 第五优先级：做多模态增强
目标：
- 接入图表、表格、公式图
- 优化 OCR
- 尝试公式重建 / LaTeX 转写

---

## 9. 当前阶段总结

当前 `knowledge_map` 模块已经完成了从“静态课程知识点”到“图谱驱动问答原型”的第一阶段搭建。

它已经具备：
- 知识图谱结构
- 教材内容接入
- 节点级候选池
- 向量检索
- 检索重排
- DeepSeek 讲解生成
- 基于图谱节点的问答能力

因此，当前模块已经具备作为“伴学智能体知识底座”的基础能力。  
下一阶段的重点将不再是单纯丰富节点内容，而是引入课程大纲、学生状态和学习路径逻辑，使系统从“能回答”升级为“能伴学”。
