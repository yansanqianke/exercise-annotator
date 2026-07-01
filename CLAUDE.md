# CLAUDE.md

习题知识点标注智能体 — 基于 RAG + LLM 的自动标注 Web 系统。

- 需求与功能清单：[docs/task.md](docs/task.md)
- 架构设计、数据库、API、分阶段计划：[docs/plan.md](docs/plan.md)

## 工作原则

- **CLAUDE.md 逐步扩充**：每完成一个实现阶段后追加该阶段沉淀的命令和约定，不提前写，内容不与 docs/ 已有文档重复
- **TDD 开发**：先写测试，再写实现
- **中文注释**：每个类、函数等都需要有注释，注释使用中文撰写
- **Python 环境管理**：使用 `uv` 管理 Python 依赖和虚拟环境
- **全局环境命令**：任何影响全局环境（安装系统包、修改全局 Python 等）的命令，需先获得用户允许
- **适时提交**：在合适的时机（阶段完成、功能就绪）主动进行 Git 提交
- **定期审视**：在合适的时机检查项目结构，对照 plan.md 确保没有偏离方向

## 开发命令

```bash
# 后端 — 环境安装
cd backend && uv venv && uv pip install -r requirements.txt

# 后端 — 开发服务器
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# 后端 — 数据库迁移
cd backend && source .venv/bin/activate
alembic revision --autogenerate -m "描述变更"
alembic upgrade head

# 后端 — 测试
cd backend && source .venv/bin/activate && python -m pytest tests/ -v

# 前端 — 环境安装
cd frontend && npm install

# 前端 — 开发服务器（含 API 代理到 :8000）
cd frontend && npm run dev

# 前端 — 生产构建
cd frontend && npm run build
```

## 技术笔记

- **密码哈希**：直接使用 `bcrypt` 库（`hashpw` / `checkpw`），`passlib` 与新版本 bcrypt（5.x）不兼容
- **测试数据库隔离**：使用 module 级共享 `sqlite:///:memory:` 引擎 + function 级事务回滚，避免每个测试重复建表
- **前端 API 代理**：Vite 开发服务器配置 proxy 将 `/api` 转发到 `localhost:8000`，避免跨域问题
- **Chroma 初始化**：新版本 Chroma 使用 `chromadb.PersistentClient(path=...)`，旧版 `Client(Settings(...))` 已废弃
- **知识点编码**：自动生成格式 `{学科代码}-KP-{三位序号}`，查询该学科下最大序号后递增
- **Chroma 同步容错**：知识点 CRUD 时 Chroma 同步用 try/except 包裹，失败不影响数据库操作
- **LLM 多 provider 适配**：使用 `openai` 库兼容 DeepSeek/OpenAI/Qwen，`base_url` 为空时按 provider 自动设置默认端点
- **SSE 流式输出**：前端使用原生 `fetch + ReadableStream` 接收，`useSSE.js` 封装为可复用 composable
- **标注 Prompt 设计**：LLM 返回结构化 JSON（`kp_codes` + `difficulty` + `question_type` + `reasoning`），含 `suggest_kps` 支持建议新知识点
- **双向知识库驱动**：教师可手动 CRUD 知识点，LLM 标注时也可建议新 KP（教师确认后自动入库），解决冷启动问题
- **标注模块分离**：题目导入与知识点解析解耦——题目可先入库后标注，已标注题目可重新标注
- **标注接口复用**：`POST /api/agent/annotate` 支持可选 `question_id`，传入则重新标注已有题目并覆盖结果
- **数据库模型预导入**：`main.py` 中需预导入所有模型，确保 uvicorn 启动时 SQLAlchemy 能解析所有 relationship
- **init_data.py**：初始化脚本创建默认管理员账户（admin/admin123），实际使用请在启动后尽快修改密码
