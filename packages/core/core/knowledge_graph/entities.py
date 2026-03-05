# -*- coding: utf-8 -*-
"""
知识图谱实体定义
使用 dataclass 定义实体类型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class EntityType(Enum):
    """实体类型枚举"""
    STANDARD = "standard"        # 规范
    PROCESS = "process"          # 工艺
    MATERIAL = "material"         # 材料
    QUALITY_STANDARD = "quality_standard"  # 质量标准
    PROJECT = "project"           # 项目
    ROUTE = "route"              # 路线
    STRUCTURE = "structure"      # 结构物


@dataclass
class Entity:
    """基础实体类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    entity_type: EntityType = EntityType.STANDARD
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entity_type": self.entity_type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """从字典创建"""
        entity_type = EntityType(data.get("entity_type", "standard"))
        
        # 根据类型返回对应实体
        if entity_type == EntityType.STANDARD:
            return Standard.from_dict(data)
        elif entity_type == EntityType.PROCESS:
            return Process.from_dict(data)
        elif entity_type == EntityType.MATERIAL:
            return Material.from_dict(data)
        elif entity_type == EntityType.QUALITY_STANDARD:
            return QualityStandard.from_dict(data)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=entity_type,
            properties=data.get("properties", {}),
        )


@dataclass
class Standard(Entity):
    """规范实体
    
    属性:
        code: 规范编号，如 "JTG D20-2017"
        category: 分类，如 "设计规范"、"施工规范"
        version: 版本
        scope: 适用范围描述
    """
    code: str = ""           # 规范编号
    category: str = ""        # 分类
    version: str = ""         # 版本
    scope: str = ""           # 适用范围
    
    def __post_init__(self):
        self.entity_type = EntityType.STANDARD
        if not self.properties:
            self.properties = {
                "code": self.code,
                "category": self.category,
                "version": self.version,
                "scope": self.scope,
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Standard':
        """从字典创建规范"""
        props = data.get("properties", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=EntityType.STANDARD,
            properties=data.get("properties", {}),
            code=props.get("code", data.get("code", "")),
            category=props.get("category", data.get("category", "")),
            version=props.get("version", data.get("version", "")),
            scope=props.get("scope", data.get("scope", "")),
        )


@dataclass
class Process(Entity):
    """工艺实体
    
    属性:
        process_type: 工艺类型，如 "基层施工"、"面层施工"
        steps: 施工步骤列表
        duration: 预计工期(天)
        conditions: 施工条件要求
    """
    process_type: str = ""       # 工艺类型
    steps: List[str] = field(default_factory=list)  # 施工步骤
    duration: float = 0          # 预计工期(天)
    conditions: str = ""         # 施工条件
    
    def __post_init__(self):
        self.entity_type = EntityType.PROCESS
        if not self.properties:
            self.properties = {
                "process_type": self.process_type,
                "steps": self.steps,
                "duration": self.duration,
                "conditions": self.conditions,
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Process':
        """从字典创建工艺"""
        props = data.get("properties", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=EntityType.PROCESS,
            properties=data.get("properties", {}),
            process_type=props.get("process_type", data.get("process_type", "")),
            steps=props.get("steps", data.get("steps", [])),
            duration=props.get("duration", data.get("duration", 0)),
            conditions=props.get("conditions", data.get("conditions", "")),
        )


@dataclass
class Material(Entity):
    """材料实体
    
    属性:
        material_type: 材料类型，如 "沥青混凝土"、"水泥混凝土"
        specs: 规格参数
        supplier: 供应商
        storage_conditions: 存储条件
    """
    material_type: str = ""           # 材料类型
    specs: Dict[str, Any] = field(default_factory=dict)  # 规格参数
    supplier: str = ""                  # 供应商
    storage_conditions: str = ""        # 存储条件
    
    def __post_init__(self):
        self.entity_type = EntityType.MATERIAL
        if not self.properties:
            self.properties = {
                "material_type": self.material_type,
                "specs": self.specs,
                "supplier": self.supplier,
                "storage_conditions": self.storage_conditions,
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        """从字典创建材料"""
        props = data.get("properties", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=EntityType.MATERIAL,
            properties=data.get("properties", {}),
            material_type=props.get("material_type", data.get("material_type", "")),
            specs=props.get("specs", data.get("specs", {})),
            supplier=props.get("supplier", data.get("supplier", "")),
            storage_conditions=props.get("storage_conditions", data.get("storage_conditions", "")),
        )


@dataclass
class QualityStandard(Entity):
    """质量标准实体
    
    属性:
        standard_code: 对应规范编号
       指标名称
        指标值
        检测方法
    """
    standard_code: str = ""      # 对应规范编号
    index_name: str = ""         # 指标名称
    index_value: Any = None      # 指标值
    test_method: str = ""        # 检测方法
    tolerance: str = ""          # 允许偏差
    
    def __post_init__(self):
        self.entity_type = EntityType.QUALITY_STANDARD
        if not self.properties:
            self.properties = {
                "standard_code": self.standard_code,
                "index_name": self.index_name,
                "index_value": str(self.index_value) if self.index_value is not None else None,
                "test_method": self.test_method,
                "tolerance": self.tolerance,
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityStandard':
        """从字典创建质量标准"""
        props = data.get("properties", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=EntityType.QUALITY_STANDARD,
            properties=data.get("properties", {}),
            standard_code=props.get("standard_code", data.get("standard_code", "")),
            index_name=props.get("index_name", data.get("index_name", "")),
            index_value=props.get("index_value", data.get("index_value")),
            test_method=props.get("test_method", data.get("test_method", "")),
            tolerance=props.get("tolerance", data.get("tolerance", "")),
        )


# 便捷函数：创建实体
def create_standard(name: str, code: str, category: str = "", 
                   description: str = "", version: str = "1.0") -> Standard:
    """创建规范实体"""
    return Standard(
        name=name,
        code=code,
        category=category,
        description=description,
        version=version,
    )


def create_process(name: str, process_type: str, steps: List[str] = None,
                   description: str = "", duration: float = 0) -> Process:
    """创建工艺实体"""
    return Process(
        name=name,
        process_type=process_type,
        steps=steps or [],
        description=description,
        duration=duration,
    )


def create_material(name: str, material_type: str, specs: Dict[str, Any] = None,
                    description: str = "") -> Material:
    """创建材料实体"""
    return Material(
        name=name,
        material_type=material_type,
        specs=specs or {},
        description=description,
    )


def create_quality_standard(name: str, standard_code: str, index_name: str,
                           index_value: Any, test_method: str = "", 
                           tolerance: str = "") -> QualityStandard:
    """创建质量标准实体"""
    return QualityStandard(
        name=name,
        standard_code=standard_code,
        index_name=index_name,
        index_value=index_value,
        test_method=test_method,
        tolerance=tolerance,
    )
