# -*- coding: utf-8 -*-
"""
API 依赖注入模块

为所有路由提供统一的服务依赖管理
"""

from typing import Optional, Dict, Any
from functools import lru_cache

from fastapi import Depends, HTTPException, Header
from pydantic import BaseModel

import sys
sys.path.insert(0, '.')

from core.engine import NeuralSiteEngine
from core.config.feature_flags import feature_flags, FeatureFlags
from core.config.settings import settings, Settings
from storage.manager import get_storage
from storage.graph_db import get_graph_db
from core.spatial.database import get_spatial_db


# ========== 服务提供者 ==========

class EngineService:
    """引擎服务 - 管理路线计算引擎"""
    
    _engines: Dict[str, NeuralSiteEngine] = {}
    
    @classmethod
    def get_engine(cls, route_id: str = "default") -> NeuralSiteEngine:
        """获取或创建引擎实例"""
        if route_id not in cls._engines:
            engine = NeuralSiteEngine(route_id)
            # 加载默认路线数据
            default_route = settings.get_default_route()
            engine.load_from_json(default_route)
            cls._engines[route_id] = engine
        return cls._engines[route_id]
    
    @classmethod
    def clear_cache(cls):
        """清空引擎缓存"""
        cls._engines.clear()


class SpatialService:
    """空间数据服务"""
    
    @staticmethod
    def get_db():
        """获取空间数据库"""
        return get_spatial_db()


class KnowledgeService:
    """知识图谱服务"""
    
    @staticmethod
    def get_graph():
        """获取图数据库"""
        return get_graph_db()


class StorageService:
    """存储服务"""
    
    @staticmethod
    def get_storage():
        """获取存储管理器"""
        return get_storage()


# ========== 依赖注入函数 ==========

def get_engine(route_id: Optional[str] = None) -> NeuralSiteEngine:
    """
    获取引擎实例的依赖注入函数
    
    Usage:
        @router.get("/items")
        async def get_items(engine: NeuralSiteEngine = Depends(get_engine)):
            ...
    """
    route_id = route_id or "default"
    return EngineService.get_engine(route_id)


def get_spatial_database():
    """获取空间数据库依赖"""
    return SpatialService.get_db()


def get_graph_database():
    """获取图数据库依赖"""
    return KnowledgeService.get_graph()


def get_storage_manager():
    """获取存储管理器依赖"""
    return StorageService.get_storage()


def get_feature_flags() -> FeatureFlags:
    """获取特性开关依赖"""
    return feature_flags


def get_settings() -> Settings:
    """获取设置依赖"""
    return settings


# ========== 请求模型 ==========

class ChainageQuery(BaseModel):
    """桩号查询"""
    station: str


class TransformRequest(BaseModel):
    """坐标转换请求"""
    x: float
    y: float
    from_srid: str = "EPSG:4547"  # 原始坐标系
    to_srid: str = "EPSG:4326"     # 目标坐标系


class RangeQueryRequest(BaseModel):
    """范围查询请求"""
    start: float
    end: float
    interval: float = 100
    include_cross_section: bool = False


class LODQuery(BaseModel):
    """LOD查询"""
    level: int


class QARequest(BaseModel):
    """知识问答请求"""
    question: str
    context: Optional[Dict[str, Any]] = None


class EntitySearchRequest(BaseModel):
    """实体搜索请求"""
    query: str
    entity_type: Optional[str] = None
    limit: int = 10


class ReasonRequest(BaseModel):
    """推理请求"""
    start_entity: str
    relation: str
    max_depth: int = 3


# ========== 特性开关检查 ==========

def require_feature(flag_name: str):
    """
    特性开关检查装饰器
    
    Usage:
        @router.get("/new-feature")
        @require_feature("enable_new_feature")
        async def new_feature():
            ...
    """
    def dependency():
        if not feature_flags.is_enabled(flag_name):
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{flag_name}' is disabled"
            )
        return True
    return Depends(dependency)


def require_feature_flag(flag_name: str) -> bool:
    """依赖注入形式的特性开关检查"""
    if not feature_flags.is_enabled(flag_name):
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{flag_name}' is disabled"
        )
    return True


# ========== API 密钥验证（可选） ==========

async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    API 密钥验证（可选）
    
    如果配置了 API_KEY，则需要验证
    """
    configured_key = settings.get("api_key")
    if configured_key and configured_key != x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
