# NeuralSite Route API
# 路线管理 CRUD 接口

from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import json

from api.deps import get_db
from models.route import (
    Route, RouteCreate, RouteUpdate, RouteResponse,
    RouteListResponse, RouteStatus, RouteLevel
)
from models.project import Project

router = APIRouter(prefix="/api/v1/routes", tags=["Routes - 路线管理"])


def _json_to_str(json_obj: Optional[dict]) -> Optional[str]:
    """将dict转换为JSON字符串存储"""
    if json_obj is None:
        return None
    return json.dumps(json_obj, ensure_ascii=False)


def _str_to_json(str_obj: Optional[str]) -> Optional[dict]:
    """将JSON字符串转换为dict"""
    if str_obj is None:
        return None
    try:
        return json.loads(str_obj)
    except json.JSONDecodeError:
        return None


# ==================== CRUD 操作 ====================

@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db)
):
    """创建路线"""
    # 验证项目存在且未删除
    project = db.query(Project).filter(
        Project.project_id == route.project_id,
        Project.is_deleted == False
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {route.project_id}"
        )
    
    db_route = Route(
        route_id=uuid.uuid4(),
        project_id=route.project_id,
        name=route.name,
        route_code=route.route_code,
        description=route.description,
        route_level=route.route_level.value if hasattr(route.route_level, 'value') else route.route_level,
        status=route.status.value if hasattr(route.status, 'value') else route.status,
        start_station=route.start_station,
        end_station=route.end_station,
        total_length=route.total_length,
        start_latitude=route.start_latitude,
        start_longitude=route.start_longitude,
        end_latitude=route.end_latitude,
        end_longitude=route.end_longitude,
        extra_data=_json_to_str(route.extra_data),
        is_deleted=False
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("", response_model=RouteListResponse)
def list_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[uuid.UUID] = None,
    status: Optional[RouteStatus] = None,
    route_level: Optional[RouteLevel] = None,
    search: Optional[str] = None,
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取路线列表"""
    query = db.query(Route)
    
    # 软删除过滤
    if not include_deleted:
        query = query.filter(Route.is_deleted == False)
    
    # 过滤条件
    if project_id:
        query = query.filter(Route.project_id == project_id)
    if status:
        query = query.filter(Route.status == status.value if hasattr(status, 'value') else status)
    if route_level:
        query = query.filter(Route.route_level == route_level.value if hasattr(route_level, 'value') else route_level)
    if search:
        query = query.filter(Route.name.ilike(f"%{search}%"))
    
    # 总数
    total = query.count()
    
    # 分页
    items = query.order_by(Route.created_at.desc()).offset(skip).limit(limit).all()
    
    return RouteListResponse(total=total, items=items)


@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取路线详情"""
    route = db.query(Route).filter(
        Route.route_id == route_id,
        Route.is_deleted == False
    ).first()
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路线不存在: {route_id}"
        )
    
    return route


@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: uuid.UUID,
    route_update: RouteUpdate,
    db: Session = Depends(get_db)
):
    """更新路线"""
    route = db.query(Route).filter(
        Route.route_id == route_id,
        Route.is_deleted == False
    ).first()
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路线不存在: {route_id}"
        )
    
    # 更新字段
    update_data = route_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "route_level" and value:
            value = value.value if hasattr(value, 'value') else value
        elif field == "status" and value:
            value = value.value if hasattr(value, 'value') else value
        elif field == "extra_data":
            value = _json_to_str(value)
        
        setattr(route, field, value)
    
    route.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(route)
    
    return route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    route_id: uuid.UUID,
    hard_delete: bool = Query(False, description="是否永久删除"),
    db: Session = Depends(get_db)
):
    """删除路线（软删除）"""
    route = db.query(Route).filter(Route.route_id == route_id).first()
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路线不存在: {route_id}"
        )
    
    if hard_delete:
        # 永久删除
        db.delete(route)
    else:
        # 软删除
        route.is_deleted = True
        route.updated_at = datetime.utcnow()
    
    db.commit()
    
    return None


@router.post("/{route_id}/restore", response_model=RouteResponse)
def restore_route(
    route_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """恢复已删除的路线"""
    route = db.query(Route).filter(
        Route.route_id == route_id,
        Route.is_deleted == True
    ).first()
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路线不存在或未被删除: {route_id}"
        )
    
    route.is_deleted = False
    route.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(route)
    
    return route
