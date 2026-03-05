# -*- coding: utf-8 -*-
"""
BIM 模块测试
"""

import pytest
import sys
sys.path.insert(0, '.')

from core.integrations.bim.models import (
    BIMProject,
    BIMBuilding,
    BIMStorey,
    BIMElement,
    BIMGeometry,
    BIMProperty,
    IFCVersion,
    ElementType,
    PropertyType,
    ImportProgress,
    ImportStatus,
    ImportError
)
from core.integrations.bim.converter import BIMConverter, NeuralSiteEntity


class TestBIMModels:
    """测试数据模型"""
    
    def test_bim_project(self):
        """测试项目模型"""
        project = BIMProject(
            name="Test Project",
            ifc_version=IFCVersion.IFC4
        )
        
        assert project.name == "Test Project"
        assert project.ifc_version == IFCVersion.IFC4
        assert project.total_elements == 0
    
    def test_bim_building(self):
        """测试建筑模型"""
        building = BIMBuilding(
            id="b1",
            global_id="b1-global",
            name="Test Building"
        )
        
        assert building.id == "b1"
        assert len(building.storeys) == 0
    
    def test_bim_storey(self):
        """测试楼层模型"""
        storey = BIMStorey(
            id="s1",
            global_id="s1-global",
            name="Level 1",
            elevation=3.0
        )
        
        assert storey.elevation == 3.0
        assert len(storey.element_ids) == 0
    
    def test_bim_element(self):
        """测试构件模型"""
        element = BIMElement(
            id="e1",
            global_id="e1-global",
            ifc_type="IfcBeam",
            element_type=ElementType.BEAM,
            name="Beam 1",
            position={"x": 0, "y": 3, "z": 0}
        )
        
        assert element.ifc_type == "IfcBeam"
        assert element.element_type == ElementType.BEAM
        assert element.position["y"] == 3
    
    def test_bim_geometry(self):
        """测试几何模型"""
        geometry = BIMGeometry(
            type="box",
            bounding_box={
                "min_x": 0, "min_y": 0, "min_z": 0,
                "max_x": 1, "max_y": 1, "max_z": 1
            }
        )
        
        assert geometry.type == "box"
        assert geometry.bounding_box["max_x"] == 1
    
    def test_bim_property(self):
        """测试属性模型"""
        prop = BIMProperty(
            name="Length",
            value=10.5,
            type=PropertyType.NUMBER,
            unit="m"
        )
        
        assert prop.value == 10.5
        assert prop.unit == "m"


class TestImportProgress:
    """测试导入进度"""
    
    def test_import_progress(self):
        """测试进度模型"""
        progress = ImportProgress(
            task_id="test-123",
            status=ImportStatus.PENDING,
            progress=0
        )
        
        assert progress.task_id == "test-123"
        assert progress.status == ImportStatus.PENDING
    
    def test_import_error(self):
        """测试错误模型"""
        error = ImportError(
            code="PARSE_ERROR",
            message="Failed to parse IFC",
            element_id="e1"
        )
        
        assert error.code == "PARSE_ERROR"
        assert error.element_id == "e1"


class TestBIMConverter:
    """测试数据转换器"""
    
    def test_converter_creates_entity(self):
        """测试转换器创建实体"""
        converter = BIMConverter()
        
        entity = NeuralSiteEntity(
            entity_type="beam",
            name="Test Beam",
            geometry={"type": "box"},
            properties={"material": "concrete"}
        )
        
        assert entity.entity_type == "beam"
        assert entity.geometry["type"] == "box"
    
    def test_convert_empty_project(self):
        """测试转换空项目"""
        project = BIMProject(
            name="Empty Project",
            ifc_version=IFCVersion.IFC4
        )
        
        converter = BIMConverter()
        result = converter.convert(project)
        
        assert result["project"]["name"] == "Empty Project"
        assert result["entities"] == []
        assert result["statistics"]["total_entities"] == 0
    
    def test_convert_element(self):
        """测试转换构件"""
        element = BIMElement(
            id="e1",
            global_id="e1-global",
            ifc_type="IfcBeam",
            element_type=ElementType.BEAM,
            name="Beam 1",
            position={"x": 5, "y": 3, "z": 0}
        )
        
        project = BIMProject(
            name="Test",
            ifc_version=IFCVersion.IFC4,
            elements={"e1": element},
            total_elements=1,
            element_type_counts={"beam": 1}
        )
        
        converter = BIMConverter()
        result = converter.convert(project)
        
        assert len(result["entities"]) > 0
        
        # 检查实体
        entity = result["entities"][0]
        assert entity["type"] == "beam"
        assert entity["name"] == "Beam 1"
    
    def test_element_type_mapping(self):
        """测试元素类型映射"""
        converter = BIMConverter()
        
        # 验证映射
        assert converter.ELEMENT_TYPE_MAP[ElementType.BEAM] == "beam"
        assert converter.ELEMENT_TYPE_MAP[ElementType.COLUMN] == "column"
        assert converter.ELEMENT_TYPE_MAP[ElementType.WALL] == "wall"


class TestIFCParser:
    """测试 IFC 解析器"""
    
    def test_parser_creation(self):
        """测试解析器创建"""
        from core.integrations.bim import IFCParser
        
        parser = IFCParser()
        
        # 验证类型映射存在
        assert "IfcBeam" in parser.IFC_TYPE_MAP
        assert "IfcWall" in parser.IFC_TYPE_MAP
        assert "IfcColumn" in parser.IFC_TYPE_MAP
    
    def test_type_mapping(self):
        """测试 IFC 类型映射"""
        from core.integrations.bim import IFCParser
        
        parser = IFCParser()
        
        assert parser.IFC_TYPE_MAP["IfcBeam"] == ElementType.BEAM
        assert parser.IFC_TYPE_MAP["IfcColumn"] == ElementType.COLUMN
        assert parser.IFC_TYPE_MAP["IfcWall"] == ElementType.WALL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
