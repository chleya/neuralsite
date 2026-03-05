# NeuralSite Project 模型
# 项目管理 - 对应 projects 表

from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# 使用统一的 Base
from models.p0_models import Base


# ==================== 枚举类 ====================

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    HIGHWAY = "highway"
    URBAN_ROAD = "urban_road"
    BRIDGE = "bridge"
    TUNNEL = "tunnel"
    MIXED = "mixed"


# ==================== Pydantic Schemas (API用) ====================

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.HIGHWAY
    status: ProjectStatus = ProjectStatus.DRAFT
    location: Optional[str] = None  # 项目位置
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    owner_id: Optional[uuid.UUID] = None
    extra_data: Optional[dict] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    extra_data: Optional[dict] = None


class ProjectResponse(ProjectBase):
    project_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None
    extra_data: Optional[dict] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    items: List[ProjectResponse]


# ==================== SQLAlchemy Model (数据库用) ====================

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    project_type = Column(String(20), default="highway", index=True)
    status = Column(String(20), default="draft", index=True)
    
    # 项目信息
    location = Column(String(500))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # 所有者
    owner_id = Column(UUID(as_uuid=True))
    
    # 扩展数据
    extra_data = Column(Text)  # JSON存储
    
    # 软删除
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    routes = relationship("Route", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_project_status', 'status'),
        Index('idx_project_owner', 'owner_id'),
    )
