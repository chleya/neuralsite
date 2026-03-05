# -*- coding: utf-8 -*-
"""
IFC 解析器

支持 IFC2x3 / IFC4 格式解析
"""

import io
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Iterator
from pathlib import Path
import logging

from .models import (
    BIMProject,
    BIMBuilding,
    BIMStorey,
    BIMElement,
    BIMProperty,
    BIMGeometry,
    IFCVersion,
    ElementType,
    PropertyType
)

logger = logging.getLogger(__name__)


class IFCParserBase(ABC):
    """IFC 解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> BIMProject:
        """解析 IFC 文件"""
        pass
    
    @abstractmethod
    def parse_stream(self, content: bytes) -> BIMProject:
        """从字节流解析"""
        pass
    
    @abstractmethod
    def get_version(self, file_path: str) -> IFCVersion:
        """获取 IFC 版本"""
        pass


class IFCParser(IFCParserBase):
    """IFC 解析器实现
    
    使用 ifcopenshell 库解析 IFC 文件
    """
    
    # IFC 类型到 NeuralSite 元素类型映射
    IFC_TYPE_MAP = {
        # 结构
        "IfcBeam": ElementType.BEAM,
        "IfcBeamStandardCase": ElementType.BEAM,
        "IfcColumn": ElementType.COLUMN,
        "IfcColumnStandardCase": ElementType.COLUMN,
        "IfcWall": ElementType.WALL,
        "IfcWallStandardCase": ElementType.WALL,
        "IfcWallElementedCase": ElementType.WALL,
        "IfcSlab": ElementType.SLAB,
        "IfcFloorSlab": ElementType.SLAB,
        "IfcRoofSlab": ElementType.SLAB,
        "IfcFooting": ElementType.FOUNDATION,
        "IfcStripFooting": ElementType.FOUNDATION,
        "IfcPadFooting": ElementType.FOUNDATION,
        "IfcPile": ElementType.FOUNDATION,
        
        # 建筑
        "IfcDoor": ElementType.DOOR,
        "IfcDoorStandardCase": ElementType.DOOR,
        "IfcWindow": ElementType.WINDOW,
        "IfcWindowStandardCase": ElementType.WINDOW,
        "IfcStairs": ElementType.STAIRS,
        "IfcStairFlight": ElementType.STAIRS,
        "IfcRailing": ElementType.RAILING,
        
        # 机电
        "IfcDuct": ElementType.DUCT,
        "IfcDuctSegment": ElementType.DUCT,
        "IfcDuctFitting": ElementType.DUCT,
        "IfcPipe": ElementType.PIPE,
        "IfcPipeSegment": ElementType.PIPE,
        "IfcPipeFitting": ElementType.PIPE,
        "IfcDistributionElement": ElementType.EQUIPMENT,
        "IfcDistributionControlElement": ElementType.EQUIPMENT,
        "IfcBuildingElementProxy": ElementType.EQUIPMENT,
        
        # 空间
        "IfcSpace": ElementType.SPACE,
        "IfcSite": ElementType.SITE,
        "IfcBuilding": ElementType.BUILDING,
        "IfcBuildingStorey": ElementType.STOREY,
    }
    
    def __init__(self):
        self._ifcopenshell = None
        self._try_import_ifcopenshell()
    
    def _try_import_ifcopenshell(self):
        """尝试导入 ifcopenshell"""
        try:
            import ifcopenshell
            self._ifcopenshell = ifcopenshell
            logger.info("ifcopenshell loaded successfully")
        except ImportError:
            logger.warning(
                "ifcopenshell not installed. "
                "Using fallback parser. Install with: pip install ifcopenshell"
            )
            self._ifcopenshell = None
    
    def get_version(self, file_path: str) -> IFCVersion:
        """获取 IFC 版本"""
        try:
            if self._ifcopenshell:
                model = self._ifcopenshell.open(file_path)
                schema = model.schema
                if "IFC4X1" in schema or "IFC4X2" in schema:
                    return IFCVersion.IFC4X1
                elif "IFC4" in schema:
                    return IFCVersion.IFC4
                else:
                    return IFCVersion.IFC2X3
            else:
                # 文本解析回退
                return self._detect_version_from_file(file_path)
        except Exception as e:
            logger.warning(f"Failed to detect IFC version: {e}")
            return IFCVersion.IFC2X3
    
    def _detect_version_from_file(self, file_path: str) -> IFCVersion:
        """从文件内容检测版本"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            header = f.read(5000)
            
        if "IFC4X1" in header or "IFC4X2" in header:
            return IFCVersion.IFC4X1
        elif "IFC4" in header:
            return IFCVersion.IFC4
        else:
            return IFCVersion.IFC2X3
    
    def parse(self, file_path: str) -> BIMProject:
        """解析 IFC 文件"""
        version = self.get_version(file_path)
        
        if self._ifcopenshell:
            return self._parse_with_ifcopenshell(file_path, version)
        else:
            return self._parse_fallback(file_path, version)
    
    def parse_stream(self, content: bytes) -> BIMProject:
        """从字节流解析"""
        version = IFCVersion.IFC4  # 默认
        
        # 写入临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            return self.parse(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def _parse_with_ifcopenshell(self, file_path: str, version: IFCVersion) -> BIMProject:
        """使用 ifcopenshell 解析"""
        model = self._ifcopenshell.open(file_path)
        
        project = BIMProject(
            name=self._get_project_name(model),
            ifc_version=version,
            source_file=file_path
        )
        
        # 解析建筑
        buildings = model.by_type("IfcBuilding")
        for building in buildings:
            bim_building = self._parse_building(building, model)
            project.buildings.append(bim_building)
        
        # 解析所有元素
        elements = model.by_type("IfcBuildingElement")
        for element in elements:
            bim_element = self._parse_element(element, model)
            if bim_element:
                project.elements[bim_element.id] = bim_element
        
        # 统计
        project.total_elements = len(project.elements)
        project.element_type_counts = self._count_element_types(project.elements)
        
        return project
    
    def _get_project_name(self, model) -> str:
        """获取项目名称"""
        project = model.by_type("IfcProject")
        if project:
            return project[0].Name or "Untitled Project"
        return "Untitled Project"
    
    def _parse_building(self, building, model) -> BIMBuilding:
        """解析建筑"""
        building_id = str(building.GlobalId)
        
        # 解析楼层
        storeys = []
        if hasattr(building, "BuildingStores") or hasattr(building, "IsDecomposedBy"):
            # 获取楼层
            rels = building.IsDecomposedBy or []
            for rel in rels:
                for storey in rel.RelatedObjects:
                    if storey.is_a("IfcBuildingStorey"):
                        bim_storey = self._parse_storey(storey, model)
                        storeys.append(bim_storey)
        
        return BIMBuilding(
            id=building_id,
            global_id=building_id,
            name=building.Name or "Building",
            storeys=storeys,
            bounding_box=self._calculate_building_bbox(building, model)
        )
    
    def _parse_storey(self, storey, model) -> BIMStorey:
        """解析楼层"""
        storey_id = str(storey.GlobalId)
        
        # 获取该楼层的所有元素
        elements = model.by_type("IfcBuildingElement")
        storey_elements = [
            e for e in elements 
            if hasattr(e, "ContainedInStructure") 
            and e.ContainedInStructure
            and e.ContainedInStructure[0].RelatingStructure.GlobalId == storey.GlobalId
        ]
        
        return BIMStorey(
            id=storey_id,
            global_id=storey_id,
            name=storey.Name or "Storey",
            elevation=storey.Elevation or 0.0,
            element_ids=[str(e.GlobalId) for e in storey_elements],
            bounding_box=self._calculate_storey_bbox(storey_elements)
        )
    
    def _parse_element(self, element, model) -> Optional[BIMElement]:
        """解析单个构件"""
        element_id = str(element.GlobalId)
        
        ifc_type = element.is_a()
        element_type = self.IFC_TYPE_MAP.get(ifc_type, ElementType.UNKNOWN)
        
        # 解析几何
        geometry = self._parse_geometry(element, model)
        
        # 解析属性
        properties = self._parse_properties(element, model)
        
        # 解析材质
        material = self._parse_material(element, model)
        
        # 获取位置
        position = self._parse_position(element)
        
        # 获取所在楼层
        storey_id = None
        if hasattr(element, "ContainedInStructure") and element.ContainedInStructure:
            structure = element.ContainedInStructure[0].RelatingStructure
            if structure.is_a("IfcBuildingStorey"):
                storey_id = str(structure.GlobalId)
        
        return BIMElement(
            id=element_id,
            global_id=element_id,
            ifc_type=ifc_type,
            element_type=element_type,
            geometry=geometry,
            position=position,
            properties=properties,
            name=element.Name,
            description=element.Description,
            material=material,
            storey_id=storey_id
        )
    
    def _parse_geometry(self, element, model) -> Optional[BIMGeometry]:
        """解析几何数据"""
        try:
            # 获取几何表示
            if not hasattr(element, "Representation"):
                return None
            
            representations = element.Representation
            if not representations:
                return None
            
            # 获取主表示
            for rep in representations.Representations:
                if rep.RepresentationIdentifier == "Body":
                    # 解析三角网格
                    if rep.is_a("IfcShapeRepresentation"):
                        items = rep.Items
                        for item in items:
                            if item.is_a("IfcTriangulatedFaceSet"):
                                return BIMGeometry(
                                    type="triangulated",
                                    triangulated=self._parse_triangulated(item),
                                    bounding_box=self._calculate_bbox(item)
                                )
                            elif item.is_a("IfcExtrudedAreaSolid"):
                                return BIMGeometry(
                                    type="extruded",
                                    extrusion=self._parse_extrusion(item),
                                    bounding_box=self._calculate_bbox(item)
                                )
            
            # 如果没有 Body 表示，使用边界盒
            return BIMGeometry(
                type="box",
                bounding_box=self._calculate_element_bbox(element)
            )
        except Exception as e:
            logger.warning(f"Failed to parse geometry for {element.GlobalId}: {e}")
            return None
    
    def _parse_triangulated(self, tfs) -> Dict[str, Any]:
        """解析三角网格"""
        coords = list(tfs.Coordinates.CoordList) if hasattr(tfs, "Coordinates") else []
        indices = []
        if hasattr(tfs, "FaceIndex"):
            indices = list(tfs.FaceIndex)
        
        return {
            "vertex_count": len(coords),
            "face_count": len(indices),
            # 简化的坐标数据
            "coordinates": coords[:1000] if coords else []  # 限制大小
        }
    
    def _parse_extrusion(self, extrusion) -> Dict[str, Any]:
        """解析拉伸体"""
        return {
            "depth": extrusion.Depth if hasattr(extrusion, "Depth") else 0,
            "extrusion_direction": self._parse_direction(extrusion.ExtrusionDirection) if hasattr(extrusion, "ExtrusionDirection") else None,
            "swept_area": str(extrusion.SweptArea) if hasattr(extrusion, "SweptArea") else None
        }
    
    def _parse_direction(self, direction) -> Optional[List[float]]:
        """解析方向向量"""
        if hasattr(direction, "DirectionRatios"):
            return list(direction.DirectionRatios)
        return None
    
    def _calculate_bbox(self, item) -> Dict[str, float]:
        """计算边界盒"""
        try:
            if hasattr(item, "BoundingBox"):
                bb = item.BoundingBox
                return {
                    "min_x": bb.BoundingBoxMin[0],
                    "min_y": bb.BoundingBoxMin[1],
                    "min_z": bb.BoundingBoxMin[2],
                    "max_x": bb.BoundingBoxMax[0],
                    "max_y": bb.BoundingBoxMax[1],
                    "max_z": bb.BoundingBoxMax[2]
                }
        except:
            pass
        return {}
    
    def _calculate_element_bbox(self, element) -> Dict[str, float]:
        """计算构件边界盒"""
        return {}
    
    def _calculate_storey_bbox(self, elements) -> Dict[str, float]:
        """计算楼层边界盒"""
        return {}
    
    def _calculate_building_bbox(self, building, model) -> Dict[str, float]:
        """计算建筑边界盒"""
        return {}
    
    def _parse_properties(self, element, model) -> List[BIMProperty]:
        """解析属性"""
        properties = []
        
        try:
            # 获取直接属性
            for attr_name in ["Name", "Description", "ObjectType", "Tag"]:
                if hasattr(element, attr_name):
                    value = getattr(element, attr_name)
                    if value:
                        properties.append(BIMProperty(
                            name=attr_name,
                            value=str(value),
                            type=PropertyType.STRING
                        ))
            
            # 获取 QuantitySet
            if hasattr(element, "Quantities"):
                for quantity in element.Quantities or []:
                    if hasattr(quantity, "Quantities"):
                        for q in quantity.Quantities:
                            if hasattr(q, "LengthValue"):
                                properties.append(BIMProperty(
                                    name=q.Name or "Length",
                                    value=q.LengthValue,
                                    type=PropertyType.NUMBER,
                                    unit="m"
                                ))
                            elif hasattr(q, "AreaValue"):
                                properties.append(BIMProperty(
                                    name=q.Name or "Area",
                                    value=q.AreaValue,
                                    type=PropertyType.NUMBER,
                                    unit="m²"
                                ))
                            elif hasattr(q, "VolumeValue"):
                                properties.append(BIMProperty(
                                    name=q.Name or "Volume",
                                    value=q.VolumeValue,
                                    type=PropertyType.NUMBER,
                                    unit="m³"
                                ))
            
            # 获取自定义属性
            if hasattr(element, "IsDefinedBy"):
                for rel in element.IsDefinedBy or []:
                    if rel.is_a("IfcPropertySet"):
                        for prop in rel.HasProperties or []:
                            prop_data = self._parse_property(prop)
                            if prop_data:
                                properties.append(prop_data)
                                
        except Exception as e:
            logger.warning(f"Failed to parse properties for {element.GlobalId}: {e}")
        
        return properties
    
    def _parse_property(self, prop) -> Optional[BIMProperty]:
        """解析单个属性"""
        try:
            if prop.is_a("IfcPropertySingleValue"):
                value = prop.NominalValue
                if value:
                    # 判断类型
                    if value.is_a("IfcInteger"):
                        return BIMProperty(
                            name=prop.Name,
                            value=int(value),
                            type=PropertyType.NUMBER
                        )
                    elif value.is_a("IfcReal"):
                        return BIMProperty(
                            name=prop.Name,
                            value=float(value),
                            type=PropertyType.NUMBER
                        )
                    elif value.is_a("IfcBoolean"):
                        return BIMProperty(
                            name=prop.Name,
                            value=bool(value),
                            type=PropertyType.BOOLEAN
                        )
                    else:
                        return BIMProperty(
                            name=prop.Name,
                            value=str(value),
                            type=PropertyType.STRING
                        )
        except:
            pass
        return None
    
    def _parse_material(self, element, model) -> Optional[str]:
        """解析材质"""
        try:
            if hasattr(element, "HasAssociations"):
                for assoc in element.HasAssociations or []:
                    if assoc.is_a("IfcRelAssociatesMaterial"):
                        material = assoc.RelatingMaterial
                        if material:
                            if material.is_a("IfcMaterial"):
                                return material.Name
                            elif material.is_a("IfcMaterialLayerSet"):
                                return material.LayerSetName
        except:
            pass
        return None
    
    def _parse_position(self, element) -> Optional[Dict[str, float]]:
        """解析位置"""
        try:
            if hasattr(element, "ObjectPlacement"):
                placement = element.ObjectPlacement
                if placement:
                    if placement.is_a("IfcLocalPlacement"):
                        location = placement.PlacementLocation
                        if location:
                            return {
                                "x": location[0],
                                "y": location[1],
                                "z": location[2]
                            }
        except:
            pass
        return None
    
    def _count_element_types(self, elements: Dict[str, BIMElement]) -> Dict[str, int]:
        """统计构件类型"""
        counts = {}
        for element in elements.values():
            type_name = element.element_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def _parse_fallback(self, file_path: str, version: IFCVersion) -> BIMProject:
        """回退解析器 - 简单的文本解析"""
        project = BIMProject(
            name=self._extract_project_name(file_path),
            ifc_version=version,
            source_file=file_path
        )
        
        # 简单计数
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 统计各类元素
            type_counts = {}
            for ifc_type in self.IFC_TYPE_MAP.keys():
                count = content.count(ifc_type)
                if count > 0:
                    element_type = self.IFC_TYPE_MAP[ifc_type]
                    type_counts[element_type.value] = type_counts.get(element_type.value, 0) + count
                    
            project.element_type_counts = type_counts
            project.total_elements = sum(type_counts.values())
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
        
        return project
    
    def _extract_project_name(self, file_path: str) -> str:
        """提取项目名称"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "IFCPROJECT" in line.upper():
                        # 尝试提取名称
                        if "NAME" in line.upper():
                            # 简化处理
                            return Path(file_path).stem
                    if line.strip().startswith("FILE_DESCRIPTION"):
                        break
        except:
            pass
        return Path(file_path).stem


def create_parser() -> IFCParser:
    """创建 IFC 解析器"""
    return IFCParser()
