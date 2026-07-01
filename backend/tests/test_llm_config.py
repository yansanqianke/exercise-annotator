"""大模型配置管理接口测试"""

import pytest
from fastapi.testclient import TestClient
from tests.conftest import get_auth_header


class TestLLMConfigCreate:
    """创建 LLM 配置测试"""

    def test_create_admin(self, client: TestClient, admin_user):
        """管理员创建配置 — 返回 201"""
        response = client.post("/api/llm-configs", json={
            "name": "DeepSeek Default",
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "sk-test123",
            "base_url": "https://api.deepseek.com",
        }, headers=get_auth_header(admin_user))
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "deepseek"
        assert "api_key" not in data  # API Key 不返回

    def test_create_teacher_forbidden(self, client: TestClient, teacher_user):
        """教师无权限 — 返回 403"""
        response = client.post("/api/llm-configs", json={
            "name": "test", "provider": "openai", "model": "gpt-4",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 403

    def test_create_unauthorized(self, client: TestClient):
        """未登录 — 返回 403"""
        response = client.post("/api/llm-configs", json={
            "name": "test", "provider": "openai", "model": "gpt-4",
        })
        assert response.status_code == 403


class TestLLMConfigList:
    """LLM 配置列表测试"""

    def test_list(self, client: TestClient, admin_user):
        """查看配置列表"""
        client.post("/api/llm-configs", json={
            "name": "DeepSeek", "provider": "deepseek", "model": "deepseek-chat", "api_key": "sk-test",
        }, headers=get_auth_header(admin_user))
        response = client.get("/api/llm-configs", headers=get_auth_header(admin_user))
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestLLMConfigActivate:
    """激活配置测试"""

    def test_activate(self, client: TestClient, admin_user):
        """激活指定配置 — 同一时间只有一个激活"""
        client.post("/api/llm-configs", json={
            "name": "Config A", "provider": "deepseek", "model": "deepseek-chat", "api_key": "sk-a",
        }, headers=get_auth_header(admin_user))
        client.post("/api/llm-configs", json={
            "name": "Config B", "provider": "openai", "model": "gpt-4", "api_key": "sk-b",
        }, headers=get_auth_header(admin_user))

        # 激活 Config A
        client.put("/api/llm-configs/1/activate", headers=get_auth_header(admin_user))

        # Config A 应该是激活的，Config B 不是
        configs = client.get("/api/llm-configs", headers=get_auth_header(admin_user)).json()
        assert configs[0]["is_active"] is True
        assert configs[1]["is_active"] is False

    def test_activate_not_found(self, client: TestClient, admin_user):
        """激活不存在的配置 — 返回 404"""
        response = client.put("/api/llm-configs/999/activate", headers=get_auth_header(admin_user))
        assert response.status_code == 404


class TestLLMConfigDelete:
    """删除配置测试"""

    def test_delete(self, client: TestClient, admin_user):
        """管理员删除配置"""
        client.post("/api/llm-configs", json={
            "name": "test", "provider": "openai", "model": "gpt-4", "api_key": "sk-test",
        }, headers=get_auth_header(admin_user))
        response = client.delete("/api/llm-configs/1", headers=get_auth_header(admin_user))
        assert response.status_code == 204

    def test_delete_not_found(self, client: TestClient, admin_user):
        """删除不存在 — 返回 404"""
        response = client.delete("/api/llm-configs/999", headers=get_auth_header(admin_user))
        assert response.status_code == 404
