"""大模型配置管理接口（admin 专有）"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigResponse, LLMConfigUpdate

router = APIRouter(prefix="/api/llm-configs", tags=["大模型配置"])


@router.get("", response_model=list[LLMConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """获取所有 LLM 配置"""
    return db.query(LLMConfig).order_by(LLMConfig.id).all()


@router.post("", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    body: LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """创建新的 LLM 配置"""
    config = LLMConfig(
        name=body.name,
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
        base_url=body.base_url,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/{config_id}", response_model=LLMConfigResponse)
def update_config(
    config_id: int,
    body: LLMConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """更新 LLM 配置"""
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    for field in ["name", "provider", "model", "api_key", "base_url"]:
        value = getattr(body, field, None)
        if value is not None:
            setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.put("/{config_id}/activate", response_model=LLMConfigResponse)
def activate_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """激活指定配置 — 同时停用其他配置"""
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 停用所有配置
    db.query(LLMConfig).update({"is_active": False})
    # 激活目标配置
    config.is_active = True
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """删除 LLM 配置"""
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
