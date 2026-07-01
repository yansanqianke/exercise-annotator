# 习题知识点标注智能体

基于 RAG + LLM 的自动标注 Web 系统。

## 技术栈

Vue3 + FastAPI + SQLite + Chroma + LlamaIndex

## 快速启动

```bash
# 后端
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend && npm run dev
```

- 后端：http://localhost:8000/health → `{"status":"ok"}`
- 前端：http://localhost:5173

## API 手动测试

### P1 · 认证

```bash
# 注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"123456"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 获取个人信息（替换 TOKEN）
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

### P2 · 学科 & 知识点

```bash
TOKEN="<登录获取的 token>"

# 创建学科
curl -X POST http://localhost:8000/api/subjects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"code":"DS","name":"数据结构","description":"数据结构与算法"}'

# 查看学科列表
curl http://localhost:8000/api/subjects -H "Authorization: Bearer $TOKEN"

# 创建知识点（自动生成编码 DS-KP-001）
curl -X POST http://localhost:8000/api/kps \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"subject_id":1,"name":"链表","description":"单链表、双链表的基本操作"}'

# 查看知识点列表
curl http://localhost:8000/api/kps -H "Authorization: Bearer $TOKEN"

# 相似知识点推荐
curl http://localhost:8000/api/kps/1/similar -H "Authorization: Bearer $TOKEN"
```

前端页面：登录后可访问 `/subjects`（学科管理）和 `/knowledge-points`（知识点管理）。

### P3 · 大模型对话

```bash
# 管理员创建 LLM 配置（需先登录获取 TOKEN）
curl -X POST http://localhost:8000/api/llm-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"DeepSeek","provider":"deepseek","model":"deepseek-chat","api_key":"sk-xxx"}'

# 激活配置
curl -X PUT http://localhost:8000/api/llm-configs/1/activate \
  -H "Authorization: Bearer $TOKEN"

# SSE 对话（前端 /chat 页面更直观）
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"messages":[{"role":"user","content":"你是谁"}]}'
```

前端页面：`/admin/llm-config`（管理员配置大模型）和 `/chat`（AI 对话）。

### P4 · 题目标注

前端页面 `/annotate`：
1. 选择学科 → 输入题目内容 → 点击"开始标注"
2. 观察流式推理过程
3. 查看标注结果（题型、难度、知识点编码、推理依据）
4. 如有建议新知识点，教师可点击"确认入库"
5. 已标注题目列表中可手动修正

```bash
# SSE 标注（前端更直观）
curl -X POST http://localhost:8000/api/agent/annotate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content":"给定一个单链表，请编写函数反转链表","subject_id":1}'
```

### P5 · 文档解析

前端页面 `/documents`：
1. 上传 PDF/Word/PPT/TXT 文档，选择"参考资料"或"题目文档"类型
2. 参考资料 → 点击"索引"将内容分块写入 Chroma，供标注管道检索
3. 题目文档 → 点击"提取题目"由 LLM 提取题目列表

```bash
# 上传文档
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@example.pdf" -F "doc_type=reference" -F "subject_id=1"
```

## 运行测试

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v          # 全部 48 个测试
python -m pytest tests/ -v -k auth  # 仅认证（17）
python -m pytest tests/ -v -k subject  # 仅学科（11）
python -m pytest tests/ -v -k kp    # 仅知识点（12）
python -m pytest tests/ -v -k llm   # 仅 LLM 配置（8）
```

## 项目文档

- 需求与功能清单：[docs/task.md](docs/task.md)
- 架构设计与开发计划：[docs/plan.md](docs/plan.md)
