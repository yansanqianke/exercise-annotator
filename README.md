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

## 运行测试

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v          # 全部 40 个测试
python -m pytest tests/ -v -k auth  # 仅认证（17）
python -m pytest tests/ -v -k subject  # 仅学科（11）
python -m pytest tests/ -v -k kp    # 仅知识点（12）
```

## 项目文档

- 需求与功能清单：[docs/task.md](docs/task.md)
- 架构设计与开发计划：[docs/plan.md](docs/plan.md)
