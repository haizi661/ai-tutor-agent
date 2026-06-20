> **补充文档**: 本文为运维排障补充。完整说明书见 `docs/AI-TUTOR-AGENT-说明书.md`。

# 运行与排障手册（中文）

最后更新：2026-06-21

这份文档只回答四类问题：

1. 项目怎么启动
2. 什么时候需要代理
3. 第一次启动为什么会慢
4. 常见报错怎么处理

## 1. 启动前提

### 1.1 Python 环境

当前项目建议在你已经安装依赖的 Python 环境里运行，不要直接用系统自带解释器。

推荐方式：

```bash
cd <项目根目录>
python -m pip install -e .
```

如果你使用的是 conda/venv，先激活环境，再执行上面的命令。

### 1.2 启动命令

默认 Web 入口：

```bash
python main.py
```

CLI 调试入口：

```bash
python main.py --cli
```

Web UI 端口固定为 `8000`；如果已被旧进程占用会直接报错，不会自动换端口。`AI_TUTOR_HOST` 只控制绑定地址。

如果直接使用 uvicorn：

```bash
python -m uvicorn ai_tutor_agent.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

不要使用系统 `uvicorn`，因为它可能走错 Python 环境，导致 `ModuleNotFoundError: fastapi`。

前端没有打包流水线，浏览器直接加载 `frontend/` 下的静态文件。

## 2. 最小可运行配置

先复制样例配置：

```bash
cp .env.example .env
```

然后至少填写一个聊天厂商 key。

推荐最小配置：

```env
CHAT_PROFILE=deepseek
DEEPSEEK_API_KEY=your_key_here

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

HF_ENDPOINT_FALLBACK_ENABLED=true
LOCAL_CONFIG_ENABLED=true
```

你也可以使用：

- `GOOGLE_API_KEY`
- `QWEN_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `MINIMAX_API_KEY`
- `GLM_API_KEY`

## 3. 什么时候需要代理

### 3.1 不一定必须要代理

如果你的机器可以直接访问：

1. 你选择的聊天模型厂商 API
2. HuggingFace（当你用 `EMBEDDING_PROVIDER=local` 且本地还没有缓存模型时）

那就不需要代理。

### 3.2 需要代理的典型场景

以下场景通常需要设置代理：

1. 本地网络无法直接访问 HuggingFace
2. 本地网络无法直接访问所选模型厂商 API
3. 第一次启动时，本地 embedding 模型下载失败

### 3.3 项目支持的代理环境变量

在 `.env` 里可设置（推荐方式）：

```env
PROXY_HOST=127.0.0.1
PROXY_PORT=7897
PROXY_SCHEME=http
```

系统会自动将国外 API 地址加入代理，国内模型端点和镜像域名合并进 `NO_PROXY` 直接连接。

也兼容传统 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量：

```env
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

建议优先使用 `PROXY_HOST` / `PROXY_PORT`，因为系统会自动处理国内直连域名白名单。  
如果你本机用的是其他端口或代理程序，改成你自己的即可。

### 3.4 对代理的准确理解

代理不是项目硬依赖，而是网络受限环境下的补充条件。

准确说法是：

1. 项目本身可以在无代理环境运行
2. 但如果外部模型 API 或 HuggingFace 在你的网络里不可直连，就必须设置代理，否则：
   - 聊天模型请求会失败
   - 或本地 embedding 第一次下载会失败

## 4. 第一次启动为什么可能比较慢

如果你使用：

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

那么第一次启动时，`sentence-transformers` 可能会下载本地向量模型。

这会导致：

1. 第一次启动明显慢于后续启动
2. 如果网络不通或无代理，RAG 初始化可能失败

项目当前的真实行为是：

1. 尝试加载本地知识检索引擎
2. 如果 embedding 初始化失败，打印警告
3. 回退为“无 RAG 模式”
4. Web 和基础聊天流程仍然可以继续运行

也就是说：

- RAG 失败不一定导致整个项目启动失败
- 但会失去知识库增强能力

项目当前已内置 HuggingFace 镜像回退机制：如果默认源不可达，会自动改用 `HF_MIRROR_ENDPOINT`（默认 `https://hf-mirror.com`）。这个行为由 `HF_ENDPOINT_FALLBACK_ENABLED=true` 控制，可在 `.env` 中关闭。

## 5. 启动成功后应看到什么

正常情况下：

1. 终端会打印：

```text
🚀 启动 Web UI: http://localhost:8000
```

2. 如果本地 RAG 成功，还会看到类似：

```text
🚀 正在加载知识检索引擎 (local:sentence-transformers/all-MiniLM-L6-v2)...
✨ 成功建立本地向量索引，知识库就绪！
📚 Web: 知识库加载成功，已启用 RAG 增强。
```

3. 浏览器访问：

```text
http://127.0.0.1:8000/
```

## 6. 常见问题与判断方法

### 6.1 端口被占用

报错类似：

```text
address already in use
```

处理：

1. 关闭旧进程
2. 或换端口启动

### 6.2 `ModuleNotFoundError: fastapi`

通常不是项目缺代码，而是你用错了解释器。

处理：

```bash
python main.py
```

或：

```bash
python -m uvicorn ai_tutor_agent.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

### 6.3 启动时卡在本地 embedding

如果看到类似：

```text
正在加载知识检索引擎 (local:sentence-transformers/...)
```

说明项目正在初始化本地向量模型。

处理建议：

1. 等待第一次下载完成
2. 如果网络受限，设置 `HTTP_PROXY` / `HTTPS_PROXY`
3. 或改用：

```env
EMBEDDING_PROVIDER=google
```

或：

```env
EMBEDDING_PROVIDER=openai
```

前提是你已配置相应 key，并且对应 API 可访问。

### 6.4 浏览器打开只有 `{"detail":"Not Found"}`

这通常说明：

1. 服务没真正启动到当前代码
2. 或你访问的是旧进程

处理：

```bash
pkill -f "python main.py"
cd <项目根目录>
python main.py
```

然后浏览器强刷：

- `Ctrl + Shift + R`

### 6.5 历史会话看起来“卡住”

如果你打开历史会话后只看到旧消息，不知道该怎么继续：

1. 看顶部状态栏
2. 如果提示“等待你继续输入”，直接发下一条消息
3. 如果提示“等待确认学习主题”，就确认主题
4. 如果提示“已恢复到学前测评阶段”，就提交测评

当前项目已经修复：

1. 打开旧会话时自动覆盖上次等待状态
2. 旧会话输入被旧 worker 吞掉
3. 系统问答和学习主题在恢复场景里混淆

## 7. 当前推荐运行方式

对你现在这个项目，最稳的方式仍然是：

1. 聊天模型：任选一个已配置厂商
2. RAG：先用 `local`
3. 如果网络受限：配置 `HTTP_PROXY` / `HTTPS_PROXY`
4. 启动：

```bash
python main.py
```

如果你想确认当前项目代码状态是否健康，先执行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```
