# 仓库卫生与上传边界（中文）

## 1. 哪些文件不要上传

以下内容属于本地运行态或机密信息，不应该提交到 GitHub：

- `.env`
- `data/*.db`
- `data/*.db-wal`
- `data/*.db-shm`
- `data/knowledge/*` 下的本地 PDF / TXT / MD 资料
- `*.log`
- `.pytest_cache/`、`__pycache__/`、`.coverage`、`htmlcov/`

## 2. 为什么不要上传

1. `.env` 含 API Key、代理等敏感信息。
2. SQLite 数据库和 `-wal/-shm` 文件属于本地状态，不是源码。
3. 本地知识库文件可能有版权或隐私问题。
4. 缓存与日志会污染 PR，增加协作者审查成本。

## 3. 提交前标准检查

```bash
git status -sb
git diff
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

检查重点：

1. 只提交代码、测试、文档。
2. 不要把运行时数据库、临时日志、下载模型缓存混入 commit。
3. 如果 `git status` 出现 `data/tutor_memory.db-wal` 或 `data/tutor_memory.db-shm`，不用提交。

## 4. 知识库目录如何管理

当前约定：

- 目录保留：`data/knowledge/.gitkeep`
- 真实资料文件不提交
- 如果团队需要共享一套公开资料，应单独放到明确的版本化目录，并先确认版权和体积

## 5. 本地配置页的边界

网页“本地配置”页本质上是写回当前机器的 `.env`。因此：

- 适合个人本地开发
- 不适合多人共享服务器
- 不应把改完的 `.env` 提交到仓库

## 6. 推荐协作习惯

1. 开发前：`git pull --rebase`
2. 提交前：跑测试
3. 发 PR 前：确认 `git status` 中没有 `.env`、数据库、知识库原始文件
4. 需要共享配置时：修改 `.env.example` 和 README，而不是提交自己的 `.env`
