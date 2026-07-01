# 习题知识点标注智能体

基于 RAG + LLM 的自动标注 Web 系统，支持教师手动管理知识点库 + LLM 自动匹配标注，双向驱动解决冷启动问题。

## 技术栈

Vue3 + FastAPI + SQLite + Chroma + DeepSeek（兼容 OpenAI / Qwen）

## 快速启动

### 1. 安装依赖

```bash
cd backend && uv venv && uv pip install -r requirements.txt   # Python
cd frontend && npm install                                     # Node
```

### 2. 初始化数据

```bash
cd backend && source .venv/bin/activate
alembic upgrade head     # 创建数据库表
python init_data.py      # 默认管理员 + 示例学科/知识点
```

### 3. 启动服务

```bash
# 终端 1 — 后端
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 终端 2 — 前端
cd frontend && npm run dev
```

- 后端：http://localhost:8000/health
- 前端：http://localhost:5173

### 4. 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

首次使用：管理员登录 → 配置大模型 → 激活 → 即可标注。

---

## 功能概览

### 知识点管理 `/knowledge-points`

教师手动 CRUD 知识点（也可在标注时由 LLM 建议创建）。创建后自动编码并写入 Chroma 向量库，支持相似知识点推荐。

### 题目标注 `/annotate`（核心功能）

分为两个子模块：

**题目导入**：手动输入或文档提取 → 保存到题库。支持"仅保存"或"保存并立即标注"。

**知识点解析**：对题库中已有题目执行 RAG 标注。
1. 点击题目行"标注"按钮 → LLM 流式推理
2. 自动输出：匹配的知识点、难度 (1-5)、题型、推理依据
3. 若库中无匹配知识点，LLM 建议新 KP，教师确认后自动入库
4. 已标注题目可重新标注（覆盖旧结果）或手动修正 KP

### 文档解析 `/documents`

上传 PDF / Word / PPT / TXT 文档：
- **参考资料** → 索引分块写入 Chroma，供标注管道语义检索
- **题目文档** → LLM 自动提取题目并入库

### AI 对话 `/chat`

SSE 流式通用对话，支持 DeepSeek / OpenAI / Qwen。

### 管理后台（admin 专有）

| 页面 | 功能 |
|------|------|
| `/admin/llm-config` | 大模型配置（API Key、模型切换、激活） |
| `/admin/users` | 用户管理（角色分配、启用/禁用） |
| `/admin/agents` | 智能体参数配置 |
| `/admin/logs` | 系统调用日志 |

---

## 运行测试

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v         # 全部 48 个
python -m pytest tests/ -v -k auth # 认证
python -m pytest tests/ -v -k kp   # 知识点
```

---

## 项目结构

```
backend/
├── app/
│   ├── api/          # REST & SSE 路由
│   ├── core/         # 配置、安全、依赖注入
│   ├── models/       # SQLAlchemy ORM 模型
│   ├── schemas/      # Pydantic 请求/响应
│   └── services/     # LLM、Chroma、标注、文档解析
├── tests/            # pytest 测试
├── alembic/          # 数据库迁移
└── init_data.py      # 初始化脚本

frontend/
├── src/
│   ├── views/        # 页面组件
│   ├── composables/  # 可复用逻辑（useSSE）
│   ├── api/          # axios 请求封装
│   ├── stores/       # Pinia 状态管理
│   └── router/       # 路由 + 守卫
└── vite.config.js    # API 代理配置
```

---

## 环境变量

复制 `.env.example` 为 `.env`，按需修改：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
JWT_SECRET_KEY=change-me
SQLITE_PATH=data/app.db
CHROMA_PATH=data/chroma
```

开发阶段也可在 `/admin/llm-config` 页面配置大模型。

## 项目文档

- 需求与功能清单：[docs/task.md](docs/task.md)
- 架构设计与开发计划：[docs/plan.md](docs/plan.md)
