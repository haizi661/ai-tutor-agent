# AI Tutor Agent: 极致自适应伴学系统 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/Powered%20by-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

**AI Tutor Agent** 是一款基于 LangGraph 开发的动态自适应伴学系统。它不仅仅是一个聊天机器人，而是一位具备**“讲解-考核-评估-重修”**完整教学闭环的私人 AI 导师。

![Web UI Preview](https://via.placeholder.com/800x450.png?text=AI+Tutor+Agent+Web+UI+Preview) <!-- 替换为你的真实截图 -->

---

## ✨ 核心特性

- 🧠 **闭环教学引擎**：基于 LangGraph 状态机实现 `Tutor (授课)` -> `Tester (出题)` -> `Evaluator (评分)` 的严谨教学循环。
- 📊 **六维能力画像**：内置学前测评量表，动态生成 `Chart.js` 能力雷达图，真正实现“因材施教”。
- 📚 **本地/云端混合 RAG**：
  - **云端大脑**：支持 Google Gemini, 阿里云 Qwen (通义千问), DeepSeek 等主流模型切换。
  - **本地索引**：使用 `sentence-transformers` 实现本地向量化，彻底解决 PDF 解析时的网络代理痛点。
- 💻 **现代化 Web 界面**：
  - ChatGPT 风格的流式打字效果（SSE）。
  - 原生支持 **LaTeX 数学公式** 与 Markdown 渲染。
  - 完善的**历史会话管理**与一键模型切换。
- 🛠️ **开发者友好**：提供详细的 `AI_DEVELOPER_GUIDE.md`，方便使用 Cursor 或 Copilot 进行二次开发。

---

## 🚀 快速开始

### 1. 环境准备
确保你已安装 Python 3.9+。

```bash
git clone https://github.com/your-username/ai-tutor-agent.git
cd ai-tutor-agent
pip install -r requirements.txt
```

### 2. 配置环境变量
复制模板并填写你的 API Key：

```bash
cp .env.example .env
```
打开 `.env` 文件，根据你的需求填入 `GOOGLE_API_KEY` 或 `OPENAI_API_KEY`。

### 3. 启动应用
```bash
python main.py
```
访问浏览器：[http://localhost:8000](http://localhost:8000)

---

## 📂 项目结构

- `ai_tutor_agent/core/`：核心状态定义与契约。
- `ai_tutor_agent/nodes/`：Tutor、Tester、Evaluator 等智能体节点实现。
- `ai_tutor_agent/infrastructure/`：LLM 工厂、本地 RAG 检索器、SQLite 存储。
- `frontend/`：基于原生 JS 与现代 CSS 构建的沉浸式前端。

---

## 🤝 贡献与反馈

如果你喜欢这个项目，欢迎点个 **Star** 🌟！如果有任何改进建议，请提交 Issue 或 Pull Request。

## 📜 开源协议

本项目采用 [MIT License](LICENSE) 协议，你可以自由地进行学习、修改和分发。
