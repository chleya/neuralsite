# -*- coding: utf-8 -*-
"""
空间数据 API - 扩展版

包含：桩号查询、坐标转换、范围查询、LOD查询
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import sys
import math
sys.path.insert(0, '.')

from core.engine import NeuralSiteEngine
from api.dependencies import (
    get_engine,
    get_spatial_database,
    get_feature_flags,
    require_feature_flag,
    ChainageQuery,
    TransformRequest,
    RangeQueryRequest,
    LODQuery
)
from core.config.feature_flags import FeatureFlags


router = APIRouter(prefix="/api/v1", tags=["空间数据V1"])


# ========== 响应模型 ==========

class CoordinateResponse(BaseModel):
    """坐标响应"""
    station: str
    station_m: float
    x: float
    y: float
    z: float
    azimuth: float


class TransformResponse(BaseModel):
    """坐标转换响应"""
    original: Dict[str, float]
    transformed: Dict[str, float]
    from_srid: str
    to_srid: str


class RangeQueryResponse(BaseModel):
    """范围查询响应"""
    start: float
    end: float
    interval: float
    count: int
    coordinates: List[Dict[str, Any]]


class LODResponse(BaseModel):
    """LOD响应"""
    level: str
    interval: float
    tolerance: float
    count: int
    coordinates: List[Dict[str, Any]]


# ========== 1. 桩号查询接口 ==========

@router.get(
    "/chainage/{station}",
    response_model=CoordinateResponse,
    summary="桩号查询",
    description="根据桩号查询三维坐标"
)
async def query_by_chainage(
    station: str,
    engine: NeuralSiteEngine = Depends(get_engine),
    route_id: Optional[str] = Query(None, description="路线ID")
) -> CoordinateResponse:
    """
    桩号查询接口
    
    根据桩号（如 K0+500）查询对应的三维坐标
    """
    # 解析桩号
    station_m = _parse_station(station)
    
    if station_m < 0:
        raise HTTPException(status_code=400, detail=f"Invalid station format: {station}")
    
    # 获取坐标
    coord = engine.get_coordinate(station_m)
    
    return CoordinateResponse(
        station=coord.to_dict()["station"],
        station_m=coord.station,
        x=coord.x,
        y=coord.y,
        z=coord.z,
        azimuth=coord.azimuth
    )


# ========== 2. 坐标转换接口 ==========

@router.post(
    "/transform",
    response_model=TransformResponse,
    summary="坐标转换",
    description="在不同坐标系之间转换坐标"
)
async def transform_coordinates(
    request: TransformRequest,
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> TransformResponse:
    """
    坐标转换接口
    
    支持坐标系转换（简化版，实际使用PROJ库）
    """
    if not feature_flags.is_enabled("enable_coordinate_transform"):
        raise HTTPException(
            status_code=403,
            detail="Coordinate transform feature is disabled"
        )
    
    # 简化实现：如果是CGCS2000<->WGS84，做简化转换
    # 实际生产中应该使用 pyproj 库
    result = _transform_coords(
        request.x, request.y,
        request.from_srid,
        request.to_srid
    )
    
    return TransformResponse(
        original={"x": request.x, "y": request.y},
        transformed=result,
        from_srid=request.from_srid,
        to_srid=request.to_srid
    )


def _transform_coords(x: float, y: float, from_srid: str, to_srid: str) -> Dict[str, float]:
    """坐标转换实现（简化版）"""
    # 这是一个简化实现
    # 实际项目中应该使用 pyproj 库
    
    # CGCS2000 / 3-degree Gauss-Kruger CM 84E (EPSG:4547) -> WGS84
    if from_srid == "EPSG:4547" and to_srid == "EPSG:4326":
        # 简化转换（经度偏移）
        return {
            "lon": x - 0.0001,  # 简化偏移
            "lat": y - 0.0001
        }
    
    # WGS84 -> CGCS2000
    if from_srid == "EPSG:4326" and to_srid == "EPSG:4547":
        return {
            "x": x + 0.0001,
            "y": y + 0.0001
        }
    
    # 默认返回原坐标
    return {"x": x, "y": y}


# ========== 3. 范围查询接口 ==========

@router.post(
    "/query/range",
    response_model=RangeQueryResponse,
    summary="范围查询",
    description="查询指定桩号范围内的坐标点"
)
async def query_range(
    request: RangeQueryRequest,
    engine: NeuralSiteEngine = Depends(get_engine),
    route_id: Optional[str] = Query(None, description="路线ID")
) -> RangeQueryResponse:
    """
    范围查询接口
    
    根据起止桩号和间隔查询坐标序列
    """
    # 验证范围
    if request.start < 0 or request.end < 0:
        raise HTTPException(status_code=400, detail="Invalid station range")
    
    if request.start >= request.end:
        raise HTTPException(status_code=400, detail="Start must be less than end")
    
    if request.interval <= 0:
        raise HTTPException(status_code=400, detail="Interval must be positive")
    
    # 计算坐标
    coords = engine.calculate_range(
        request.start,
        request.end,
        request.interval
    )
    
    result_coords = []
    for coord in coords:
        result_coords.append({
            "station": coord["station"],
            "station_m": coord["station_m"],
            "x": coord["x"],
            "y": coord["y"],
            "z": coord["z"],
            "azimuth": coord["azimuth"]
        })
    
    return RangeQueryResponse(
        start=request.start,
        end=request.end,
        interval=request.interval,
        count=len(result_coords),
        coordinates=result_coords
    )


# ========== 4. LOD 接口 ==========

@router.get(
    "/lod/{level}",
    response_model=LODResponse,
    summary="LOD查询",
    description="根据LOD级别查询坐标数据"
)
async def query_by_lod(
    level: int = Path(..., ge=0, le=3, description="LOD级别 (0-3)"),
    start: float = Query(0, description="起始桩号"),
    end: float = Query(1000, description="结束桩号"),
    engine: NeuralSiteEngine = Depends(get_engine),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> LODResponse:
    """
    LOD查询接口
    
    根据LOD级别自动调整采样间隔：
    - LOD0: 50m间隔（粗精度）
    - LOD1: 10m间隔（中等精度）
    - LOD2: 1m间隔（高精度）
    - LOD3: 0.1m间隔（超高精度）
    """
    if not feature_flags.is_enabled("enable_lod_calculation"):
        raise HTTPException(
            status_code=403,
            detail="LOD calculation feature is disabled"
        )
    
    # LOD配置
    lod_configs = {
        0: {"interval": 50, "tolerance": 0.5},
        1: {"interval": 10, "tolerance": 0.05},
        2: {"interval": 1, "tolerance": 0.01},
        3: {"interval": 0.1, "tolerance": 0.001}
    }
    
    config = lod_configs.get(level, lod_configs[1])
    
    # 计算坐标
    coords = engine.calculate_range(start, end, config["interval"])
    
    result_coords = []
    for coord in coords:
        result_coords.append({
            "station": coord["station"],
            "x": coord["x"],
            "y": coord["y"],
            "z": coord["z"],
            "azimuth": coord["azimuth"]
        })
    
    return LODResponse(
        level=f"LOD{level}",
        interval=config["interval"],
        tolerance=config["tolerance"],
        count=len(result_coords),
        coordinates=result_coords
    )


# ========== 辅助函数 ==========

def _parse_station(station_str: str) -> float:
    """解析桩号字符串为米"""
    import re
    station_str = str(station_str).upper()
    
    # 格式: K0+000 或 0+000 或 0
    patterns = [
        r'^K?(\d+)\+(\d{3})$',  # K0+000 或 0+000
        r'^K?(\d+)$',           # K0 或 0
    ]
    
    for pattern in patterns:
        match = re.match(pattern, station_str)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]) * 1000 + int(groups[1])
            elif len(groups) == 1:
                return int(groups[0]) * 1000
    
    return -1  # 无效格式


# ========== 注册到主应用 ==========

def register_routes(app):
    """注册路由到FastAPI应用"""
    app.include_router(router)
