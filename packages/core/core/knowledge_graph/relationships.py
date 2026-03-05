# -*- coding: utf-8 -*-
"""
知识图谱关系定义
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class RelationshipType(Enum):
    """关系类型枚举"""
    CONTAINS = "CONTAINS"           # 包含：规范包含章节、条款
    DEPENDS_ON = "DEPENDS_ON"       # 依赖：工艺依赖材料
    APPLIES_TO = "APPLIES_TO"       # 适用于：规范适用于道路类型
    REQUIRES = "REQUIRES"           # 前置：工艺需要前置工艺
    HAS_STANDARD = "HAS_STANDARD"   # 拥有标准：项目拥有质量标准
    USES = "USES"                   # 使用：工艺使用材料
    REFERENCES = "REFERENCES"       # 引用：引用规范
    LINKED_TO = "LINKED_TO"        # 关联：与其他实体关联


# 关系类型常量（用于简化创建）
CONTAINS = RelationshipType.CONTAINS
DEPENDS_ON = RelationshipType.DEPENDS_ON
APPLIES_TO = RelationshipType.APPLIES_TO
REQUIRES = RelationshipType.REQUIRES
HAS_STANDARD = RelationshipType.HAS_STANDARD
USES = RelationshipType.USES
REFERENCES = RelationshipType.REFERENCES
LINKED_TO = RelationshipType.LINKED_TO


@dataclass
class Relationship:
    """关系类
    
    属性:
        id: 关系唯一ID
        source_id: 源实体ID
        target_id: 目标实体ID
        relationship_type: 关系类型
        properties: 关系属性
        weight: 关系权重（用于推理）
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relationship_type: RelationshipType = RelationshipType.LINKED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # 关系权重
    
    def __post_init__(self):
        if isinstance(self.relationship_type, str):
            try:
                self.relationship_type = RelationshipType(self.relationship_type)
            except ValueError:
                self.relationship_type = RelationshipType.LINKED_TO
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "properties": self.properties,
            "weight": self.weight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """从字典创建"""
        rel_type = data.get("relationship_type", "LINKED_TO")
        if isinstance(rel_type, str):
            try:
                rel_type = RelationshipType(rel_type)
            except ValueError:
                rel_type = RelationshipType.LINKED_TO
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            relationship_type=rel_type,
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
        )


# 便捷函数：创建关系
def create_relationship(source_id: str, target_id: str, 
                       rel_type: RelationshipType,
                       properties: Dict[str, Any] = None,
                       weight: float = 1.0) -> Relationship:
    """创建关系"""
    return Relationship(
        source_id=source_id,
        target_id=target_id,
        relationship_type=rel_type,
        properties=properties or {},
        weight=weight,
    )


def create_contains_relation(parent_id: str, child_id: str, 
                            weight: float = 1.0) -> Relationship:
    """创建包含关系"""
    return create_relationship(
        source_id=parent_id,
        target_id=child_id,
        rel_type=CONTAINS,
        weight=weight,
    )


def create_depends_on_relation(process_id: str, material_id: str,
                              weight: float = 1.0) -> Relationship:
    """创建依赖关系（工艺依赖材料）"""
    return create_relationship(
        source_id=process_id,
        target_id=material_id,
        rel_type=DEPENDS_ON,
        weight=weight,
    )


def create_applies_to_relation(standard_id: str, road_type: str,
                               weight: float = 1.0) -> Relationship:
    """创建适用于关系"""
    return create_relationship(
        source_id=standard_id,
        target_id=road_type,
        rel_type=APPLIES_TO,
        properties={"road_type": road_type},
        weight=weight,
    )


def create_requires_relation(process_id: str, prerequisite_id: str,
                             weight: float = 1.0) -> Relationship:
    """创建前置关系"""
    return create_relationship(
        source_id=process_id,
        target_id=prerequisite_id,
        rel_type=REQUIRES,
        weight=weight,
    )


def create_uses_relation(process_id: str, material_id: str,
                       weight: float = 1.0) -> Relationship:
    """创建使用关系"""
    return create_relationship(
        source_id=process_id,
        target_id=material_id,
        rel_type=USES,
        weight=weight,
    )


def create_references_relation(entity_id: str, standard_id: str,
                              weight: float = 1.0) -> Relationship:
    """创建引用关系"""
    return create_relationship(
        source_id=entity_id,
        target_id=standard_id,
        rel_type=REFERENCES,
        weight=weight,
    )
