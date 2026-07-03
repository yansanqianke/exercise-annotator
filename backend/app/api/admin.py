"""管理后台接口 — 用户管理、智能体管理、系统日志"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.config import Agent, SystemLog
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/api/admin", tags=["管理后台"])

# ==================== 用户管理 ====================


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """获取用户列表"""
    return db.query(User).order_by(User.id).all()


class RoleUpdate(BaseModel):
    role: str = Field(description="角色：admin / teacher")


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """修改用户角色"""
    if body.role not in ("admin", "teacher"):
        raise HTTPException(status_code=400, detail="无效的角色")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


class ActiveUpdate(BaseModel):
    is_active: bool


@router.put("/users/{user_id}/active", response_model=UserResponse)
def update_user_active(
    user_id: int,
    body: ActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """启用 / 禁用用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


# ==================== 智能体管理 ====================


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="")
    agent_type: str = Field(default="annotator")
    config_json: str = Field(default="{}")
    is_active: bool = True


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    config_json: str | None = None
    is_active: bool | None = None


class AgentResponse(BaseModel):
    id: int
    name: str
    description: str
    agent_type: str
    config_json: str
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """获取智能体列表"""
    return db.query(Agent).order_by(Agent.id).all()


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    body: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """创建智能体"""
    agent = Agent(**body.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.put("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    body: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """更新智能体"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    for field in ("name", "description", "config_json", "is_active"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(agent, field, val)
    db.commit()
    db.refresh(agent)
    return agent


# ==================== 系统日志 ====================

class LogResponse(BaseModel):
    id: int
    user_id: int
    agent_id: int | None
    action: str
    input_summary: str
    tokens_used: int
    latency_ms: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[LogResponse])
def list_logs(
    user_id: int | None = Query(None),
    action: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """获取系统日志，支持按用户/动作过滤"""
    query = db.query(SystemLog)
    if user_id is not None:
        query = query.filter(SystemLog.user_id == user_id)
    if action is not None:
        query = query.filter(SystemLog.action == action)
    return query.order_by(SystemLog.id.desc()).limit(200).all()
