# NeuralSite Station 桩号数据模型
# 存储工程桩号、坐标、高程等信息

from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.p0_models import Base


# ==================== 枚举类 ====================

class StationType(str, Enum):
    """桩号类型"""
    MILESTONE = "milestone"        # 里程碑
    KILOMETER = "kilometer"         # 公里桩
    HUNDRED = "hundred"             # 百米桩
    PLUS = "plus"                   # 加桩
    BRIDGE = "bridge"              # 桥墩/桥台
    TUNNEL = "tunnel"               # 隧道
    CULVERT = "culvert"             # 涵洞
    INTERCHANGE = "interchange"     # 互通
    OTHER = "other"


class CoordinateSystem(str, Enum):
    """坐标系"""
    WGS84 = "WGS84"
    CGCS2000 = "CGCS2000"
    XIAN80 = "Xian80"
    LOCAL = "local"


# ==================== Pydantic Schemas (API用) ====================

class StationBase(BaseModel):
    """桩号基础字段"""
    project_id: uuid.UUID
    route_id: uuid.UUID
    
    # 桩号信息
    station: float = Field(..., description="桩号(米)")
    station_display: Optional[str] = Field(None, description="显示用桩号,如K1+200")
    station_type: StationType = StationType.PLUS
    
    # 坐标
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    elevation: Optional[float] = Field(None, description="高程(米)")
    x: Optional[float] = Field(None, description="X坐标(平面)")
    y: Optional[float] = Field(None, description="Y坐标(平面)")
    z: Optional[float] = Field(None, description="Z坐标(高程)")
    coordinate_system: Optional[CoordinateSystem] = Field(None, description="坐标系")
    
    # 附加信息
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    extra_data: Optional[dict] = Field(default_factory=dict, description="附加元数据")


class StationCreate(StationBase):
    """创建桩号"""
    created_by: Optional[uuid.UUID] = None


class StationUpdate(BaseModel):
    """更新桩号"""
    station: Optional[float] = None
    station_display: Optional[str] = None
    station_type: Optional[StationType] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    elevation: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    coordinate_system: Optional[CoordinateSystem] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class StationResponse(StationBase):
    """桩号响应"""
    station_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationBatchCreate(BaseModel):
    """批量创建桩号"""
    stations: List[StationCreate] = Field(..., description="桩号列表")


class StationBatchResponse(BaseModel):
    """批量创建响应"""
    created: int = Field(..., description="成功创建数量")
    failed: int = Field(..., description="失败数量")
    errors: List[dict] = Field(default_factory=list, description="错误详情")


class StationCoordinatesResponse(BaseModel):
    """桩号坐标查询响应"""
    station: float
    station_display: Optional[str] = None
    route_id: uuid.UUID
    project_id: uuid.UUID
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    elevation: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


# ==================== SQLAlchemy Models (数据库用) ====================

class Station(Base):
    """桩号数据表"""
    __tablename__ = "stations"

    station_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    route_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    
    # 桩号信息
    station = Column(Numeric(18, 4), nullable=False, index=True)
    station_display = Column(String(30), index=True)
    station_type = Column(String(20), default="plus")
    
    # 坐标 (WGS84)
    longitude = Column(Numeric(12, 8))
    latitude = Column(Numeric(11, 8))
    elevation = Column(Numeric(12, 4))
    
    # 平面坐标
    x = Column(Numeric(18, 4))
    y = Column(Numeric(18, 4))
    z = Column(Numeric(12, 4))
    coordinate_system = Column(String(20))
    
    # 附加信息
    description = Column(Text)
    tags = Column(JSON)
    extra_data = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_station_project_route', 'project_id', 'route_id', 'station'),
        Index('idx_station_display', 'station_display'),
    )


# ==================== 索引/视图辅助 ====================

# Station 可以关联到 Photo/Issue 等, 通过 station 字段
