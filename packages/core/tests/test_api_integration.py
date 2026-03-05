# -*- coding: utf-8 -*-
"""
NeuralSite Core API 集成测试

测试所有 MVP API 端点
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.main import app


# 创建测试客户端
client = TestClient(app)


class TestRoot:
    """测试根端点"""
    
    def test_root(self):
        """测试根路径返回正确信息"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NeuralSite Core API"
        assert "version" in data
        assert "timestamp" in data


class TestHealthCheck:
    """测试健康检查"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data
    
    def test_list_features(self):
        """测试特性开关列表"""
        response = client.get("/features")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "enable_chainage_query" in data["features"]


class TestChainageQuery:
    """测试桩号查询"""
    
    def test_query_by_chainage_k0(self):
        """测试K0+000查询"""
        response = client.get("/api/v1/chainage/K0+000")
        assert response.status_code == 200
        data = response.json()
        assert "station" in data
        assert "x" in data
        assert "y" in data
        assert "z" in data
        assert data["station"] == "K0+000"
    
    def test_query_by_chainage_k500(self):
        """测试K0+500查询"""
        response = client.get("/api/v1/chainage/K0+500")
        assert response.status_code == 200
        data = response.json()
        assert "station" in data
        assert data["station"] == "K0+500"
    
    def test_query_by_invalid_chainage(self):
        """测试无效桩号"""
        response = client.get("/api/v1/chainage/invalid")
        assert response.status_code == 400


class TestRangeQuery:
    """测试范围查询"""
    
    def test_query_range_basic(self):
        """测试基础范围查询"""
        response = client.post(
            "/api/v1/query/range",
            json={
                "start": 0,
                "end": 500,
                "interval": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["coordinates"]) == data["count"]
    
    def test_query_range_with_cross_section(self):
        """测试带横断面的范围查询"""
        response = client.post(
            "/api/v1/query/range",
            json={
                "start": 0,
                "end": 200,
                "interval": 100,
                "include_cross_section": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
    
    def test_query_range_invalid_interval(self):
        """测试无效间隔"""
        response = client.post(
            "/api/v1/query/range",
            json={
                "start": 0,
                "end": 500,
                "interval": -1
            }
        )
        assert response.status_code == 400
    
    def test_query_range_invalid_range(self):
        """测试无效范围"""
        response = client.post(
            "/api/v1/query/range",
            json={
                "start": 500,
                "end": 0,
                "interval": 100
            }
        )
        assert response.status_code == 400


class TestLODQuery:
    """测试LOD查询"""
    
    def test_query_lod0(self):
        """测试LOD0查询"""
        response = client.get("/api/v1/lod/0?start=0&end=500")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "LOD0"
        assert data["interval"] == 50
    
    def test_query_lod1(self):
        """测试LOD1查询"""
        response = client.get("/api/v1/lod/1?start=0&end=500")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "LOD1"
        assert data["interval"] == 10
    
    def test_query_lod2(self):
        """测试LOD2查询"""
        response = client.get("/api/v1/lod/2?start=0&end=100")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "LOD2"
        assert data["interval"] == 1
    
    def test_query_lod_invalid_level(self):
        """测试无效LOD级别"""
        response = client.get("/api/v1/lod/5")
        assert response.status_code == 422  # FastAPI validation error


class TestTransform:
    """测试坐标转换"""
    
    def test_transform_coordinates(self):
        """测试坐标转换"""
        response = client.post(
            "/api/v1/transform",
            json={
                "x": 500000,
                "y": 3000000,
                "from_srid": "EPSG:4547",
                "to_srid": "EPSG:4326"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "original" in data
        assert "transformed" in data


class TestQA:
    """测试知识问答"""
    
    def test_qa_elevation(self):
        """测试高程查询"""
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "K0+500的设计标高是多少"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["confidence"] > 0
    
    def test_qa_coordinate(self):
        """测试坐标查询"""
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "K0+500的坐标是什么"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
    
    def test_qa_invalid(self):
        """测试无效问题"""
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "这是个什么问题"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] < 0.5


class TestEntitySearch:
    """测试实体搜索"""
    
    def test_search_entities(self):
        """测试实体搜索"""
        response = client.get("/api/v1/kg/search?q=test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total" in data
        assert "entities" in data
    
    def test_search_with_type(self):
        """测试带类型过滤的搜索"""
        response = client.get("/api/v1/kg/search?q=test&entity_type=Project&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"


class TestReasoning:
    """测试推理接口"""
    
    def test_reason_basic(self):
        """测试基础推理"""
        response = client.post(
            "/api/v1/kg/reason",
            json={
                "start_entity": "K0+500",
                "relation": "has_coordinate",
                "max_depth": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "results" in data


class TestExistingAPI:
    """测试现有API向后兼容性"""
    
    def test_spatial_nearby(self):
        """测试空间附近查询（原有API）"""
        response = client.post(
            "/api/v1/spatial/nearby",
            json={
                "x": 500000,
                "y": 3000000,
                "radius": 100
            }
        )
        assert response.status_code == 200
    
    def test_knowledge_test(self):
        """测试知识图谱连接（原有API）"""
        response = client.get("/api/v1/knowledge/test")
        assert response.status_code == 200


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
