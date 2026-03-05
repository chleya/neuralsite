# -*- coding: utf-8 -*-
"""
BIM 数据模型

定义 IFC 元素到 NeuralSite 实体的映射结构
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


class IFCVersion(str, Enum):
    """IFC 版本"""
    IFC2X3 = "IFC2X3"
    IFC4 = "IFC4"
    IFC4X1 = "IFC4X1"


class ElementType(str, Enum):
    """BIM 构件类型映射到 NeuralSite 实体类型"""
    # 结构
    BEAM = "beam"           # 梁
    COLUMN = "column"       # 柱
    WALL = "wall"           # 墙
    SLAB = "slab"           # 板/楼板
    FOUNDATION = "foundation"  # 基础
    
    # 建筑
    DOOR = "door"           # 门
    WINDOW = "window"       # 窗
    STAIRS = "stairs"       # 楼梯
    RAILING = "railing"     # 栏杆
    
    # 机电
    DUCT = "duct"           # 风管
    PIPE = "pipe"           # 管道
    EQUIPMENT = "equipment" # 设备
    
    # 其他
    SPACE = "space"         # 空间
    SITE = "site"           # 场地
    BUILDING = "building"   # 建筑
    STOREY = "storey"       # 楼层
    UNKNOWN = "unknown"     # 未知


class PropertyType(str, Enum):
    """属性类型"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    REFERENCE = "reference"


class BIMProperty(BaseModel):
    """BIM 属性"""
    name: str
    value: Any
    type: PropertyType = PropertyType.STRING
    unit: Optional[str] = None
    category: Optional[str] = None
    
    
class BIMGeometry(BaseModel):
    """BIM 几何数据"""
    type: str  # "box", "extruded", "bspline", "triangulated"
    
    # 边界盒
    bounding_box: Optional[Dict[str, float]] = None
    
    # 拉伸体
    extrusion: Optional[Dict[str, Any]] = None
    
    # 三角网格
    triangulated: Optional[Dict[str, Any]] = None
    
    # 原始 IFC 几何句柄
    ifc_geometry_handle: Optional[str] = None


class BIMElement(BaseModel):
    """BIM 构件"""
    id: str  # IFC GUID
    global_id: str  # 全局唯一ID
    
    # 类型信息
    ifc_type: str  # 如 "IfcBeam", "IfcWall"
    element_type: ElementType = ElementType.UNKNOWN
    
    # 几何
    geometry: Optional[BIMGeometry] = None
    
    # 位置 (局部坐标，相对于父构件)
    position: Optional[Dict[str, float]] = None
    
    # 属性
    properties: List[BIMProperty] = []
    
    # 名称和描述
    name: Optional[str] = None
    description: Optional[str] = None
    
    # 材质
    material: Optional[str] = None
    
    # 层级关系
    storey_id: Optional[str] = None  # 所属楼层
    building_id: Optional[str] = None  # 所属建筑


class BIMStorey(BaseModel):
    """BIM 楼层"""
    id: str
    global_id: str
    
    name: str
    elevation: float = 0.0  # 标高
    
    # 构件
    element_ids: List[str] = []
    
    # 边界盒
    bounding_box: Optional[Dict[str, float]] = None


class BIMBuilding(BaseModel):
    """BIM 建筑"""
    id: str
    global_id: str
    
    name: str
    
    # 楼层
    storeys: List[BIMStorey] = []
    
    # 顶层构件 (不在楼层内的)
    top_level_elements: List[BIMElement] = []
    
    # 边界盒
    bounding_box: Optional[Dict[str, float]] = None


class BIMProject(BaseModel):
    """BIM 项目"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    ifc_version: IFCVersion
    
    # 建筑
    buildings: List[BIMBuilding] = []
    
    # 所有构件
    elements: Dict[str, BIMElement] = {}  # id -> element
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    source_file: Optional[str] = None
    
    # 统计
    total_elements: int = 0
    element_type_counts: Dict[str, int] = {}
    
    
class ImportStatus(str, Enum):
    """导入状态"""
    PENDING = "pending"
    PARSING = "parsing"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportError(BaseModel):
    """导入错误"""
    code: str
    message: str
    element_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ImportProgress(BaseModel):
    """导入进度"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    
    status: ImportStatus = ImportStatus.PENDING
    
    # 进度 (0-100)
    progress: float = 0.0
    
    # 阶段消息
    message: str = ""
    
    # 统计
    total_elements: int = 0
    processed_elements: int = 0
    
    # 错误
    errors: List[ImportError] = []
    
    # 结果
    result: Optional[BIMProject] = None
    
    # 时间
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
