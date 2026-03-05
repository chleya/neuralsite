# -*- coding: utf-8 -*-
"""
API路由 - 计算接口

使用 FastAPI 依赖注入模式管理引擎实例
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入核心模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core import NeuralSiteEngine
from agents.parser import DesignParser

# 导入配置
from core.config import feature_flags, settings


router = APIRouter(prefix="/api/v1", tags=["计算"])


# ========== 数据模型 ==========

class CalculateRequest(BaseModel):
    """坐标计算请求"""
    route_id: str = Field(default="default", description="路线ID")
    station: float = Field(..., description="桩号(m)")
    lod: Optional[str] = Field(default="LOD1", description="LOD级别")


class CalculateRangeRequest(BaseModel):
    """批量计算请求"""
    route_id: str = Field(default="default")
    start: float = Field(..., description="起始桩号(m)")
    end: float = Field(..., description="结束桩号(m)")
    interval: float = Field(default=100, description="间隔(m)")


class CrossSectionRequest(BaseModel):
    """横断面计算请求"""
    station: float = Field(..., description="桩号(m)")
    offset: float = Field(default=0, description="横向偏移(m)")


class ParseTextRequest(BaseModel):
    """文本解析请求"""
    text: str = Field(..., description="输入文本")
    calculate: bool = Field(default=False, description="是否同时计算坐标")
    route_id: str = Field(default="default", description="路线ID")


# ========== 引擎实例管理 - 依赖注入模式 ==========

class EngineManager:
    """
    引擎管理器 - 使用依赖注入模式
    
    代替全局字典 _engines = {}，通过依赖注入提供引擎实例
    """
    
    def __init__(self):
        self._engines: Dict[str, NeuralSiteEngine] = {}
    
    def get_engine(self, route_id: str = "default") -> NeuralSiteEngine:
        """获取或创建引擎实例"""
        # 启用缓存时才使用缓存
        if feature_flags.is_enabled("enable_cache"):
            if route_id in self._engines:
                return self._engines[route_id]
        
        # 创建新引擎
        engine = NeuralSiteEngine(route_id)
        
        # 加载默认数据（从配置中读取，而不是硬编码）
        default_route_data = settings.get_default_route()
        
        # 如果请求的 route_id 与默认不同，创建一个变体
        if route_id != "default":
            route_data = default_route_data.copy()
            route_data["route_id"] = route_id
        else:
            route_data = default_route_data
        
        engine.load_from_json(route_data)
        
        # 缓存引擎（如果启用）
        if feature_flags.is_enabled("enable_cache"):
            self._engines[route_id] = engine
        
        return engine
    
    def clear_cache(self, route_id: Optional[str] = None):
        """清除引擎缓存"""
        if route_id:
            self._engines.pop(route_id, None)
        else:
            self._engines.clear()
    
    def list_routes(self) -> List[str]:
        """列出所有缓存的路线"""
        return list(self._engines.keys())


# 全局管理器实例（仅用于依赖注入工厂）
_engine_manager = EngineManager()


def get_engine_manager() -> EngineManager:
    """获取引擎管理器（依赖注入）"""
    return _engine_manager


def get_engine(route_id: str = "default") -> NeuralSiteEngine:
    """
    获取引擎实例的依赖注入函数
    
    用法:
        @router.post("/calculate")
        async def calculate(request: CalculateRequest, engine: NeuralSiteEngine = Depends(get_engine)):
            ...
    """
    manager = get_engine_manager()
    return manager.get_engine(route_id)


# ========== 路由 ==========

@router.get("/")
async def root():
    """根路径"""
    return {
        "name": "NeuralSite Core API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "features": feature_flags.get_all(),
        "cached_routes": _engine_manager.list_routes()
    }


@router.post("/calculate")
async def calculate_coordinate(request: CalculateRequest, engine: NeuralSiteEngine = Depends(get_engine)):
    """
    计算单点坐标
    
    输入桩号，返回3D坐标
    
    使用 Depends(get_engine) 注入引擎实例，而非全局字典
    """
    try:
        result = engine.get_coordinate_dict(request.station)
        
        return {
            "status": "success",
            "route_id": request.route_id,
            "lod": request.lod,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate/range")
async def calculate_range(request: CalculateRangeRequest, engine: NeuralSiteEngine = Depends(get_engine)):
    """
    批量计算坐标
    
    输入起止桩号和间隔，返回坐标数组
    """
    # Feature Flag 检查
    if not feature_flags.is_enabled("enable_batch_calculation"):
        raise HTTPException(
            status_code=403, 
            detail="Batch calculation is currently disabled"
        )
    
    try:
        # LOD处理
        if request.interval <= 0:
            # 使用LOD（如果启用）
            if feature_flags.is_enabled("enable_lod_calculation"):
                results = engine.calculate_lod(request.start, request.end, "LOD1")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="LOD calculation is disabled"
                )
        else:
            results = engine.calculate_range(request.start, request.end, request.interval)
        
        return {
            "status": "success",
            "route_id": request.route_id,
            "start": request.start,
            "end": request.end,
            "interval": request.interval,
            "count": len(results),
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross_section")
async def calculate_cross_section(request: CrossSectionRequest):
    """
    计算横断面
    
    输入桩号和偏移，返回断面点
    """
    # Feature Flag 检查
    if not feature_flags.is_enabled("enable_cross_section"):
        raise HTTPException(
            status_code=403,
            detail="Cross section calculation is currently disabled"
        )
    
    try:
        engine = get_engine("default")
        result = engine.calculate_cross_section(request.station, request.offset)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_text(request: ParseTextRequest):
    """
    解析文本参数
    
    输入工程文本，提取参数
    """
    # Feature Flag 检查
    if not feature_flags.is_enabled("enable_text_parser"):
        raise HTTPException(
            status_code=403,
            detail="Text parser is currently disabled"
        )
    
    try:
        parser = DesignParser()
        parsed = parser.parse_text(request.text)
        
        result = {
            "status": "success",
            "input": request.text,
            "parsed": parsed,
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果需要同时计算
        if request.calculate:
            engine = get_engine(request.route_id)
            engine.load_from_json(parser.to_engine_format())
            
            # 计算第一个桩号
            if parsed.get("horizontal"):
                first_station = parsed["horizontal"][0].get("start_station", "K0+000")
                station_m = int(first_station.split("+")[0][1:]) * 1000 + int(first_station.split("+")[1])
                coord = engine.get_coordinate_dict(station_m)
                result["coordinate"] = coord
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes")
async def list_routes():
    """列出所有路线"""
    return {
        "routes": _engine_manager.list_routes(),
        "count": len(_engine_manager.list_routes())
    }


@router.delete("/cache")
async def clear_cache(route_id: Optional[str] = None):
    """清除引擎缓存"""
    _engine_manager.clear_cache(route_id)
    return {
        "status": "success",
        "message": f"Cache cleared for {route_id or 'all routes'}"
    }


@router.get("/features")
async def list_features():
    """列出所有特性开关"""
    return {
        "features": feature_flags.get_all()
    }
