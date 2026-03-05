# NeuralSite Route 模型
# 路线管理 - 对应 routes 表

from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# 使用统一的 Base
from models.p0_models import Base


# ==================== 枚举类 ====================

class RouteStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    CONSTRUCTION = "construction"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RouteLevel(str, Enum):
    MAIN_LINE = "main_line"       # 主线
    INTERCHANGE = "interchange"   # 互通立交
    RAMP = "ramp"                 # 匝道
    SERVICE_ROAD = "service_road" # 辅道


# ==================== Pydantic Schemas (API用) ====================

class RouteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    route_code: Optional[str] = Field(None, max_length=50)  # 路线编号，如 "K0+000 - K10+000"
    description: Optional[str] = None
    route_level: RouteLevel = RouteLevel.MAIN_LINE
    status: RouteStatus = RouteStatus.DRAFT
    
    # 里程信息
    start_station: Optional[float] = None  # 起始桩号
    end_station: Optional[float] = None    # 结束桩号
    total_length: Optional[float] = None   # 总长度(km)
    
    # 地理信息
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None


class RouteCreate(RouteBase):
    project_id: uuid.UUID
    extra_data: Optional[dict] = None


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    route_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    route_level: Optional[RouteLevel] = None
    status: Optional[RouteStatus] = None
    start_station: Optional[float] = None
    end_station: Optional[float] = None
    total_length: Optional[float] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    extra_data: Optional[dict] = None


class RouteResponse(RouteBase):
    route_id: uuid.UUID
    project_id: uuid.UUID
    extra_data: Optional[dict] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteListResponse(BaseModel):
    """路线列表响应"""
    total: int
    items: List[RouteResponse]


# ==================== SQLAlchemy Model (数据库用) ====================

class Route(Base):
    __tablename__ = "routes"

    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    route_code = Column(String(50))
    description = Column(Text)
    route_level = Column(String(20), default="main_line", index=True)
    status = Column(String(20), default="draft", index=True)
    
    # 里程信息
    start_station = Column(Numeric(18, 4))
    end_station = Column(Numeric(18, 4))
    total_length = Column(Numeric(18, 4))  # 单位: km
    
    # 地理坐标
    start_latitude = Column(Numeric(11, 8))
    start_longitude = Column(Numeric(12, 8))
    end_latitude = Column(Numeric(11, 8))
    end_longitude = Column(Numeric(12, 8))
    
    # 扩展数据
    extra_data = Column(Text)  # JSON存储
    
    # 软删除
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="routes")

    __table_args__ = (
        Index('idx_route_project_status', 'project_id', 'status'),
        Index('idx_route_project_level', 'project_id', 'route_level'),
    )
