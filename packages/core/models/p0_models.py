# NeuralSite P0 数据模型
# 对应数据库迁移脚本 001_p0_baseline.sql

from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ==================== 枚举类 ====================

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ENGINEER = "engineer"
    WORKER = "worker"


class IssueType(str, Enum):
    QUALITY = "quality"
    SAFETY = "safety"
    PROGRESS = "progress"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


class OperationType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


# ==================== Pydantic Schemas (API用) ====================

class UserBase(BaseModel):
    username: str
    real_name: Optional[str] = None
    role: UserRole = UserRole.WORKER
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    project_id: uuid.UUID
    file_path: str
    captured_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    station: Optional[float] = None
    station_display: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class PhotoCreate(PhotoBase):
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    captured_by: Optional[uuid.UUID] = None
    gps_accuracy: Optional[float] = None
    entity_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = None
    local_id: Optional[str] = None  # 离线端本地ID


class PhotoUpdate(BaseModel):
    station: Optional[float] = None
    station_display: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    verified_by: Optional[uuid.UUID] = None


class PhotoResponse(PhotoBase):
    photo_id: uuid.UUID
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    captured_by: Optional[uuid.UUID] = None
    gps_accuracy: Optional[float] = None
    ai_classification: Optional[dict] = None
    is_verified: bool = False
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    entity_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.PENDING
    local_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IssueBase(BaseModel):
    project_id: uuid.UUID
    issue_type: IssueType
    title: str
    description: Optional[str] = None
    severity: IssueSeverity = IssueSeverity.MEDIUM


class IssueCreate(IssueBase):
    station: Optional[float] = None
    station_display: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_description: Optional[str] = None
    photo_ids: Optional[List[uuid.UUID]] = []
    reported_by: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    deadline: Optional[datetime] = None
    local_id: Optional[str] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IssueSeverity] = None
    status: Optional[IssueStatus] = None
    assigned_to: Optional[uuid.UUID] = None
    resolved_by: Optional[uuid.UUID] = None
    resolution_note: Optional[str] = None
    deadline: Optional[datetime] = None
    photo_ids: Optional[List[uuid.UUID]] = None


class IssueResponse(IssueBase):
    issue_id: uuid.UUID
    station: Optional[float] = None
    station_display: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_description: Optional[str] = None
    photo_ids: List[uuid.UUID] = []
    status: IssueStatus = IssueStatus.OPEN
    reported_by: Optional[uuid.UUID] = None
    reported_at: datetime
    assigned_to: Optional[uuid.UUID] = None
    assigned_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    deadline: Optional[datetime] = None
    ai_screening: Optional[dict] = None
    sync_status: SyncStatus = SyncStatus.PENDING
    local_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncQueueItem(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    operation: OperationType
    payload: dict
    device_id: Optional[str] = None
    app_version: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== SQLAlchemy Models (数据库用) ====================

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    real_name = Column(String(100))
    role = Column(String(20), default="worker")
    project_id = Column(UUID(as_uuid=True))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PhotoRecord(Base):
    __tablename__ = "photo_records"

    photo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64))
    file_size = Column(Integer)
    mime_type = Column(String(50))
    captured_at = Column(DateTime, nullable=False)
    captured_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    
    # GPS
    latitude = Column(Numeric(11, 8))
    longitude = Column(Numeric(12, 8))
    gps_accuracy = Column(Numeric(8, 2))
    
    # 桩号
    station = Column(Numeric(18, 4), index=True)
    station_display = Column(String(20))
    
    # AI分类
    ai_classification = Column(JSON)
    
    # 人工确认
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    verified_at = Column(DateTime)
    
    # 关联
    entity_id = Column(UUID(as_uuid=True))
    entity_type = Column(String(50))
    description = Column(Text)
    tags = Column(JSON)
    
    # 同步
    sync_status = Column(String(20), default="pending", index=True)
    local_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_photo_project_station', 'project_id', 'station'),
    )


class Issue(Base):
    __tablename__ = "issues"

    issue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    issue_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="medium", index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 位置
    station = Column(Numeric(18, 4), index=True)
    station_display = Column(String(20))
    latitude = Column(Numeric(11, 8))
    longitude = Column(Numeric(12, 8))
    location_description = Column(String(500))
    
    # 关联照片
    photo_ids = Column(JSON)
    
    # 状态
    status = Column(String(20), default="open", index=True)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), index=True)
    reported_at = Column(DateTime, default=datetime.utcnow)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), index=True)
    assigned_at = Column(DateTime)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    resolved_at = Column(DateTime)
    resolution_note = Column(Text)
    deadline = Column(DateTime)
    
    # AI初筛
    ai_screening = Column(JSON)
    
    # 同步
    sync_status = Column(String(20), default="pending", index=True)
    local_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_issue_project_status', 'project_id', 'status'),
    )


class SyncQueue(Base):
    __tablename__ = "sync_queue"

    queue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    operation = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    
    device_id = Column(String(100))
    app_version = Column(String(20))
    
    status = Column(String(20), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
