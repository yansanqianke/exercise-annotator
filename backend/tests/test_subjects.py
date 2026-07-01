"""学科管理接口测试"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import get_auth_header


class TestSubjectCreate:
    """创建学科测试"""

    def test_create_success_admin(self, client: TestClient, admin_user):
        """管理员创建学科 — 返回 201"""
        response = client.post("/api/subjects", json={
            "code": "DS",
            "name": "数据结构",
            "description": "数据结构与算法",
        }, headers=get_auth_header(admin_user))
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "DS"
        assert data["name"] == "数据结构"

    def test_create_success_teacher(self, client: TestClient, teacher_user):
        """教师创建学科 — 返回 201"""
        response = client.post("/api/subjects", json={
            "code": "OS",
            "name": "操作系统",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 201

    def test_create_duplicate_code(self, client: TestClient, admin_user):
        """学科代码重复 — 返回 400"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(admin_user))
        response = client.post("/api/subjects", json={
            "code": "DS", "name": "重复代码",
        }, headers=get_auth_header(admin_user))
        assert response.status_code == 400
        assert "代码" in response.json()["detail"]

    def test_create_unauthorized(self, client: TestClient):
        """未登录创建 — 返回 403"""
        response = client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        })
        assert response.status_code == 403


class TestSubjectList:
    """学科列表测试"""

    def test_list_empty(self, client: TestClient, teacher_user):
        """空列表 — 返回 200"""
        response = client.get("/api/subjects", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(self, client: TestClient, teacher_user):
        """有数据的列表"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/subjects", json={
            "code": "OS", "name": "操作系统",
        }, headers=get_auth_header(teacher_user))

        response = client.get("/api/subjects", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestSubjectUpdate:
    """更新学科测试"""

    def test_update_success(self, client: TestClient, admin_user):
        """更新学科名称"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(admin_user))
        response = client.put("/api/subjects/1", json={
            "name": "数据结构（新版）",
        }, headers=get_auth_header(admin_user))
        assert response.status_code == 200
        assert response.json()["name"] == "数据结构（新版）"

    def test_update_not_found(self, client: TestClient, admin_user):
        """更新不存在的学科 — 返回 404"""
        response = client.put("/api/subjects/999", json={
            "name": "不存在",
        }, headers=get_auth_header(admin_user))
        assert response.status_code == 404


class TestSubjectDelete:
    """删除学科测试"""

    def test_delete_admin(self, client: TestClient, admin_user):
        """管理员删除 — 返回 204"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(admin_user))
        response = client.delete("/api/subjects/1", headers=get_auth_header(admin_user))
        assert response.status_code == 204

    def test_delete_teacher_forbidden(self, client: TestClient, teacher_user):
        """教师删除 — 返回 403"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        response = client.delete("/api/subjects/1", headers=get_auth_header(teacher_user))
        assert response.status_code == 403

    def test_delete_not_found(self, client: TestClient, admin_user):
        """删除不存在的学科 — 返回 404"""
        response = client.delete("/api/subjects/999", headers=get_auth_header(admin_user))
        assert response.status_code == 404
