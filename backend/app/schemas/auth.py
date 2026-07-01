"""认证相关 Pydantic Schema — 请求 / 响应"""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(min_length=2, max_length=50, description="登录用户名")
    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    """JWT 令牌响应"""
    access_token: str = Field(description="JWT 访问令牌")
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """用户修改个人信息请求"""
    email: EmailStr | None = Field(default=None, description="新邮箱")
    password: str | None = Field(default=None, min_length=6, max_length=100, description="新密码")
