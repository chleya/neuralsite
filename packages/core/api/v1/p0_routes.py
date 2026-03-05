# NeuralSite P0 API 路由
# 照片管理 + 问题跟踪 + 用户权限
# 已连接真实服务

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from api.deps import get_db, get_current_user
from models.p0_models import (
    User, UserCreate, UserResponse,
    PhotoRecord, PhotoCreate, PhotoUpdate, PhotoResponse,
    Issue, IssueCreate, IssueUpdate, IssueResponse,
    SyncQueue, SyncStatus, IssueStatus, UserRole
)
from services.photo_service import PhotoService
from services.issue_service import IssueService

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 路由前缀
router = APIRouter(prefix="/api/v1", tags=["P0 - 基础功能"])


# ==================== 用户管理 ====================

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 加密密码
    hashed_password = pwd_context.hash(user.password)
    
    # 创建用户
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        real_name=user.real_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/auth/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # TODO: 返回JWT token
    return {
        "access_token": "mock_token",
        "token_type": "bearer",
        "user_id": str(user.user_id),
        "role": user.role
    }


@router.get("/users", response_model=List[UserResponse])
def list_users(
    project_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    query = db.query(User)
    if project_id:
        query = query.filter(User.project_id == project_id)
    if role:
        query = query.filter(User.role == role)
    return query.offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


# ==================== 照片管理 ====================

@router.post("/photos/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    project_id: uuid.UUID = None,
    station: Optional[float] = None,
    station_display: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    description: Optional[str] = None,
    captured_by: uuid.UUID = None,
    local_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """上传照片"""
    service = PhotoService(db)
    return await service.create_photo(
        file=file,
        project_id=project_id,
        station=station,
        station_display=station_display,
        latitude=latitude,
        longitude=longitude,
        description=description,
        captured_by=captured_by,
        local_id=local_id
    )


@router.get("/photos", response_model=List[PhotoResponse])
def list_photos(
    project_id: Optional[uuid.UUID] = None,
    station_start: Optional[float] = None,
    station_end: Optional[float] = None,
    captured_by: Optional[uuid.UUID] = None,
    is_verified: Optional[bool] = None,
    sync_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询照片列表"""
    service = PhotoService(db)
    return service.list_photos(
        project_id=project_id,
        station_start=station_start,
        station_end=station_end,
        captured_by=captured_by,
        is_verified=is_verified,
        sync_status=sync_status,
        skip=skip,
        limit=limit
    )


@router.get("/photos/{photo_id}", response_model=PhotoResponse)
def get_photo(photo_id: uuid.UUID, db: Session = Depends(get_db)):
    """获取照片详情"""
    service = PhotoService(db)
    photo = service.get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return photo


@router.put("/photos/{photo_id}", response_model=PhotoResponse)
def update_photo(
    photo_id: uuid.UUID,
    photo: PhotoUpdate,
    db: Session = Depends(get_db)
):
    """更新照片信息"""
    service = PhotoService(db)
    updated = service.update_photo(photo_id, photo)
    if not updated:
        raise HTTPException(status_code=404, detail="照片不存在")
    return updated


@router.post("/photos/{photo_id}/verify", response_model=PhotoResponse)
def verify_photo(
    photo_id: uuid.UUID,
    verified_by: uuid.UUID,
    db: Session = Depends(get_db)
):
    """人工确认照片"""
    service = PhotoService(db)
    verified = service.verify_photo(photo_id, verified_by)
    if not verified:
        raise HTTPException(status_code=404, detail="照片不存在")
    return verified


# ==================== 问题管理 ====================

@router.post("/issues", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue: IssueCreate,
    db: Session = Depends(get_db)
):
    """创建问题"""
    service = IssueService(db)
    return service.create_issue(issue)


@router.get("/issues", response_model=List[IssueResponse])
def list_issues(
    project_id: Optional[uuid.UUID] = None,
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[uuid.UUID] = None,
    reported_by: Optional[uuid.UUID] = None,
    station_start: Optional[float] = None,
    station_end: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询问题列表"""
    service = IssueService(db)
    return service.list_issues(
        project_id=project_id,
        issue_type=issue_type,
        severity=severity,
        status=status,
        assigned_to=assigned_to,
        reported_by=reported_by,
        station_start=station_start,
        station_end=station_end,
        skip=skip,
        limit=limit
    )


@router.get("/issues/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: uuid.UUID, db: Session = Depends(get_db)):
    """获取问题详情"""
    service = IssueService(db)
    issue = service.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    return issue


@router.put("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: uuid.UUID,
    issue: IssueUpdate,
    db: Session = Depends(get_db)
):
    """更新问题"""
    service = IssueService(db)
    updated = service.update_issue(issue_id, issue)
    if not updated:
        raise HTTPException(status_code=404, detail="问题不存在")
    return updated


@router.post("/issues/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: uuid.UUID,
    assigned_to: uuid.UUID,
    db: Session = Depends(get_db)
):
    """分配问题"""
    service = IssueService(db)
    assigned = service.assign_issue(issue_id, assigned_to)
    if not assigned:
        raise HTTPException(status_code=404, detail="问题不存在")
    return assigned


@router.post("/issues/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: uuid.UUID,
    resolved_by: uuid.UUID,
    resolution_note: str,
    db: Session = Depends(get_db)
):
    """解决问题"""
    service = IssueService(db)
    resolved = service.resolve_issue(issue_id, resolved_by, resolution_note)
    if not resolved:
        raise HTTPException(status_code=404, detail="问题不存在")
    return resolved


# ==================== 仪表盘统计 ====================

@router.get("/dashboard/summary")
def get_dashboard_summary(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取项目仪表盘汇总"""
    photo_service = PhotoService(db)
    issue_service = IssueService(db)
    
    photos = photo_service.list_photos(project_id=project_id, limit=1000)
    issues = issue_service.list_issues(project_id=project_id, limit=1000)
    
    return {
        "project_id": str(project_id),
        "photo_stats": {
            "total": len(photos),
            "verified": sum(1 for p in photos if p.is_verified),
            "pending_verify": sum(1 for p in photos if not p.is_verified),
        },
        "issue_stats": {
            "total": len(issues),
            "open": sum(1 for i in issues if i.status == "open"),
            "in_progress": sum(1 for i in issues if i.status == "in_progress"),
            "resolved": sum(1 for i in issues if i.status == "resolved"),
            "closed": sum(1 for i in issues if i.status == "closed"),
        }
    }
