# -*- coding: utf-8 -*-
"""
NeuralSite Spatial API - 空间计算API
基于PostgreSQL数据库实现桩号坐标查询、工程实体查询

实现：
1. GET /api/v1/stations/{station}/coordinates - 桩号查坐标
2. GET /api/v1/stations/range/coordinates - 桩号范围查坐标序列
3. GET /api/v1/stations/nearest - 坐标查最近桩号
4. GET /api/v1/entities - 工程实体查询
5. GET /api/v1/entities/{id} - 工程实体详情
"""

import uuid
import re
import math
from datetime import datetime
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps import get_db


# 路由前缀
router = APIRouter(prefix="/api/v1", tags=["Spatial - 空间计算"])


# ==================== Pydantic 响应模型 ====================

class StationCoordinatesItem(BaseModel):
    """桩号坐标项"""
    station: float
    station_display: str
    easting: Optional[float] = None
    northing: Optional[float] = None
    elevation: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    azimuth: Optional[float] = None


class StationCoordinatesResponse(BaseModel):
    """桩号查坐标响应"""
    station: str
    station_m: float
    easting: float
    northing: float
    elevation: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    azimuth: float


class StationRangeResponse(BaseModel):
    """桩号范围查询响应"""
    start: float
    end: float
    count: int
    coordinates: List[StationCoordinatesItem]


class NearestStationResponse(BaseModel):
    """最近桩号查询响应"""
    station: float
    station_display: str
    distance: float
    easting: float
    northing: float
    elevation: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    azimuth: Optional[float] = None


class EngineeringEntityItem(BaseModel):
    """工程实体项"""
    entity_id: uuid.UUID
    entity_type: str
    entity_name: str
    entity_code: Optional[str] = None
    start_station: Optional[float] = None
    end_station: Optional[float] = None
    station_display: Optional[str] = None
    construction_status: str
    project_id: uuid.UUID


class EngineeringEntityDetail(EngineeringEntityItem):
    """工程实体详情"""
    geometry_data: Optional[dict] = None
    design_parameters: Optional[dict] = None
    parent_entity_id: Optional[uuid.UUID] = None
    source_drawing_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class EntityListResponse(BaseModel):
    """工程实体列表响应"""
    total: int
    items: List[EngineeringEntityItem]


# ==================== 辅助函数 ====================

def parse_station(station_str: str) -> float:
    """
    解析桩号字符串为米
    
    支持格式:
    - K0+500 -> 500
    - K1+200.5 -> 1200.5
    - 0+500 -> 500
    - 1200 -> 1200
    """
    station_str = str(station_str).strip().upper()
    
    # 匹配 K0+500 或 0+500 格式
    match = re.match(r'^K?(\d+)\+(\d+(?:\.\d+)?)$', station_str)
    if match:
        km = int(match.group(1))
        m = float(match.group(2))
        return km * 1000 + m
    
    # 匹配纯数字格式 (如 500, 1200.5)
    match = re.match(r'^K?(\d+(?:\.\d+)?)$', station_str)
    if match:
        return float(match.group(1))
    
    raise ValueError(f"Invalid station format: {station_str}")


def format_station(station_m: float) -> str:
    """
    将米格式化为桩号字符串
    
    500 -> K0+500
    1200.5 -> K1+200.5
    """
    km = int(station_m // 1000)
    m = station_m % 1000
    if m == 0:
        return f"K{km}+000"
    else:
        return f"K{km}+{m:03.1f}" if m == int(m) else f"K{km}+{m:03.1f}"


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """计算两点之间的欧氏距离"""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# ==================== API 端点 ====================

# 1. 桩号查坐标
@router.get(
    "/stations/{station}/coordinates",
    response_model=StationCoordinatesResponse,
    summary="桩号查坐标",
    description="根据桩号查询三维坐标，支持 K0+500 格式或纯数字"
)
async def get_coordinates_by_station(
    station: str = Path(..., description="桩号，如 K0+500 或 500"),
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """
    桩号查坐标
    
    根据桩号（如 K0+500）查询对应的三维坐标
    """
    try:
        station_m = parse_station(station)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 查询坐标
    sql = text("""
        SELECT 
            station, station_display, 
            easting, northing, elevation,
            latitude, longitude, azimuth
        FROM station_coordinate_mapping
        WHERE station = :station_m
    """)
    
    if station_system_id:
        sql = text("""
            SELECT 
                station, station_display, 
                easting, northing, elevation,
                latitude, longitude, azimuth
            FROM station_coordinate_mapping
            WHERE station = :station_m AND station_system_id = :station_system_id
        """)
    
    params = {"station_m": station_m}
    if station_system_id:
        params["station_system_id"] = station_system_id
    
    result = db.execute(sql, params).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"桩号 {station} ({station_m}m) 不存在"
        )
    
    return StationCoordinatesResponse(
        station=station,
        station_m=station_m,
        easting=float(result.easting),
        northing=float(result.northing),
        elevation=float(result.elevation) if result.elevation else None,
        latitude=float(result.latitude) if result.latitude else None,
        longitude=float(result.longitude) if result.longitude else None,
        azimuth=float(result.azimuth) if result.azimuth else 0.0
    )


# 2. 桩号范围查坐标序列
@router.get(
    "/stations/range/coordinates",
    response_model=StationRangeResponse,
    summary="桩号范围查坐标",
    description="查询指定桩号范围内的坐标点序列"
)
async def get_coordinates_by_range(
    start: str = Query(..., description="起始桩号，如 K0+0"),
    end: str = Query(..., description="结束桩号，如 K1+0"),
    interval: float = Query(10, description="查询间隔(米)", gt=0),
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """
    桩号范围查询
    
    根据起止桩号和间隔查询坐标序列
    """
    try:
        start_m = parse_station(start)
        end_m = parse_station(end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if start_m >= end_m:
        raise HTTPException(status_code=400, detail="起始桩号必须小于结束桩号")
    
    # 查询范围内的坐标点
    sql = text("""
        SELECT 
            station, station_display, 
            easting, northing, elevation,
            latitude, longitude, azimuth
        FROM station_coordinate_mapping
        WHERE station >= :start_m AND station <= :end_m
        ORDER BY station
    """)
    
    params = {"start_m": start_m, "end_m": end_m}
    
    if station_system_id:
        sql = text("""
            SELECT 
                station, station_display, 
                easting, northing, elevation,
                latitude, longitude, azimuth
            FROM station_coordinate_mapping
            WHERE station >= :start_m AND station <= :end_m
                AND station_system_id = :station_system_id
            ORDER BY station
        """)
        params["station_system_id"] = station_system_id
    
    result = db.execute(sql, params).fetchall()
    
    coordinates = []
    for row in result:
        coordinates.append(StationCoordinatesItem(
            station=float(row.station),
            station_display=row.station_display,
            easting=float(row.easting) if row.easting else None,
            northing=float(row.northing) if row.northing else None,
            elevation=float(row.elevation) if row.elevation else None,
            latitude=float(row.latitude) if row.latitude else None,
            longitude=float(row.longitude) if row.longitude else None,
            azimuth=float(row.azimuth) if row.azimuth else None
        ))
    
    return StationRangeResponse(
        start=start_m,
        end=end_m,
        count=len(coordinates),
        coordinates=coordinates
    )


# 3. 坐标查最近桩号
@router.get(
    "/stations/nearest",
    response_model=NearestStationResponse,
    summary="坐标查最近桩号",
    description="根据坐标查询最近的桩号"
)
async def get_nearest_station(
    x: float = Query(..., description="X坐标(东向)或经度"),
    y: float = Query(..., description="Y坐标(北向)或纬度"),
    use_geographic: bool = Query(False, description="是否使用经纬度坐标"),
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """
    坐标查最近桩号
    
    根据给定的坐标，查找最近的桩号点
    """
    if use_geographic:
        # 使用经纬度查询
        sql = text("""
            SELECT 
                station, station_display,
                easting, northing, elevation,
                latitude, longitude, azimuth,
                (ST_MakePoint(longitude, latitude) <-> ST_MakePoint(:lon, :lat)) as distance
            FROM station_coordinate_mapping
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        if station_system_id:
            sql = text("""
                SELECT 
                    station, station_display,
                    easting, northing, elevation,
                    latitude, longitude, azimuth,
                    (ST_MakePoint(longitude, latitude) <-> ST_MakePoint(:lon, :lat)) as distance
                FROM station_coordinate_mapping
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                    AND station_system_id = :station_system_id
            """)
            params = {"lon": x, "lat": y, "station_system_id": station_system_id}
        else:
            params = {"lon": x, "lat": y}
    else:
        # 使用平面坐标查询
        sql = text("""
            SELECT 
                station, station_display,
                easting, northing, elevation,
                latitude, longitude, azimuth,
                SQRT(POWER(easting - :x, 2) + POWER(northing - :y, 2)) as distance
            FROM station_coordinate_mapping
            WHERE easting IS NOT NULL AND northing IS NOT NULL
        """)
        if station_system_id:
            sql = text("""
                SELECT 
                    station, station_display,
                    easting, northing, elevation,
                    latitude, longitude, azimuth,
                    SQRT(POWER(easting - :x, 2) + POWER(northing - :y, 2)) as distance
                FROM station_coordinate_mapping
                WHERE easting IS NOT NULL AND northing IS NOT NULL
                    AND station_system_id = :station_system_id
            """)
            params = {"x": x, "y": y, "station_system_id": station_system_id}
        else:
            params = {"x": x, "y": y}
    
    sql = text(str(sql) + " ORDER BY distance LIMIT 1")
    
    result = db.execute(sql, params).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="未找到附近的桩号点"
        )
    
    return NearestStationResponse(
        station=float(result.station),
        station_display=result.station_display,
        distance=float(result.distance),
        easting=float(result.easting),
        northing=float(result.northing),
        elevation=float(result.elevation) if result.elevation else None,
        latitude=float(result.latitude) if result.latitude else None,
        longitude=float(result.longitude) if result.longitude else None,
        azimuth=float(result.azimuth) if result.azimuth else None
    )


# 4. 工程实体查询
@router.get(
    "/entities",
    response_model=EntityListResponse,
    summary="工程实体查询",
    description="查询工程实体列表"
)
async def list_entities(
    project_id: Optional[uuid.UUID] = Query(None, description="项目ID"),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    station_start: Optional[float] = Query(None, description="起始桩号"),
    station_end: Optional[float] = Query(None, description="结束桩号"),
    search: Optional[str] = Query(None, description="搜索实体名称"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """
    工程实体查询
    
    查询工程实体列表，支持多种过滤条件
    """
    # 构建查询
    sql = text("""
        SELECT 
            entity_id, entity_type, entity_name, entity_code,
            start_station, end_station, station_display,
            construction_status, project_id
        FROM engineering_entity
        WHERE is_active = true
    """)
    
    params = {}
    
    if project_id:
        sql = text(str(sql) + " AND project_id = :project_id")
        params["project_id"] = str(project_id)
    
    if entity_type:
        sql = text(str(sql) + " AND entity_type = :entity_type")
        params["entity_type"] = entity_type
    
    if station_start is not None:
        sql = text(str(sql) + " AND start_station >= :station_start")
        params["station_start"] = station_start
    
    if station_end is not None:
        sql = text(str(sql) + " AND end_station <= :station_end")
        params["station_end"] = station_end
    
    if search:
        sql = text(str(sql) + " AND entity_name ILIKE :search")
        params["search"] = f"%{search}%"
    
    # 计算总数
    count_sql = text(f"SELECT COUNT(*) as total FROM ({sql}) as sub")
    count_result = db.execute(count_sql, params).fetchone()
    total = count_result.total if count_result else 0
    
    # 分页查询
    sql = text(str(sql) + " ORDER BY start_station LIMIT :limit OFFSET :skip")
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(sql, params).fetchall()
    
    items = []
    for row in result:
        items.append(EngineeringEntityItem(
            entity_id=row.entity_id,
            entity_type=row.entity_type,
            entity_name=row.entity_name,
            entity_code=row.entity_code,
            start_station=float(row.start_station) if row.start_station else None,
            end_station=float(row.end_station) if row.end_station else None,
            station_display=row.station_display,
            construction_status=row.construction_status,
            project_id=row.project_id
        ))
    
    return EntityListResponse(total=total, items=items)


# 5. 工程实体详情
@router.get(
    "/entities/{entity_id}",
    response_model=EngineeringEntityDetail,
    summary="工程实体详情",
    description="获取工程实体详细信息"
)
async def get_entity_detail(
    entity_id: uuid.UUID = Path(..., description="实体ID"),
    db: Session = Depends(get_db)
):
    """
    工程实体详情
    
    根据实体ID获取完整的工程实体信息
    """
    sql = text("""
        SELECT 
            entity_id, entity_type, entity_name, entity_code,
            start_station, end_station, station_display,
            geometry_data, design_parameters,
            construction_status, project_id,
            parent_entity_id, source_drawing_id,
            created_at, updated_at
        FROM engineering_entity
        WHERE entity_id = :entity_id AND is_active = true
    """)
    
    result = db.execute(sql, {"entity_id": str(entity_id)}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"工程实体 {entity_id} 不存在"
        )
    
    return EngineeringEntityDetail(
        entity_id=result.entity_id,
        entity_type=result.entity_type,
        entity_name=result.entity_name,
        entity_code=result.entity_code,
        start_station=float(result.start_station) if result.start_station else None,
        end_station=float(result.end_station) if result.end_station else None,
        station_display=result.station_display,
        geometry_data=result.geometry_data,
        design_parameters=result.design_parameters,
        construction_status=result.construction_status,
        project_id=result.project_id,
        parent_entity_id=result.parent_entity_id,
        source_drawing_id=result.source_drawing_id,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


# ==================== 路由注册 ====================

def register_routes(app):
    """注册路由到FastAPI应用"""
    app.include_router(router)
