# knowledge_map + companion 模块 README（升级版）

## 1. 模块目标

本模块不仅用于构建知识图谱，还扩展为伴学智能体原型系统，包含知识、检索、学生状态三层。

## 2. 系统结构

1.  知识层：章节切分PDF + mineru + 知识图谱
2.  检索层：Chroma + BM25 + rerank
3.  学生层：student_state

## 3. 学生状态（核心）

当前结构： - student_id - current_node_id - visited_nodes -
wrong_nodes - mastery_scores - recommended_queue

持久化: data/student_states/

## 4. debug_companion

用于调试知识、路径、学生状态，不会重新跑MinerU。

## 5. 命令分类

知识类：ask / node / search\
结构类：path / prereq / next\
内容类：formulas / examples\
学生类：student / set_current / mark_visited / mark_wrong / mastery\
决策类：recommend / review

## 6. 当前能力

✔ 知识图谱\
✔ RAG\
✔ 学生模型\
✔ 个性化推荐

## 7. 当前缺失



## 8. 下一步

学完自动跳转下一节点


## 9. 知识图谱节点属性说明（当前已实现）

当前系统中的每一个知识点节点（Node）已经包含了**结构信息 + 教学内容 + 检索候选 + 学习路径信息**四大类属性。

---

### 一、基础结构属性（Graph Structure）

用于标识节点本身和图谱结构：

- `node_id`  
  节点唯一标识，例如 `KM007`

- `name`  
  知识点名称，例如「控制系统的数学模型」

- `chapter`  
  所属章节

- `level`  
  节点层级（一级知识点 / 二级知识点）

- `part_of`  
  所属上级节点（用于构建层级结构）

---

### 二、路径与关系属性（Learning Path）

用于描述知识点之间的学习关系：

- `prerequisite_nodes`  
  前置知识（学当前节点前需要掌握的内容）

- `next_nodes`  
  后继知识（学完当前节点之后推荐学习的内容）

- `recommended_next_nodes`  
  推荐学习路径（用于伴学推荐系统）

---

### 三、教材定位属性（Document Grounding）

用于把知识点和教材内容绑定：

- `page_refs`  
  初始页码范围（粗定位）

- `anchor_page`  
  锚点页（知识点首次出现位置）

- `page_refs_refined`  
  精细页码范围（用于后续检索）

- `section_title`  
  匹配到的教材小节标题

---

### 四、基础教学内容（Raw Content）

直接从教材中抽取的内容：

- `explanation_raw`  
  原始讲解文本（OCR + 清洗后）

- `summary`  
  知识点摘要

- `core_concepts`  
  核心概念列表

- `key_points`  
  关键知识点

---

### 五、候选池（Candidate Pool，用于 RAG）

这是系统最关键的一层，用于支撑检索和生成：

- `definition_candidates`  
  定义类候选句

- `key_point_candidates`  
  重点句候选

- `formula_candidates`  
  公式候选（包含公式或公式描述）

- `example_candidates`  
  例子候选（案例、应用场景等）

👉 这些字段会被写入向量库（Chroma），用于节点内检索。

---

### 六、生成后的教学内容（LLM Generated）

通过向量检索 + DeepSeek 生成：

- `explanation_teacher_style`  
  老师风格讲解（更适合教学）

- `formulas`  
  筛选后的核心公式

- `examples`  
  筛选后的典型例子

---

### 七、课程与教学属性（部分已预留）

（部分已存在，部分正在扩展）

- `tags`  
  知识点标签

- `importance_level`（规划中）  
  重要程度（一般 / 重点 / 核心）

- `requirement_level`（规划中）  
  课程要求（了解 / 理解 / 掌握）

- `mastery_threshold`（规划中）  
  掌握阈值（用于判断是否学会）

---

### 八、总结

当前知识图谱已经不仅仅是“知识点列表”，而是一个：

- ✔ 有结构（图谱关系）  
- ✔ 有内容（教材抽取）  
- ✔ 有检索（候选池 + 向量库）  
- ✔ 有生成（老师讲解）  
- ✔ 有路径（学习顺序）  

的**图谱驱动学习系统基础层**。

后续将进一步结合：

- 学生状态（mastery / 错题 / 学习记录）
- 个性化推荐
- 题目反馈

逐步演进为完整的“伴学智能体”。