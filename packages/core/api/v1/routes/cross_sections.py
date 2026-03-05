# NeuralSite CrossSection API 路由
# 横断面数据管理

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user, CurrentUser
from models.cross_section import (
    CrossSection, CrossSectionCreate, CrossSectionUpdate, CrossSectionResponse,
    CrossSectionBatchCreate, CrossSectionBatchResponse,
    CrossSectionType, MeasurementMethod,
    section_points_to_json, section_elements_to_json,
    json_to_section_points, json_to_section_elements
)


# 路由前缀
router = APIRouter(prefix="/api/v1/cross-sections", tags=["CrossSection - 横断面管理"])


# ==================== 横断面管理 ====================

@router.post("", response_model=CrossSectionResponse, status_code=status.HTTP_201_CREATED)
def create_cross_section(
    cross_section: CrossSectionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建横断面"""
    # 处理枚举类型
    cs_type = cross_section.cross_section_type.value if hasattr(cross_section.cross_section_type, 'value') else cross_section.cross_section_type
    meas_method = cross_section.measurement_method.value if cross_section.measurement_method and hasattr(cross_section.measurement_method, 'value') else cross_section.measurement_method
    
    db_cs = CrossSection(
        project_id=cross_section.project_id,
        route_id=cross_section.route_id,
        station=cross_section.station,
        station_display=cross_section.station_display,
        cross_section_type=cs_type,
        measured_at=cross_section.measured_at,
        measured_by=cross_section.measured_by or (current_user.user_id if current_user else None),
        measurement_method=meas_method,
        center_elevation=cross_section.center_elevation,
        left_elevation=cross_section.left_elevation,
        right_elevation=cross_section.right_elevation,
        points_json=section_points_to_json(cross_section.points) if cross_section.points else [],
        elements_json=section_elements_to_json(cross_section.elements) if cross_section.elements else [],
        description=cross_section.description,
        tags=cross_section.tags,
        extra_data=cross_section.extra_data
    )
    db.add(db_cs)
    db.commit()
    db.refresh(db_cs)
    
    # 返回响应时转换JSON
    return convert_db_to_response(db_cs)


@router.get("", response_model=List[CrossSectionResponse])
def list_cross_sections(
    project_id: Optional[uuid.UUID] = None,
    route_id: Optional[uuid.UUID] = None,
    station_start: Optional[float] = Query(None, description="起始桩号"),
    station_end: Optional[float] = Query(None, description="结束桩号"),
    cross_section_type: Optional[str] = Query(None, description="横断面类型"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取横断面列表"""
    query = db.query(CrossSection)
    
    if project_id:
        query = query.filter(CrossSection.project_id == project_id)
    if route_id:
        query = query.filter(CrossSection.route_id == route_id)
    if station_start is not None:
        query = query.filter(CrossSection.station >= station_start)
    if station_end is not None:
        query = query.filter(CrossSection.station <= station_end)
    if cross_section_type:
        query = query.filter(CrossSection.cross_section_type == cross_section_type)
    
    results = query.order_by(CrossSection.station).offset(skip).limit(limit).all()
    return [convert_db_to_response(r) for r in results]


@router.get("/{cross_section_id}", response_model=CrossSectionResponse)
def get_cross_section(
    cross_section_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取横断面详情"""
    cross_section = db.query(CrossSection).filter(CrossSection.cross_section_id == cross_section_id).first()
    if not cross_section:
        raise HTTPException(status_code=404, detail="横断面不存在")
    return convert_db_to_response(cross_section)


@router.put("/{cross_section_id}", response_model=CrossSectionResponse)
def update_cross_section(
    cross_section_id: uuid.UUID,
    cross_section: CrossSectionUpdate,
    db: Session = Depends(get_db)
):
    """更新横断面"""
    db_cs = db.query(CrossSection).filter(CrossSection.cross_section_id == cross_section_id).first()
    if not db_cs:
        raise HTTPException(status_code=404, detail="横断面不存在")
    
    update_data = cross_section.model_dump(exclude_unset=True)
    
    # 处理枚举类型
    if 'cross_section_type' in update_data and update_data['cross_section_type']:
        val = update_data['cross_section_type']
        update_data['cross_section_type'] = val.value if hasattr(val, 'value') else val
    if 'measurement_method' in update_data and update_data['measurement_method']:
        val = update_data['measurement_method']
        update_data['measurement_method'] = val.value if hasattr(val, 'value') else val
    
    # 处理points和elements列表
    if 'points' in update_data and update_data['points']:
        update_data['points_json'] = section_points_to_json(update_data.pop('points'))
    if 'elements' in update_data and update_data['elements']:
        update_data['elements_json'] = section_elements_to_json(update_data.pop('elements'))
    
    for key, value in update_data.items():
        setattr(db_cs, key, value)
    
    db_cs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_cs)
    return convert_db_to_response(db_cs)


@router.delete("/{cross_section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cross_section(
    cross_section_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除横断面"""
    cross_section = db.query(CrossSection).filter(CrossSection.cross_section_id == cross_section_id).first()
    if not cross_section:
        raise HTTPException(status_code=404, detail="横断面不存在")
    
    db.delete(cross_section)
    db.commit()
    return None


# ==================== 批量操作 ====================

@router.post("/batch", response_model=CrossSectionBatchResponse)
def batch_create_cross_sections(
    batch: CrossSectionBatchCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """批量创建横断面"""
    created = 0
    failed = 0
    errors = []
    
    for idx, cs_data in enumerate(batch.cross_sections):
        try:
            cs_type = cs_data.cross_section_type.value if hasattr(cs_data.cross_section_type, 'value') else cs_data.cross_section_type
            meas_method = cs_data.measurement_method.value if cs_data.measurement_method and hasattr(cs_data.measurement_method, 'value') else cs_data.measurement_method
            
            db_cs = CrossSection(
                project_id=cs_data.project_id,
                route_id=cs_data.route_id,
                station=cs_data.station,
                station_display=cs_data.station_display,
                cross_section_type=cs_type,
                measured_at=cs_data.measured_at,
                measured_by=cs_data.measured_by or (current_user.user_id if current_user else None),
                measurement_method=meas_method,
                center_elevation=cs_data.center_elevation,
                left_elevation=cs_data.left_elevation,
                right_elevation=cs_data.right_elevation,
                points_json=section_points_to_json(cs_data.points) if cs_data.points else [],
                elements_json=section_elements_to_json(cs_data.elements) if cs_data.elements else [],
                description=cs_data.description,
                tags=cs_data.tags,
                extra_data=cs_data.extra_data
            )
            db.add(db_cs)
            created += 1
        except Exception as e:
            failed += 1
            errors.append({
                "index": idx,
                "station": cs_data.station,
                "error": str(e)
            })
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return CrossSectionBatchResponse(
            created=0,
            failed=len(batch.cross_sections),
            errors=[{"error": str(e)}]
        )
    
    return CrossSectionBatchResponse(
        created=created,
        failed=failed,
        errors=errors
    )


# ==================== 辅助函数 ====================

def convert_db_to_response(db_cs: CrossSection) -> CrossSectionResponse:
    """将数据库模型转换为响应模型"""
    return CrossSectionResponse(
        project_id=db_cs.project_id,
        route_id=db_cs.route_id,
        station=db_cs.station,
        station_display=db_cs.station_display,
        cross_section_type=CrossSectionType(db_cs.cross_section_type),
        measured_at=db_cs.measured_at,
        measured_by=db_cs.measured_by,
        measurement_method=MeasurementMethod(db_cs.measurement_method) if db_cs.measurement_method else None,
        center_elevation=db_cs.center_elevation,
        left_elevation=db_cs.left_elevation,
        right_elevation=db_cs.right_elevation,
        points=json_to_section_points(db_cs.points_json) if db_cs.points_json else [],
        elements=json_to_section_elements(db_cs.elements_json) if db_cs.elements_json else [],
        description=db_cs.description,
        tags=db_cs.tags or [],
        extra_data=db_cs.extra_data or {},
        cross_section_id=db_cs.cross_section_id,
        created_at=db_cs.created_at,
        updated_at=db_cs.updated_at
    )
