# NeuralSite Station API 路由
# 桩号数据管理

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.deps import get_db, get_current_user, CurrentUser
from models.station import (
    Station, StationCreate, StationUpdate, StationResponse,
    StationBatchCreate, StationBatchResponse, StationCoordinatesResponse,
    StationType, CoordinateSystem
)


# 路由前缀
router = APIRouter(prefix="/api/v1/stations", tags=["Station - 桩号管理"])


# ==================== 桩号管理 ====================

@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(
    station: StationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建桩号"""
    # 检查route是否存在
    # 注意: 这里简化处理,实际应验证route_id
    
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
    
    # 更新字段
    update_data = station.model_dump(exclude_unset=True)
    
    # 处理枚举类型
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


@router.get("/{station}/coordinates", response_model=StationCoordinatesResponse)
def get_station_coordinates(
    station: float,
    project_id: Optional[uuid.UUID] = Query(None, description="项目ID"),
    route_id: Optional[uuid.UUID] = Query(None, description="路线ID"),
    db: Session = Depends(get_db)
):
    """根据桩号查询坐标"""
    query = db.query(Station).filter(Station.station == station)
    
    if project_id:
        query = query.filter(Station.project_id == project_id)
    if route_id:
        query = query.filter(Station.route_id == route_id)
    
    db_station = query.first()
    if not db_station:
        raise HTTPException(status_code=404, detail=f"桩号 {station} 不存在")
    
    return StationCoordinatesResponse(
        station=db_station.station,
        station_display=db_station.station_display,
        route_id=db_station.route_id,
        project_id=db_station.project_id,
        longitude=db_station.longitude,
        latitude=db_station.latitude,
        elevation=db_station.elevation,
        x=db_station.x,
        y=db_station.y,
        z=db_station.z
    )


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
