# 习题知识点标注智能体

基于 RAG + LLM 的自动标注 Web 系统。

## 技术栈

Vue3 + FastAPI + SQLite + Chroma + LlamaIndex

## 快速启动（P1 验收）

### 1. 启动后端

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

启动后访问 http://localhost:8000/health 确认返回 `{"status":"ok"}`

### 2. 启动前端

```bash
cd frontend
npm run dev
```

启动后访问 http://localhost:5173 ，可以看到登录/注册页面。

### 3. API 手动测试

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

### 4. 运行测试

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

## 项目文档

- 需求与功能清单：[docs/task.md](docs/task.md)
- 架构设计与开发计划：[docs/plan.md](docs/plan.md)
