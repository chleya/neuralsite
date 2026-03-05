# -*- coding: utf-8 -*-
"""
BIM 数据转换器

将 IFC 数据转换为 NeuralSite 实体格式
"""

from typing import Dict, List, Optional, Any
import logging
from uuid import uuid4

from .models import (
    BIMProject,
    BIMElement,
    BIMBuilding,
    BIMStorey,
    BIMGeometry,
    ElementType
)

logger = logging.getLogger(__name__)


class NeuralSiteEntityType(str):
    """NeuralSite 实体类型常量"""
    STRUCTURE = "structure"
    BEAM = "beam"
    COLUMN = "column"
    WALL = "wall"
    SLAB = "slab"
    FOUNDATION = "foundation"
    SPACE = "space"
    POINT = "point"
    LINE = "line"
    SURFACE = "surface"
    MESH = "mesh"


class NeuralSiteEntity:
    """NeuralSite 实体"""
    
    def __init__(
        self,
        entity_type: str,
        name: str,
        geometry: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, float]] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid4())
        self.entity_type = entity_type
        self.name = name
        self.geometry = geometry or {}
        self.properties = properties or {}
        self.position = position or {}
        self.parent_id = parent_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.entity_type,
            "name": self.name,
            "geometry": self.geometry,
            "properties": self.properties,
            "position": self.position,
            "parent_id": self.parent_id,
            "metadata": self.metadata
        }


class BIMConverter:
    """BIM 数据转换器
    
    将 BIMProject 转换为 NeuralSite 格式
    """
    
    # BIM 元素类型到 NeuralSite 实体类型映射
    ELEMENT_TYPE_MAP = {
        ElementType.BEAM: NeuralSiteEntityType.BEAM,
        ElementType.COLUMN: NeuralSiteEntityType.COLUMN,
        ElementType.WALL: NeuralSiteEntityType.WALL,
        ElementType.SLAB: NeuralSiteEntityType.SLAB,
        ElementType.FOUNDATION: NeuralSiteEntityType.FOUNDATION,
        ElementType.SPACE: NeuralSiteEntityType.SPACE,
        ElementType.DOOR: NeuralSiteEntityType.STRUCTURE,
        ElementType.WINDOW: NeuralSiteEntityType.STRUCTURE,
        ElementType.STAIRS: NeuralSiteEntityType.STRUCTURE,
        ElementType.RAILING: NeuralSiteEntityType.STRUCTURE,
        ElementType.DUCT: NeuralSiteEntityType.STRUCTURE,
        ElementType.PIPE: NeuralSiteEntityType.STRUCTURE,
        ElementType.EQUIPMENT: NeuralSiteEntityType.STRUCTURE,
    }
    
    def __init__(self):
        self.entities: List[NeuralSiteEntity] = []
        self.entity_map: Dict[str, NeuralSiteEntity] = {}
    
    def convert(self, bim_project: BIMProject) -> Dict[str, Any]:
        """转换整个 BIM 项目"""
        self.entities = []
        self.entity_map = {}
        
        # 转换所有建筑
        for building in bim_project.buildings:
            self._convert_building(building)
        
        # 转换所有独立元素
        for element in bim_project.elements.values():
            if element.id not in self.entity_map:
                self._convert_element(element)
        
        return self._build_output(bim_project)
    
    def _convert_building(self, building: BIMBuilding):
        """转换建筑"""
        # 建筑作为一个组实体
        building_entity = NeuralSiteEntity(
            entity_type=NeuralSiteEntityType.STRUCTURE,
            name=building.name,
            properties={
                "bim_type": "building",
                "bim_id": building.id,
                "global_id": building.global_id,
                "storey_count": len(building.storeys)
            },
            metadata={
                "bim_source": "ifc",
                "element_count": len(building.element_ids)
            }
        )
        
        self.entities.append(building_entity)
        self.entity_map[building.id] = building_entity
        
        # 转换楼层
        for storey in building.storeys:
            self._convert_storey(storey, building_entity.id)
    
    def _convert_storey(self, storey: BIMStorey, building_id: str):
        """转换楼层"""
        storey_entity = NeuralSiteEntity(
            entity_type=NeuralSiteEntityType.SPACE,
            name=storey.name,
            position={"z": storey.elevation},
            parent_id=self.entity_map.get(building_id).id if building_id in self.entity_map else None,
            properties={
                "bim_type": "storey",
                "bim_id": storey.id,
                "elevation": storey.elevation,
                "element_count": len(storey.element_ids)
            }
        )
        
        self.entities.append(storey_entity)
        self.entity_map[storey.id] = storey_entity
    
    def _convert_element(self, element: BIMElement):
        """转换构件"""
        # 获取 NeuralSite 实体类型
        entity_type = self.ELEMENT_TYPE_MAP.get(
            element.element_type,
            NeuralSiteEntityType.STRUCTURE
        )
        
        # 转换几何数据
        geometry = self._convert_geometry(element.geometry)
        
        # 构建属性
        properties = {
            "bim_type": element.ifc_type,
            "bim_id": element.id,
            "element_category": element.element_type.value
        }
        
        # 添加 IFC 属性
        for prop in element.properties:
            properties[f"ifc_{prop.name.lower()}"] = prop.value
        
        # 添加材质
        if element.material:
            properties["material"] = element.material
        
        # 获取父实体 ID
        parent_id = None
        if element.storey_id and element.storey_id in self.entity_map:
            parent_id = self.entity_map[element.storey_id].id
        elif element.building_id and element.building_id in self.entity_map:
            parent_id = self.entity_map[element.building_id].id
        
        # 创建实体
        entity = NeuralSiteEntity(
            entity_type=entity_type,
            name=element.name or f"{element.element_type.value}_{element.id[:8]}",
            geometry=geometry,
            properties=properties,
            position=element.position or {},
            parent_id=parent_id,
            metadata={
                "bim_source": "ifc",
                "global_id": element.global_id,
                "description": element.description
            }
        )
        
        self.entities.append(entity)
        self.entity_map[element.id] = entity
    
    def _convert_geometry(self, geometry: Optional[BIMGeometry]) -> Dict[str, Any]:
        """转换几何数据"""
        if not geometry:
            return {}
        
        result = {
            "type": geometry.type
        }
        
        if geometry.bounding_box:
            result["boundingBox"] = {
                "min": [
                    geometry.bounding_box.get("min_x", 0),
                    geometry.bounding_box.get("min_y", 0),
                    geometry.bounding_box.get("min_z", 0)
                ],
                "max": [
                    geometry.bounding_box.get("max_x", 0),
                    geometry.bounding_box.get("max_y", 0),
                    geometry.bounding_box.get("max_z", 0)
                ]
            }
        
        if geometry.extrusion:
            result["extrusion"] = {
                "depth": geometry.extrusion.get("depth", 0),
                "direction": geometry.extrusion.get("extrusion_direction")
            }
        
        if geometry.triangulated:
            triangulated = geometry.triangulated
            result["mesh"] = {
                "vertexCount": triangulated.get("vertex_count", 0),
                "faceCount": triangulated.get("face_count", 0),
                # 简化的坐标数据用于预览
                "hasMesh": triangulated.get("vertex_count", 0) > 0
            }
        
        return result
    
    def _build_output(self, bim_project: BIMProject) -> Dict[str, Any]:
        """构建输出"""
        return {
            "project": {
                "id": bim_project.id,
                "name": bim_project.name,
                "ifc_version": bim_project.ifc_version.value,
                "source_file": bim_project.source_file,
                "created_at": bim_project.created_at.isoformat()
            },
            "entities": [e.to_dict() for e in self.entities],
            "statistics": {
                "total_entities": len(self.entities),
                "by_type": self._count_by_type(),
                "bim_statistics": {
                    "total_elements": bim_project.total_elements,
                    "element_type_counts": bim_project.element_type_counts
                }
            }
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for entity in self.entities:
            counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
        return counts
    
    def get_entities(self) -> List[NeuralSiteEntity]:
        """获取转换后的实体列表"""
        return self.entities
    
    def get_entity_map(self) -> Dict[str, NeuralSiteEntity]:
        """获取 ID 到实体的映射"""
        return self.entity_map


def convert_bim_to_neuralsite(bim_project: BIMProject) -> Dict[str, Any]:
    """便捷函数：转换 BIM 项目到 NeuralSite 格式"""
    converter = BIMConverter()
    return converter.convert(bim_project)
