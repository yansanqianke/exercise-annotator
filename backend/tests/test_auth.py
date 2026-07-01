"""认证接口测试"""

import pytest
from fastapi.testclient import TestClient


class TestRegister:
    """用户注册测试"""

    def test_register_success(self, client: TestClient):
        """正常注册 — 返回 JWT 令牌"""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_default_role_is_teacher(self, client: TestClient):
        """注册用户默认角色为 teacher"""
        response = client.post("/api/auth/register", json={
            "username": "newuser2",
            "email": "newuser2@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        # 用返回的 token 获取用户信息验证角色
        token = response.json()["access_token"]
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.json()["role"] == "teacher"

    def test_register_duplicate_username(self, client: TestClient, admin_user):
        """重复用户名注册 — 返回 400"""
        response = client.post("/api/auth/register", json={
            "username": "admin",  # 已存在
            "email": "other@example.com",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, admin_user):
        """重复邮箱注册 — 返回 400"""
        response = client.post("/api/auth/register", json={
            "username": "othername",
            "email": "admin@example.com",  # 已存在
            "password": "password123",
        })
        assert response.status_code == 400
        assert "邮箱已被注册" in response.json()["detail"]

    def test_register_short_password(self, client: TestClient):
        """密码过短 — 422 校验错误"""
        response = client.post("/api/auth/register", json={
            "username": "user",
            "email": "user@example.com",
            "password": "12345",  # 少于 6 位
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """无效邮箱格式 — 422 校验错误"""
        response = client.post("/api/auth/register", json={
            "username": "user",
            "email": "not-an-email",
            "password": "password123",
        })
        assert response.status_code == 422


class TestLogin:
    """用户登录测试"""

    def test_login_success(self, client: TestClient, teacher_user):
        """正确用户名密码 — 返回 JWT"""
        response = client.post("/api/auth/login", json={
            "username": "teacher",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, teacher_user):
        """错误密码 — 返回 401"""
        response = client.post("/api/auth/login", json={
            "username": "teacher",
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """不存在的用户 — 返回 401"""
        response = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "password",
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db_session):
        """被禁用的用户 — 返回 403"""
        from app.models.user import User
        from app.core.security import hash_password

        inactive = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            role="teacher",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        response = client.post("/api/auth/login", json={
            "username": "inactive",
            "password": "password123",
        })
        assert response.status_code == 403
        assert "账号已被禁用" in response.json()["detail"]


class TestGetMe:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client: TestClient, teacher_user):
        """有效 token — 返回用户信息"""
        from tests.conftest import get_auth_header
        response = client.get("/api/auth/me", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "teacher"
        assert data["email"] == "teacher@example.com"
        assert data["role"] == "teacher"

    def test_get_me_without_token(self, client: TestClient):
        """无 token — 返回 403（HTTPBearer 拦截）"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_get_me_invalid_token(self, client: TestClient):
        """无效 token — 返回 401"""
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401


class TestUpdateMe:
    """修改个人信息测试"""

    def test_update_email_success(self, client: TestClient, teacher_user):
        """修改邮箱成功"""
        from tests.conftest import get_auth_header
        response = client.put("/api/auth/me", json={
            "email": "newemail@example.com",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    def test_update_password_success(self, client: TestClient, teacher_user):
        """修改密码成功 — 之后可用新密码登录"""
        from tests.conftest import get_auth_header
        response = client.put("/api/auth/me", json={
            "password": "newpassword123",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 200

        # 用新密码登录
        login_resp = client.post("/api/auth/login", json={
            "username": "teacher",
            "password": "newpassword123",
        })
        assert login_resp.status_code == 200

    def test_update_duplicate_email(self, client: TestClient, teacher_user, admin_user):
        """修改为已被他人使用的邮箱 — 返回 400"""
        from tests.conftest import get_auth_header
        response = client.put("/api/auth/me", json={
            "email": "admin@example.com",  # admin 已占用
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 400
        assert "邮箱已被使用" in response.json()["detail"]

    def test_update_without_token(self, client: TestClient):
        """无 token — 返回 403"""
        response = client.put("/api/auth/me", json={"email": "x@x.com"})
        assert response.status_code == 403
