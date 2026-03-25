# RAG 2.0 系统完整使用指南

## 📋 文件结构

```
ai-tutor-agent/
├── ai_tutor_agent/
│   ├── infrastructure/         # RAG 2.0 核心模块
│   │   ├── retriever.py        # 混合检索 + BM25 重排
│   │   ├── processor.py        # MinerU PDF 处理
│   │   ├── embedding.py        # 千问 Embedding 辅助类
│   │   └── checkpoint.py       # 检查点管理
│   ├── config.py               # 配置系统（包含 RAG 参数）
│   ├── core/
│   │   └── state.py            # 状态定义（包含 student_id）
│   ├── nodes/                  # 各节点实现
│   ├── orchestration/
│   │   └── workflow.py         # 工作流编排
│   └── ...
├── debug_rag.py                # RAG 系统交互式调试脚本
├── main.py                     # 应用启动入口
├── data/
│   ├── knowledge/              # 📁 用户上传的 PDF 文件
│   ├── chroma_db/              # 📁 向量数据库存储
│   └── tutor_memory.db         # 🗂️ 会话历史数据库
├── .env                        # ⚙️ 环境变量配置（不在 git 中）
├── .env.example.rag            # 📝 配置示例
└── requirements.txt            # 依赖包列表
```

## 🔧 环境配置

### 第 1 步：创建 `.env` 文件

```bash
cp .env.example.rag .env
```

### 第 2 步：填入 API Key（必要配置）

编辑 `.env` 文件，填入以下必要字段：

```bash
# === 必需配置 ===

# 百炼 (阿里云) 的 Embedding API Key
# 获取地址: https://bailian.console.aliyun.com/
DASHSCOPE_API_KEY=sk_xxxxxx_xxxxx

# MinerU PDF 解析服务 Token
# 获取地址: https://mineru.net/
MINERU_API_TOKEN=token_xxxxx

# Embedding 服务选择
EMBEDDING_PROVIDER=dashscope

# Embedding 模型（留空自动选择）
EMBEDDING_MODEL_NAME=

# === 可选配置 ===

# 用于 query rewrite 的 LLM（debug_rag 中用到）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk_xxxxx
MODEL_NAME=gpt-4-mini
```

### 第 3 步：验证配置

```bash
python3 -c "
from ai_tutor_agent.config import get_settings
settings = get_settings()
print(f'✅ embedding_provider: {settings.embedding_provider}')
print(f'✅ knowledge_dir: {settings.knowledge_dir}')
print(f'✅ chroma_dir: {settings.chroma_dir}')
print(f'✅ memory_db_path: {settings.memory_db_path}')
"
```

## 🚀 使用方式

### 方式 1：启动应用（生产环境）

```bash
python main.py
```

然后在浏览器打开前端界面上传 PDF 知识文件。

### 方式 2：调试 RAG 系统（开发环境）

```bash
python debug_rag.py
```

此时会进入交互式调试界面：

```
请输入测试问题: 什么是 RAG？
```

系统会执行以下步骤：
1. **查询改写**（Query Rewrite）：用 LLM 改写自然语言问题
2. **混合检索**（Hybrid Search）：BM25 + 向量搜索
3. **结果展示**：显示排序后的检索结果，包含评分和元数据

## 📁 工作流程

### 1. PDF 上传和处理

```
data/knowledge/your_file.pdf
    ↓ (上传)
MinerU API (后台解析为 Markdown)
    ↓ (下载并处理)
文本分割 (chunk 大小: 1000)
    ↓
存入 ChromaDB + BM25 索引
    ↓
data/chroma_db/ (持久化存储)
```

### 2. 查询检索

```
用户问题 "什么是 RAG？"
    ↓ (Query Rewrite)
改写为: "检索增强生成(RAG)的定义、原理和应用是什么？"
    ↓ (混合检索)
BM25 检索 (关键词匹配)
向量检索 (语义相似度)
    ↓ (融合、重排)
返回 Top-3 最相关的文档
```

### 3. 上下文增强

```
Tutor 节点
    ↓
调用 LocalFileKnowledgeProvider.query_hybrid()
    ↓
获取相关知识块
    ↓
注入到 LLM prompt 中
    ↓
生成基于知识库的答案
```

## 🐛 调试常见问题

### 问题 1：`DASHSCOPE_API_KEY` 未配置

```
❌ RuntimeError: DASHSCOPE_API_KEY is required when EMBEDDING_PROVIDER=dashscope.
```

**解决**：
1. 获取 key：https://bailian.console.aliyun.com/
2. 填入 `.env`：`DASHSCOPE_API_KEY=sk_xxxxx`
3. 重启应用

### 问题 2：PDF 上传后检索为空

```
⚠️ 没有检索到任何结果。
```

**解决**：
1. 检查 PDF 是否成功上传到 `data/knowledge/`
2. 检查 `data/chroma_db/` 是否有向量数据
3. 运行 `python debug_rag.py` 测试检索

### 问题 3：导入错误

```
❌ ModuleNotFoundError: No module named 'fitz'
```

**解决**：
```bash
pip install -r requirements.txt
```

### 问题 4：配置优先级

配置文件优先级（高 → 低）：
1. `.env` 文件（最高）
2. 环境变量
3. 代码默认值（最低）

## 📊 关键配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `EMBEDDING_PROVIDER` | `local` | embedding 服务：local / google / openai / **dashscope** |
| `DASHSCOPE_API_KEY` | 空 | 千问 API Key（必须） |
| `MINERU_API_TOKEN` | 空 | MinerU Token（必须） |
| `CHROMA_DIR` | `data/chroma_db` | 向量数据库存储位置 |
| `KNOWLEDGE_DIR` | `data/knowledge` | 知识文件目录 |
| `MEMORY_DB_PATH` | `data/tutor_memory.db` | 会话记忆数据库 |
| `KNOWLEDGE_TOP_K` | 3 | 单次检索返回的文档数 |
| `KNOWLEDGE_CHUNK_SIZE` | 1000 | 文本分块大小 |
| `KNOWLEDGE_CHUNK_OVERLAP` | 150 | 分块之间的重叠大小 |

## 🧪 完整测试流程

```bash
# 1. 验证环境
python3 -c "from ai_tutor_agent.config import get_settings; print('✅ 配置系统正常')"

# 2. 验证 RAG 模块
python3 -c "
from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider
print('✅ RAG 模块正常')
"

# 3. 启动调试工具（需要先上传 PDF 到 data/knowledge/）
python debug_rag.py

# 4. 在调试界面输入测试问题
请输入测试问题: 什么是 AI？
请输入测试问题: exit  # 退出

# 5. 启动应用
python main.py
```

## 📚 代码架构

```
LocalFileKnowledgeProvider (核心)
├── __init__()
│   ├── 初始化 Embedding 后端 (千问)
│   ├── 初始化 Chroma 向量库
│   ├── 初始化 MinerU 处理器
│   ├── 建立 BM25 索引
│   └── 自动扫描 data/knowledge/ 同步文件
├── query_hybrid()          # 混合检索
│   ├── BM25 关键词搜索
│   ├── 向量语义搜索
│   └── 融合排序
├── query_with_scores()     # 纯向量搜索 (带分数)
└── query_with_bm25()       # 纯 BM25 搜索
```

## 💡 快速命令参考

```bash
# 查看配置
grep -E "^(DASHSCOPE|MINERU|EMBEDDING|CHROMA|MEMORY)" .env

# 查看已上传的知识文件
ls -lh data/knowledge/

# 查看向量库状态
ls -lh data/chroma_db/

# 清空向量库（重新初始化）
rm -rf data/chroma_db/*

# 运行完整测试
python -m pytest tests/ -v

# 查看日志
tail -f logs/app.log
```

## 🎯 下一步

1. ✅ 上传 PDF 文件到 `data/knowledge/`
2. ✅ 运行 `python debug_rag.py` 测试检索
3. ✅ 启动 `python main.py` 运行应用
4. ✅ 在前端界面提问，观察检索结果

---

**最后更新**: 2026-03-25  
**RAG 版本**: 2.0  
**状态**: ✅ 全部配置完毕
