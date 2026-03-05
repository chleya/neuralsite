# NeuralSite Project API
# 项目管理 CRUD 接口

from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import json

from api.deps import get_db
from models.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectListResponse, ProjectStatus, ProjectType
)
from models.p0_models import Base

router = APIRouter(prefix="/api/v1/projects", tags=["Projects - 项目管理"])


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

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """创建项目"""
    db_project = Project(
        project_id=uuid.uuid4(),
        name=project.name,
        description=project.description,
        project_type=project.project_type.value if hasattr(project.project_type, 'value') else project.project_type,
        status=project.status.value if hasattr(project.status, 'value') else project.status,
        location=project.location,
        start_date=project.start_date,
        end_date=project.end_date,
        owner_id=project.owner_id,
        extra_data=_json_to_str(project.extra_data),
        is_deleted=False
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ProjectStatus] = None,
    project_type: Optional[ProjectType] = None,
    owner_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project)
    
    # 软删除过滤
    if not include_deleted:
        query = query.filter(Project.is_deleted == False)
    
    # 过滤条件
    if status:
        query = query.filter(Project.status == status.value if hasattr(status, 'value') else status)
    if project_type:
        query = query.filter(Project.project_type == project_type.value if hasattr(project_type, 'value') else project_type)
    if owner_id:
        query = query.filter(Project.owner_id == owner_id)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    
    # 总数
    total = query.count()
    
    # 分页
    items = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    
    return ProjectListResponse(total=total, items=items)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == False
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {project_id}"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == False
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {project_id}"
        )
    
    # 更新字段
    update_data = project_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "project_type" and value:
            value = value.value if hasattr(value, 'value') else value
        elif field == "status" and value:
            value = value.value if hasattr(value, 'value') else value
        elif field == "extra_data":
            value = _json_to_str(value)
        
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    hard_delete: bool = Query(False, description="是否永久删除"),
    db: Session = Depends(get_db)
):
    """删除项目（软删除）"""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {project_id}"
        )
    
    if hard_delete:
        # 永久删除
        db.delete(project)
    else:
        # 软删除
        project.is_deleted = True
        project.updated_at = datetime.utcnow()
    
    db.commit()
    
    return None


@router.post("/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """恢复已删除的项目"""
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.is_deleted == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在或未被删除: {project_id}"
        )
    
    project.is_deleted = False
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


from datetime import datetime
