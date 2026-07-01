"""知识点管理接口测试"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import get_auth_header


class TestKPCreate:
    """创建知识点测试"""

    @pytest.fixture(autouse=True)
    def setup_subject(self, client, teacher_user):
        """每个测试前创建学科依赖"""
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))

    def test_create_success(self, client, teacher_user):
        """创建知识点 — 返回 201，自动生成编码"""
        response = client.post("/api/kps", json={
            "subject_id": 1,
            "name": "链表",
            "description": "单链表、双链表的基本操作",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "DS-KP-001"
        assert data["name"] == "链表"

    def test_create_multiple_kps_increments_code(self, client, teacher_user):
        """连续创建知识点，编码自增"""
        client.post("/api/kps", json={
            "subject_id": 1, "name": "链表",
        }, headers=get_auth_header(teacher_user))
        response = client.post("/api/kps", json={
            "subject_id": 1, "name": "栈",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 201
        assert response.json()["code"] == "DS-KP-002"

    def test_create_subject_not_found(self, client, teacher_user):
        """学科不存在 — 返回 404"""
        response = client.post("/api/kps", json={
            "subject_id": 999,
            "name": "不存在的知识点",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 404

    def test_create_unauthorized(self, client):
        """未登录 — 返回 403"""
        response = client.post("/api/kps", json={
            "subject_id": 1, "name": "链表",
        })
        assert response.status_code == 403


class TestKPList:
    """知识点列表测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, teacher_user):
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/subjects", json={
            "code": "OS", "name": "操作系统",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/kps", json={
            "subject_id": 1, "name": "链表",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/kps", json={
            "subject_id": 2, "name": "进程",
        }, headers=get_auth_header(teacher_user))

    def test_list_all(self, client, teacher_user):
        """不按学科过滤 — 返回全部"""
        response = client.get("/api/kps", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_filter_by_subject(self, client, teacher_user):
        """按学科过滤"""
        response = client.get("/api/kps?subject_id=1", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["code"] == "DS-KP-001"


class TestKPUpdate:
    """更新知识点测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, teacher_user):
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/kps", json={
            "subject_id": 1, "name": "链表",
        }, headers=get_auth_header(teacher_user))

    def test_update_success(self, client, teacher_user):
        """更新知识点名称和描述"""
        response = client.put("/api/kps/1", json={
            "name": "链表（修订版）",
            "description": "增加了循环链表",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "链表（修订版）"
        assert "循环链表" in data["description"]

    def test_update_not_found(self, client, teacher_user):
        """更新不存在 — 返回 404"""
        response = client.put("/api/kps/999", json={
            "name": "不存在",
        }, headers=get_auth_header(teacher_user))
        assert response.status_code == 404


class TestKPDelete:
    """删除知识点测试（软删除）"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, teacher_user):
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        client.post("/api/kps", json={
            "subject_id": 1, "name": "链表",
        }, headers=get_auth_header(teacher_user))

    def test_soft_delete(self, client, teacher_user):
        """软删除 — 返回 204，is_deleted 标记为 True"""
        response = client.delete("/api/kps/1", headers=get_auth_header(teacher_user))
        assert response.status_code == 204

        # 列表仍然可见，但标记已删除
        list_resp = client.get("/api/kps", headers=get_auth_header(teacher_user))
        assert list_resp.json()[0]["is_deleted"] is True

    def test_delete_not_found(self, client, teacher_user):
        """删除不存在 — 返回 404"""
        response = client.delete("/api/kps/999", headers=get_auth_header(teacher_user))
        assert response.status_code == 404


class TestSimilarKPs:
    """相似知识点推荐测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, teacher_user):
        client.post("/api/subjects", json={
            "code": "DS", "name": "数据结构",
        }, headers=get_auth_header(teacher_user))
        for name in ["链表", "双向链表", "栈", "队列", "二叉树", "哈希表", "堆"]:
            client.post("/api/kps", json={
                "subject_id": 1, "name": name, "description": f"{name}的描述",
            }, headers=get_auth_header(teacher_user))

    def test_similar_recommendation(self, client, teacher_user):
        """查询相似知识点 — 排除自身"""
        response = client.get("/api/kps/1/similar?top_k=3", headers=get_auth_header(teacher_user))
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3
        # 不应包含自身
        kp_ids = [r["kp_id"] for r in data]
        assert 1 not in kp_ids

    def test_similar_not_found(self, client, teacher_user):
        """知识点不存在 — 返回 404"""
        response = client.get("/api/kps/999/similar", headers=get_auth_header(teacher_user))
        assert response.status_code == 404
