# NeuralSite Station API 路由
# 桩号数据管理

from datetime import datetime
from typing import List, Optional
import uuid
import re
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from pydantic import BaseModel

from api.deps import get_db, get_current_user, CurrentUser
from models.station import (
    Station, StationCreate, StationUpdate, StationResponse,
    StationBatchCreate, StationBatchResponse, StationCoordinatesResponse,
    StationType, CoordinateSystem
)


# 路由前缀
router = APIRouter(prefix="/api/v1/stations", tags=["Station - 桩号管理"])


# ==================== 辅助函数 ====================

def parse_station(station_str: str) -> float:
    """解析桩号字符串为米"""
    station_str = str(station_str).strip().upper()
    match = re.match(r'^K?(\d+)\+(\d+(?:\.\d+)?)$', station_str)
    if match:
        km = int(match.group(1))
        m = float(match.group(2))
        return km * 1000 + m
    match = re.match(r'^K?(\d+(?:\.\d+)?)$', station_str)
    if match:
        return float(match.group(1))
    raise ValueError(f"Invalid station format: {station_str}")


# ==================== Pydantic 响应模型 ====================

class StationRangeResponse(BaseModel):
    """桩号范围查询响应"""
    start: float
    end: float
    count: int
    coordinates: List[dict]


class NearestStationResponse(BaseModel):
    """最近桩号查询响应"""
    station: float
    station_display: str
    distance: float
    easting: float
    northing: float
    elevation: Optional[float] = None


# ==================== 空间计算API (PostgreSQL) ====================
# 这些路由必须在参数化路由之前定义

# 1. 桩号查坐标
@router.get("/{station}/coordinates")
def get_coordinates_by_station(
    station: str,
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """桩号查坐标，支持 K0+500 格式"""
    try:
        station_m = parse_station(station)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    sql = text("""
        SELECT station, station_display, easting, northing, elevation, azimuth
        FROM station_coordinate_mapping
        WHERE station = :station_m
    """)
    
    result = db.execute(sql, {"station_m": station_m}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"桩号 {station} 不存在")
    
    return {
        "station": station,
        "station_m": station_m,
        "easting": float(result.easting),
        "northing": float(result.northing),
        "elevation": float(result.elevation) if result.elevation else None,
        "azimuth": float(result.azimuth) if result.azimuth else 0.0
    }


# 2. 桩号范围查询
@router.get("/range/coordinates", response_model=StationRangeResponse)
def get_coordinates_by_range(
    start: str = Query(..., description="起始桩号，如 K0+0"),
    end: str = Query(..., description="结束桩号，如 K1+0"),
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """桩号范围查坐标序列"""
    try:
        start_m = parse_station(start)
        end_m = parse_station(end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    sql = text("""
        SELECT station, station_display, easting, northing, elevation
        FROM station_coordinate_mapping
        WHERE station >= :start_m AND station <= :end_m
        ORDER BY station
    """)
    params = {"start_m": start_m, "end_m": end_m}
    
    result = db.execute(sql, params).fetchall()
    
    return StationRangeResponse(
        start=start_m,
        end=end_m,
        count=len(result),
        coordinates=[
            {
                "station": float(r.station),
                "station_display": r.station_display,
                "easting": float(r.easting),
                "northing": float(r.northing),
                "elevation": float(r.elevation) if r.elevation else None
            }
            for r in result
        ]
    )


# 3. 坐标查最近桩号
@router.get("/nearest", response_model=NearestStationResponse)
def get_nearest_station(
    x: float = Query(..., description="X坐标(东向)"),
    y: float = Query(..., description="Y坐标(北向)"),
    station_system_id: Optional[str] = Query(None, description="桩号系统ID"),
    db: Session = Depends(get_db)
):
    """坐标查最近桩号"""
    sql = text("""
        SELECT station, station_display, easting, northing, elevation,
            SQRT(POWER(easting - :x, 2) + POWER(northing - :y, 2)) as distance
        FROM station_coordinate_mapping
        WHERE easting IS NOT NULL AND northing IS NOT NULL
        ORDER BY distance LIMIT 1
    """)
    
    result = db.execute(sql, {"x": x, "y": y}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="未找到附近的桩号点")
    
    return NearestStationResponse(
        station=float(result.station),
        station_display=result.station_display,
        distance=float(result.distance),
        easting=float(result.easting),
        northing=float(result.northing),
        elevation=float(result.elevation) if result.elevation else None
    )


# ==================== 旧版桩号管理API ====================

@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(
    station: StationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建桩号"""
    db_station = Station(
        project_id=station.project_id,
        route_id=station.route_id,
        station=station.station,
        station_display=station.station_display,
        station_type=station.station_type.value if hasattr(station.station_type, 'value') else station.station_type,
        longitude=station.longitude,
        latitude=station.latitude,
        elevation=station.elevation,
        x=station.x,
        y=station.y,
        z=station.z,
        coordinate_system=station.coordinate_system.value if hasattr(station.coordinate_system, 'value') else station.coordinate_system,
        description=station.description,
        tags=station.tags,
        extra_data=station.extra_data,
        created_by=current_user.user_id if current_user else None
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


@router.get("", response_model=List[StationResponse])
def list_stations(
    project_id: Optional[uuid.UUID] = None,
    route_id: Optional[uuid.UUID] = None,
    station_start: Optional[float] = Query(None, description="起始桩号"),
    station_end: Optional[float] = Query(None, description="结束桩号"),
    station_type: Optional[str] = Query(None, description="桩号类型"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取桩号列表"""
    query = db.query(Station)
    
    if project_id:
        query = query.filter(Station.project_id == project_id)
    if route_id:
        query = query.filter(Station.route_id == route_id)
    if station_start is not None:
        query = query.filter(Station.station >= station_start)
    if station_end is not None:
        query = query.filter(Station.station <= station_end)
    if station_type:
        query = query.filter(Station.station_type == station_type)
    
    return query.order_by(Station.station).offset(skip).limit(limit).all()


@router.get("/{station_id}", response_model=StationResponse)
def get_station(
    station_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取桩号详情"""
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="桩号不存在")
    return station


@router.put("/{station_id}", response_model=StationResponse)
def update_station(
    station_id: uuid.UUID,
    station: StationUpdate,
    db: Session = Depends(get_db)
):
    """更新桩号"""
    db_station = db.query(Station).filter(Station.station_id == station_id).first()
    if not db_station:
        raise HTTPException(status_code=404, detail="桩号不存在")
    
    update_data = station.model_dump(exclude_unset=True)
    
    if 'station_type' in update_data and update_data['station_type']:
        val = update_data['station_type']
        update_data['station_type'] = val.value if hasattr(val, 'value') else val
    if 'coordinate_system' in update_data and update_data['coordinate_system']:
        val = update_data['coordinate_system']
        update_data['coordinate_system'] = val.value if hasattr(val, 'value') else val
    
    for key, value in update_data.items():
        setattr(db_station, key, value)
    
    db_station.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_station)
    return db_station


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(
    station_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除桩号"""
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="桩号不存在")
    
    db.delete(station)
    db.commit()
    return None


# ==================== 批量操作 ====================

@router.post("/batch", response_model=StationBatchResponse)
def batch_create_stations(
    batch: StationBatchCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """批量创建桩号"""
    created = 0
    failed = 0
    errors = []
    
    for idx, station_data in enumerate(batch.stations):
        try:
            db_station = Station(
                project_id=station_data.project_id,
                route_id=station_data.route_id,
                station=station_data.station,
                station_display=station_data.station_display,
                station_type=station_data.station_type.value if hasattr(station_data.station_type, 'value') else station_data.station_type,
                longitude=station_data.longitude,
                latitude=station_data.latitude,
                elevation=station_data.elevation,
                x=station_data.x,
                y=station_data.y,
                z=station_data.z,
                coordinate_system=station_data.coordinate_system.value if hasattr(station_data.coordinate_system, 'value') else station_data.coordinate_system,
                description=station_data.description,
                tags=station_data.tags,
                extra_data=station_data.extra_data,
                created_by=current_user.user_id if current_user else None
            )
            db.add(db_station)
            created += 1
        except Exception as e:
            failed += 1
            errors.append({
                "index": idx,
                "station": station_data.station,
                "error": str(e)
            })
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return StationBatchResponse(
            created=0,
            failed=len(batch.stations),
            errors=[{"error": str(e)}]
        )
    
    return StationBatchResponse(
        created=created,
        failed=failed,
        errors=errors
    )
