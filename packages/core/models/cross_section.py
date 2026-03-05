# NeuralSite CrossSection 横断面数据模型
# 存储横断面测量数据、要素信息等

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

class CrossSectionType(str, Enum):
    """横断面类型"""
    ROAD = "road"                  # 道路横断面
    BRIDGE = "bridge"              # 桥梁横断面
    TUNNEL = "tunnel"              # 隧道横断面
    CULVERT = "culvert"            # 涵洞横断面
    RETAINING = "retaining"        # 挡土墙横断面
    SLOPE = "slope"                # 边坡横断面
    OTHER = "other"


class MeasurementMethod(str, Enum):
    """测量方法"""
    TOTAL_STATION = "total_station"    # 全站仪
    GPS = "GPS"                        # GPS
    LEVEL = "level"                    # 水准仪
    DRONE = "drone"                    # 无人机
    LASER_SCANNER = "laser_scanner"   # 激光扫描
    MANUAL = "manual"                  # 人工


# ==================== 横断面要素模型 ====================

class SectionPoint(BaseModel):
    """横断面要素点"""
    distance: float = Field(..., description="距中桩距离(米),左负右正")
    elevation: float = Field(..., description="高程(米)")
    point_type: str = Field(default="terrain", description="点类型:terrain/edge/kerb/ditch")
    description: Optional[str] = Field(None, description="描述")


class SectionElement(BaseModel):
    """横断面结构要素"""
    element_type: str = Field(..., description="要素类型:lane/shoulder/median/ditch/slope")
    start_distance: float = Field(..., description="起点距中桩距离")
    end_distance: float = Field(..., description="终点距中桩距离")
    start_elevation: Optional[float] = Field(None, description="起点高程")
    end_elevation: Optional[float] = Field(None, description="终点高程")
    width: Optional[float] = Field(None, description="宽度")
    slope: Optional[float] = Field(None, description="坡度(%)")


# ==================== Pydantic Schemas (API用) ====================

class CrossSectionBase(BaseModel):
    """横断面基础字段"""
    project_id: uuid.UUID
    route_id: uuid.UUID
    
    # 桩号信息
    station: float = Field(..., description="桩号(米)")
    station_display: Optional[str] = Field(None, description="显示用桩号")
    cross_section_type: CrossSectionType = CrossSectionType.ROAD
    
    # 测量信息
    measured_at: Optional[datetime] = Field(None, description="测量时间")
    measured_by: Optional[uuid.UUID] = Field(None, description="测量人")
    measurement_method: Optional[MeasurementMethod] = Field(None, description="测量方法")
    
    # 高程数据
    center_elevation: Optional[float] = Field(None, description="中桩高程")
    left_elevation: Optional[float] = Field(None, description="左侧高程")
    right_elevation: Optional[float] = Field(None, description="右侧高程")
    
    # 地形点数据
    points: Optional[List[SectionPoint]] = Field(default_factory=list, description="地形点列表")
    
    # 结构要素
    elements: Optional[List[SectionElement]] = Field(default_factory=list, description="结构要素")
    
    # 附加信息
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    extra_data: Optional[dict] = Field(default_factory=dict, description="附加元数据")


class CrossSectionCreate(CrossSectionBase):
    """创建横断面"""
    pass


class CrossSectionUpdate(BaseModel):
    """更新横断面"""
    station: Optional[float] = None
    station_display: Optional[str] = None
    cross_section_type: Optional[CrossSectionType] = None
    measured_at: Optional[datetime] = None
    measured_by: Optional[uuid.UUID] = None
    measurement_method: Optional[MeasurementMethod] = None
    center_elevation: Optional[float] = None
    left_elevation: Optional[float] = None
    right_elevation: Optional[float] = None
    points: Optional[List[SectionPoint]] = None
    elements: Optional[List[SectionElement]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class CrossSectionResponse(CrossSectionBase):
    """横断面响应"""
    cross_section_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrossSectionBatchCreate(BaseModel):
    """批量创建横断面"""
    cross_sections: List[CrossSectionCreate] = Field(..., description="横断面列表")


class CrossSectionBatchResponse(BaseModel):
    """批量创建响应"""
    created: int = Field(..., description="成功创建数量")
    failed: int = Field(..., description="失败数量")
    errors: List[dict] = Field(default_factory=list, description="错误详情")


# ==================== SQLAlchemy Models (数据库用) ====================

class CrossSection(Base):
    """横断面数据表"""
    __tablename__ = "cross_sections"

    cross_section_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    route_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    measured_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    
    # 桩号信息
    station = Column(Numeric(18, 4), nullable=False, index=True)
    station_display = Column(String(30), index=True)
    cross_section_type = Column(String(20), default="road")
    
    # 测量信息
    measured_at = Column(DateTime)
    measurement_method = Column(String(20))
    
    # 高程数据
    center_elevation = Column(Numeric(12, 4))
    left_elevation = Column(Numeric(12, 4))
    right_elevation = Column(Numeric(12, 4))
    
    # 地形点JSON
    points_json = Column(JSON, default=list)
    
    # 结构要素JSON
    elements_json = Column(JSON, default=list)
    
    # 附加信息
    description = Column(Text)
    tags = Column(JSON)
    extra_data = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_cs_project_route_station', 'project_id', 'route_id', 'station'),
    )


# ==================== 辅助函数 ====================

def section_points_to_json(points: List[SectionPoint]) -> list:
    """转换地形点为JSON"""
    return [p.model_dump() for p in points]


def section_elements_to_json(elements: List[SectionElement]) -> list:
    """转换结构要素为JSON"""
    return [e.model_dump() for e in elements]


def json_to_section_points(data: list) -> List[SectionPoint]:
    """从JSON转换地形点"""
    return [SectionPoint(**p) for p in data]


def json_to_section_elements(data: list) -> List[SectionElement]:
    """从JSON转换结构要素"""
    return [SectionElement(**e) for e in data]
