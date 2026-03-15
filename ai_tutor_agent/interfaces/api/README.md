# API Interface

当前 Web API 已拆分为以下子模块：

- `app.py`: FastAPI 应用装配入口与静态前端挂载。
- `runtime.py`: 运行时状态、SessionManager、厂商/模型目录、lifespan。
- `session.py`: 会话启动、恢复、答题、主题确认、SSE 流。
- `history.py`: 会话历史读取、摘要与删除。
- `config.py`: 快速档案切换、本机 `.env` 配置读写。
- `knowledge.py`: 本地知识库状态、文件上传、书架列表与删除。
- `adapter.py`: Web `EventSink` / `AnswerProvider` 适配层。

## 已实现端点

- `GET /api/health`
- `GET /api/config`
- `POST /api/config`
- `GET /api/config/local`
- `POST /api/config/local`
- `GET /api/history`
- `GET /api/history/{thread_id}`
- `GET /api/messages/{thread_id}`
- `DELETE /api/history/{thread_id}`
- `POST /api/start`
- `POST /api/sessions/{thread_id}/resume`
- `GET /api/stream?thread_id=...`
- `POST /api/answer`
- `POST /api/submit_assessment`
- `POST /api/confirm_topic`
- `GET /api/knowledge`
- `GET /api/knowledge/files`
- `POST /api/upload`
- `DELETE /api/knowledge/files/{filename}`
- `DELETE /api/knowledge/files`

## 约束

1. API Key 最终都只保存在服务端本机 `.env`。
2. 网页“本地配置”页只是一个写本机 `.env` 的个人开发工具，不适合共享部署。
3. 历史恢复应先读 `GET /api/history/{thread_id}`，再决定是否调用 `POST /api/sessions/{thread_id}/resume`。
4. 节点不应因为接口层变化而改成直接依赖 FastAPI 请求对象。
