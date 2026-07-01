# 习题知识点标注智能体 · 系统实现计划

> 技术栈：Vue3 + FastAPI + SQLite + Chroma + LlamaIndex + DeepSeek API + Docker

---

## 目录

1. [系统架构总览](#1-系统架构总览)
2. [角色与权限设计](#2-角色与权限设计)
3. [SQLite 数据库设计](#3-sqlite-数据库设计)
4. [Chroma 向量数据库设计](#4-chroma-向量数据库设计)
5. [API 接口设计](#5-api-接口设计)
6. [核心智能体实现](#6-核心智能体实现)
7. [前端页面规划](#7-前端页面规划)
8. [分阶段实现计划](#8-分阶段实现计划)
9. [项目目录结构](#9-项目目录结构)
10. [Docker 部署](#10-docker-部署)

---

## 1. 系统架构总览

| 层次 | 技术选型 | 职责 | 说明 |
|------|---------|------|------|
| 前端 | Vue 3 + Element Plus | 用户界面 | Composition API，Pinia 状态管理，Vue Router |
| 后端 | Python 3.11 + FastAPI | 业务逻辑 / API | 异步框架，依赖注入做权限控制，SSE 流式输出 |
| 关系数据库 | SQLite + SQLAlchemy | 结构化数据持久化 | Alembic 做迁移管理 |
| 向量数据库 | Chroma | 语义检索 | 嵌入 Python 进程，无需独立服务 |
| RAG 框架 | LlamaIndex | 文档索引 / 检索 | 负责分块、嵌入、查询管道 |
| 大模型 | DeepSeek API | 标注推理 / 对话 | 配置页支持切换 OpenAI / Qwen |
| 文档解析 | pdfplumber + python-docx + python-pptx | 提取原始文本 | 两种场景：参考资料索引、题目文档提取 |
| 部署 | Docker Compose | 容器化一键部署 | 前端 Nginx 容器 + 后端 Python 容器 |

### 整体数据流

```
┌─ 浏览器 (Vue3) ─────────────────────────────────────────┐
│  管理页面  ─── HTTPS/REST ───→  FastAPI  ──→ SQLite      │
│  标注页面  ─── SSE Stream  ───→  Agent   ──→ Chroma      │
└─────────────────────────────────────────────────────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
            LlamaIndex          DeepSeek          SQLite
         (文档索引/检索)        (LLM 推理)       (结果持久化)
```

---

## 2. 角色与权限设计

系统设置 **管理员（admin）** 和 **教师（teacher）** 两个角色。

> **可扩展性说明**：角色字段使用字符串枚举，权限声明采用白名单模式（`require_role(["admin", "teacher"])`），后续添加 `student` 角色无需修改数据库结构，约 2-4 小时工作量。

| 功能模块 | 管理员 | 教师 |
|---------|--------|------|
| 用户管理（查看 / 修改角色 / 禁用） | ✅ | ✗ |
| 大模型配置（API Key / 模型切换） | ✅ | ✗ |
| 智能体管理（配置标注参数） | ✅ | ✗ |
| 系统日志查看 | ✅ | ✗ |
| 学科管理（CRUD） | ✅ | ✅ |
| 知识点管理（CRUD，共享库） | ✅ | ✅ |
| 题目标注（使用智能体） | ✅ | ✅ |
| 文档上传（参考资料 / 题目文档） | ✅ | ✅ |
| 查看标注结果 | ✅ | ✅ |
| 查看相似知识点推荐 | ✅ | ✅ |

---

## 3. SQLite 数据库设计

### users — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `username` | VARCHAR(50) UNIQUE | 登录用户名 |
| `email` | VARCHAR(100) UNIQUE | 邮箱 |
| `password_hash` | VARCHAR(128) | bcrypt 哈希 |
| `role` | VARCHAR(20) | `admin` / `teacher`（字符串枚举，便于扩展） |
| `is_active` | BOOLEAN | 账号是否启用 |
| `created_at` | DATETIME | 注册时间 |

### subjects — 学科表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `code` | VARCHAR(10) UNIQUE | 学科代码，如 `DS`、`OS` |
| `name` | VARCHAR(100) | 学科名称，如"数据结构" |
| `description` | TEXT | 简介 |
| `created_by` | FK → users | 创建者 |
| `created_at` | DATETIME | |

### knowledge_points — 知识点表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `subject_id` | FK → subjects | 所属学科 |
| `code` | VARCHAR(20) UNIQUE | 自动生成，格式 `DS-KP-001` |
| `name` | VARCHAR(100) | 知识点名称 |
| `description` | TEXT | 详细描述，也是嵌入的文本来源 |
| `created_by` | FK → users | 审计用，非所有权 |
| `is_deleted` | BOOLEAN DEFAULT 0 | 软删除，不物理删除向量 |
| `created_at` / `updated_at` | DATETIME | |

### questions — 题目表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `subject_id` | FK → subjects | 所属学科 |
| `content` | TEXT | 题目正文 |
| `type` | VARCHAR(20) | `choice` / `judgment` / `short_answer` / `programming` |
| `difficulty` | INTEGER | 1–5，由 LLM 标注 |
| `source_doc_id` | FK → documents NULL | 来自哪个文档（批量导入时填写） |
| `created_by` | FK → users | |
| `created_at` | DATETIME | |

### question_kp_map — 题目-知识点关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `question_id` | FK → questions | |
| `kp_id` | FK → knowledge_points | |
| `confidence` | FLOAT | LLM 输出的置信度 0.0–1.0 |
| `is_manual` | BOOLEAN | 是否为教师手动修正 |

### documents — 文档表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `filename` | VARCHAR(200) | 服务器存储路径 |
| `original_name` | VARCHAR(200) | 原始文件名 |
| `doc_type` | VARCHAR(20) | `reference`（参考资料）/ `questions`（题目文档） |
| `subject_id` | FK → subjects | |
| `status` | VARCHAR(20) | `pending` / `processing` / `done` / `failed` |
| `created_by` | FK → users | |
| `created_at` | DATETIME | |

### llm_configs — 大模型配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(50) | 配置名称 |
| `provider` | VARCHAR(20) | `openai` / `qwen` / `deepseek` |
| `model` | VARCHAR(50) | 如 `deepseek-chat` |
| `api_key` | VARCHAR(200) | 加密存储 |
| `base_url` | VARCHAR(200) | 自定义 API 端点 |
| `is_active` | BOOLEAN | 当前使用的配置（同时只有一个激活） |

### agents — 智能体表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(100) | 智能体名称 |
| `description` | TEXT | 功能介绍 |
| `agent_type` | VARCHAR(20) | `annotator` / `chat` |
| `config_json` | TEXT | JSON 格式，存储 top_k、温度等参数 |
| `is_active` | BOOLEAN | |

### system_logs — 系统日志表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | |
| `user_id` | FK → users | |
| `agent_id` | FK → agents NULL | 关联的智能体 |
| `action` | VARCHAR(50) | `annotate` / `chat` / `index_doc` 等 |
| `input_summary` | TEXT | 输入摘要（前 100 字） |
| `tokens_used` | INTEGER | 本次调用消耗 token 数 |
| `latency_ms` | INTEGER | 耗时毫秒 |
| `status` | VARCHAR(20) | `success` / `error` |
| `created_at` | DATETIME | |

---

## 4. Chroma 向量数据库设计

系统使用两个 Collection：

### Collection: `kp_store`

- **用途 1**：标注时语义检索 top-K 候选知识点
- **用途 2**：知识点相似推荐
- **嵌入文本**：`{name}: {description}`
- **Metadata**：`kp_id`、`subject_id`、`code`
- **更新时机**：知识点创建 / 修改 / 软删除时同步

### Collection: `ref_materials`

- **用途**：标注时提供参考资料上下文
- **分块策略**：512 token，overlap 64
- **Metadata**：`doc_id`、`subject_id`、`chunk_index`
- **更新时机**：文档上传并触发索引后写入

### 相似知识点推荐实现

```python
async def get_similar_kps(kp_id: int, top_k: int = 5) -> list:
    kp = db.get_kp(kp_id)
    results = chroma_kp_store.query(
        query_texts=[f"{kp.name}: {kp.description}"],
        n_results=top_k + 1   # +1 排除自身
    )
    return [r for r in results["metadatas"][0] if r["kp_id"] != kp_id]
```

这是标注管道已有向量库的零成本附赠功能，无需额外模型或数据结构。

---

## 5. API 接口设计

> **协议约定**：管理类接口统一 HTTPS REST；智能体调用接口（标注 / 对话）统一 SSE 流式传输，前端使用 `fetch + ReadableStream` 接收。

### 认证 `/api/auth`

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| POST | `/api/auth/register` | 公开 | 用户注册，默认角色 teacher |
| POST | `/api/auth/login` | 公开 | 返回 JWT Token |
| GET | `/api/auth/me` | 登录用户 | 获取当前用户信息 |
| PUT | `/api/auth/me` | 登录用户 | 修改个人信息 / 密码 |

### 用户管理 `/api/users`

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| GET | `/api/users` | admin | 用户列表（分页） |
| PUT | `/api/users/{id}/role` | admin | 修改用户角色 |
| PUT | `/api/users/{id}/active` | admin | 启用 / 禁用账号 |

### 学科 & 知识点 `/api/subjects` · `/api/kps`

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| GET | `/api/subjects` | teacher+ | 学科列表 |
| POST | `/api/subjects` | teacher+ | 创建学科 |
| PUT | `/api/subjects/{id}` | teacher+ | 更新学科 |
| DELETE | `/api/subjects/{id}` | admin | 删除学科 |
| GET | `/api/kps?subject_id=` | teacher+ | 知识点列表（按学科过滤） |
| POST | `/api/kps` | teacher+ | 创建知识点，自动嵌入写入 Chroma |
| PUT | `/api/kps/{id}` | teacher+ | 更新，同步更新 Chroma |
| DELETE | `/api/kps/{id}` | teacher+ | 软删除，Chroma 同步标记 |
| GET | `/api/kps/{id}/similar` | teacher+ | 相似知识点推荐 |
| POST | `/api/kps/batch-import` | teacher+ | 批量导入知识点（JSON / CSV） |

### 题目 `/api/questions`

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| GET | `/api/questions` | teacher+ | 题目列表，支持按学科 / 题型 / 难度过滤 |
| GET | `/api/questions/{id}` | teacher+ | 题目详情 + 标注结果 |
| PUT | `/api/questions/{id}/kps` | teacher+ | 手动修正知识点标注 |
| DELETE | `/api/questions/{id}` | teacher+ | 删除题目 |

### 文档 `/api/documents`

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| POST | `/api/documents/upload` | teacher+ | 上传文件（multipart），`doc_type` 指定类型 |
| GET | `/api/documents` | teacher+ | 文档列表 |
| POST | `/api/documents/{id}/index` | teacher+ | 将参考资料解析并写入 Chroma |
| POST | `/api/documents/{id}/extract` | teacher+ | 从题目文档提取题目列表（LLM 解析） |

### 配置 & 日志

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| CRUD | `/api/llm-configs` | admin | 管理大模型配置，`PUT /{id}/activate` 切换激活 |
| CRUD | `/api/agents` | admin | 管理智能体配置 |
| GET | `/api/logs` | admin | 系统日志，支持按用户 / 日期 / 动作过滤 |

### 智能体调用（SSE 接口）

| Method | 路径 | 权限 | 说明 |
|--------|------|------|------|
| POST | `/api/agent/annotate` | teacher+ | 单题标注，SSE 流式返回推理过程 + 最终 JSON |
| POST | `/api/agent/chat` | teacher+ | 大模型对话，SSE 流式输出 |
| POST | `/api/agent/batch-annotate` | teacher+ | 批量标注，SSE 逐题推送进度 |

**SSE 事件格式约定：**

```json
// 推理过程（流式文字）
{"type": "thinking", "content": "正在检索相关知识点..."}

// 最终结构化结果
{"type": "result", "kps": ["DS-KP-006", "DS-KP-007"], "difficulty": 3, "question_type": "programming"}

// 结束信号
{"type": "done"}
```

---

## 6. 核心智能体实现

### RAG 标注管道（完整流程）

```
① 接收题目输入
   POST body: { content, subject_id, type_hint? }
   SSE 连接建立，开始推送事件
        │
        ▼
② 双路并行检索
   ├─ kp_store:      语义检索 top-10 候选知识点（按 subject_id 过滤）
   └─ ref_materials: 语义检索 top-3 相关参考段落
        │
        ▼
③ 构造 Prompt
   注入候选 KP 列表 + 参考段落
   要求输出固定 JSON Schema
        │
        ▼
④ DeepSeek API 流式调用
   推理过程 → SSE "thinking" 事件 → 前端实时展示
   最终输出 → JSON 解析为结构化结果
        │
        ▼
⑤ 结果验证 & 持久化
   校验 KP 编码是否存在于数据库
   ── 存在的编码 → 写入 question_kp_map
   ── suggest_kps 建议 → 推送给前端，教师确认后自动入库
   记录 system_logs
        │
        ▼
⑥ 推送最终结果 & 关闭 SSE
   推送 "result" 事件（含已有 KP + 建议新 KP）
   推送 "done" 事件，关闭连接
```

### 标注 Prompt 模板

```
系统角色：你是一个专业的教育领域知识点标注专家。

候选知识点列表（来自 {subject_name} 学科）：
{kp_list}

参考资料上下文：
{ref_context}

请分析以下题目，完成三项标注任务。
输出必须是合法 JSON，格式严格如下：
{
  "kp_codes": ["DS-KP-XXX", ...],   // 涉及的知识点编码，1-5个，无匹配则 []
  "suggest_kps": [                  // 建议新增知识点，无建议则 []
    {"name": "知识点名称", "description": "简要描述"}
  ],
  "difficulty": 3,                   // 难度 1(易)-5(难)
  "question_type": "programming",    // choice/judgment/short_answer/programming
  "reasoning": "..."                 // 简要说明标注依据
}

题目内容：
{question_content}
```

### 知识点库双向驱动设计

解决知识点库"冷启动"问题——标注依赖知识库，但知识库可能不完整：

```
教师手动创建 KP ──────┐
                      ▼
                 Chroma 向量库
                      ▲
LLM 分析题目 → 建议新 KP（教师确认后入库）
```

- 标注时 LLM 可在 `suggest_kps` 中建议不存在于候选列表的新知识点
- 前端展示建议，教师点击"确认入库"后自动创建 KP 并写入 Chroma
- 下次标注时，新知识点已可用

### 文档解析两种场景

**场景 A：参考资料 → Chroma 索引**

```
pdfplumber / python-docx 提取全文
    → LlamaIndex SimpleDirectoryReader 加载
    → SentenceSplitter 分块（512 token，overlap 64）
    → 嵌入写入 ref_materials Collection
```

**场景 B：题目文档 → 批量标注**

```
解析器提取全文
    → LLM 结构化提取题目列表（JSON 数组）
    → 逐题调用标注管道
    → SSE 逐题推送进度（"正在处理第 3/20 题..."）
```

---

## 7. 前端页面规划

| 路由 | 页面名称 | 权限 | 核心内容 |
|------|---------|------|---------|
| `/login` | 登录 | 公开 | JWT 登录表单 |
| `/register` | 注册 | 公开 | 注册表单，角色默认 teacher |
| `/` | 首页 Dashboard | teacher+ | 统计卡片（题目数 / 知识点数 / 调用次数）、最近标注记录 |
| `/profile` | 个人信息 | teacher+ | 修改用户名 / 邮箱 / 密码 |
| `/subjects` | 学科管理 | teacher+ | 学科列表，CRUD 操作 |
| `/knowledge-points` | 知识点管理 | teacher+ | 按学科分组列表，CRUD，查看相似 KP |
| `/documents` | 文档管理 | teacher+ | 上传 / 管理参考资料和题目文档，触发索引 / 提取 |
| `/annotate` | **题目标注（核心）** | teacher+ | 输入题目 → SSE 流式展示推理过程 → 显示标注结果 → 支持手动修正 |
| `/questions` | 题目列表 | teacher+ | 已标注题目列表，筛选 / 查看详情 |
| `/chat` | 大模型对话 | teacher+ | 普通对话界面，SSE 流式输出 |
| `/agents` | 智能体介绍 | teacher+ | 展示系统内智能体，功能说明 |
| `/admin/users` | 用户管理 | admin | 用户列表，角色修改，启用 / 禁用 |
| `/admin/llm-config` | 大模型配置 | admin | 配置 API Key、模型、端点，切换激活配置 |
| `/admin/agent-config` | 智能体管理 | admin | 管理智能体参数（top_k、温度等） |
| `/admin/logs` | 系统日志 | admin | 调用历史，按用户 / 日期过滤，Token 统计 |

---

## 8. 分阶段实现计划

总计约 **9–10 天**。

### P1 · 项目脚手架 + 数据库 + JWT 认证（1.5 天）

- FastAPI 项目结构，SQLAlchemy 模型定义，Alembic 初始迁移
- 注册 / 登录接口，JWT 签发与验证，角色权限中间件
- Vue3 项目初始化（Vite + Pinia + Vue Router），路由守卫，登录 / 注册页

### P2 · 学科 & 知识点 CRUD + Chroma 集成（1.5 天）

- 学科 / 知识点 REST API 实现
- Chroma 初始化，知识点写入 / 更新 / 删除同步向量库
- 相似知识点推荐接口
- 前端：学科管理页、知识点管理页

### P3 · 大模型配置 + SSE 基础对话（1 天）

- LLM 配置 CRUD，多 provider 适配（DeepSeek / OpenAI / Qwen）
- SSE 对话接口（`/api/agent/chat`）
- 前端：大模型配置页、对话页

### P4 · 核心标注智能体（RAG 管道）（2 天）

- LlamaIndex 检索管道搭建（双路检索：kp_store + ref_materials）
- Prompt 模板，结构化 JSON 输出解析
- SSE 标注接口（`/api/agent/annotate`），结果持久化
- 前端：题目标注页（流式推理展示 + 结果确认 + 手动修正）

### P5 · 文档解析（两种场景）（1.5 天）

- pdfplumber / python-docx / python-pptx 文本提取
- 场景 A：参考资料 → LlamaIndex 分块嵌入 → Chroma
- 场景 B：题目文档 → LLM 提取题目列表 → 批量标注 SSE 进度
- 前端：文档管理页、批量标注进度展示

### P6 · 管理后台页面 + 系统日志（1 天）

- 用户管理页（角色分配、启用 / 禁用）
- 智能体管理页（参数配置）
- 系统日志页（调用历史、Token 统计）
- 首页 Dashboard（统计卡片）

### P7 · Docker 部署 + 初始化脚本 + README（0.5 天）

- 后端 Dockerfile（python:3.11-slim）
- 前端 Dockerfile（Node build → Nginx serve）
- Docker Compose（volume 挂载 SQLite + Chroma 数据目录）
- 数据初始化脚本（默认管理员账号、示例学科 / 知识点）
- README（环境变量说明、一键启动命令）

---

## 9. 项目目录结构

### 后端 `backend/`

```
backend/
├── app/
│   ├── api/                # 路由层
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── subjects.py
│   │   ├── kps.py
│   │   ├── questions.py
│   │   ├── documents.py
│   │   ├── agent.py        # SSE 接口
│   │   └── admin.py
│   ├── core/
│   │   ├── config.py       # 环境变量
│   │   ├── security.py     # JWT
│   │   └── deps.py         # 依赖注入 / 权限
│   ├── models/             # SQLAlchemy ORM 模型
│   ├── schemas/            # Pydantic 请求/响应模型
│   ├── services/
│   │   ├── llm.py          # LLM 客户端（多 provider）
│   │   ├── rag.py          # LlamaIndex 检索管道
│   │   ├── annotator.py    # 标注智能体核心逻辑
│   │   └── parser.py       # 文档解析
│   └── main.py
├── alembic/                # 数据库迁移脚本
├── init_data.py            # 初始化脚本
├── requirements.txt
└── Dockerfile
```

### 前端 `frontend/`

```
frontend/
├── src/
│   ├── views/
│   │   ├── auth/           # 登录 / 注册
│   │   ├── annotate/       # 核心标注页
│   │   ├── kps/            # 知识点管理
│   │   ├── questions/      # 题目列表
│   │   ├── documents/      # 文档管理
│   │   ├── chat/           # 对话页
│   │   └── admin/          # 管理后台页面
│   ├── stores/             # Pinia
│   │   ├── auth.js
│   │   └── config.js
│   ├── composables/
│   │   └── useSSE.js       # SSE 封装 hook
│   ├── api/                # axios 请求封装
│   ├── router/             # 路由 + 角色守卫
│   └── main.js
├── nginx.conf
├── Dockerfile
└── vite.config.js
```

### 根目录

```
project-root/
├── backend/
├── frontend/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 10. Docker 部署

### docker-compose.yml

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data/sqlite:/app/data       # SQLite 持久化
      - ./data/chroma:/app/chroma     # Chroma 持久化
      - ./data/uploads:/app/uploads   # 上传文件
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
```

### 环境变量 `.env`

```env
# 大模型
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxx
LLM_BASE_URL=https://api.deepseek.com

# 安全
JWT_SECRET_KEY=your-secret-key-change-this
JWT_EXPIRE_HOURS=24

# 路径
SQLITE_PATH=/app/data/app.db
CHROMA_PATH=/app/chroma
UPLOAD_PATH=/app/uploads
```

### 一键启动

```bash
# 初次启动
cp .env.example .env          # 填写 API Key
docker compose up -d --build
docker compose exec backend python init_data.py   # 初始化默认数据

# 之后启动
docker compose up -d
```

> **注意**：Chroma 和 SQLite 数据通过 volume 挂载到宿主机 `./data/` 目录，容器重建不会丢失数据。
