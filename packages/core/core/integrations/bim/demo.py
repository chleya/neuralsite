# -*- coding: utf-8 -*-
"""
BIM 导入示例

展示如何使用 BIM 模块
"""

import sys
sys.path.insert(0, '.')

from core.integrations.bim import IFCParser, BIMConverter, BIMProject
from core.integrations.bim.models import IFCVersion, ElementType


def demo_parse():
    """演示解析 IFC 文件"""
    parser = IFCParser()
    
    # 如果有 IFC 文件
    # project = parser.parse("path/to/file.ifc")
    
    # 打印支持的类型
    print("=== IFC 类型映射 ===")
    for ifc_type, element_type in parser.IFC_TYPE_MAP.items():
        print(f"  {ifc_type} -> {element_type.value}")
    
    return parser


def demo_convert():
    """演示数据转换"""
    # 创建示例 BIM 项目
    from core.integrations.bim.models import (
        BIMProject, BIMBuilding, BIMStorey, BIMElement, 
        BIMGeometry, BIMProperty, PropertyType
    )
    
    project = BIMProject(
        name="Demo Project",
        ifc_version=IFCVersion.IFC4
    )
    
    # 添加建筑
    building = BIMBuilding(
        id="b1",
        global_id="b1-global",
        name="Demo Building"
    )
    
    # 添加楼层
    storey = BIMStorey(
        id="s1",
        global_id="s1-global",
        name="Level 1",
        elevation=0.0
    )
    building.storeys.append(storey)
    project.buildings.append(building)
    
    # 添加构件
    element = BIMElement(
        id="e1",
        global_id="e1-global",
        ifc_type="IfcBeam",
        element_type=ElementType.BEAM,
        name="Beam 1",
        position={"x": 0, "y": 3, "z": 0},
        geometry=BIMGeometry(
            type="box",
            bounding_box={
                "min_x": 0, "min_y": 2.5, "min_z": 0,
                "max_x": 6, "max_y": 3.5, "max_z": 0.3
            }
        ),
        properties=[
            BIMProperty(name="Length", value=6.0, type=PropertyType.NUMBER, unit="m"),
            BIMProperty(name="Section", value="300x600", type=PropertyType.STRING)
        ],
        material="Concrete C30"
    )
    
    project.elements["e1"] = element
    project.total_elements = 1
    project.element_type_counts = {"beam": 1}
    
    # 转换
    converter = BIMConverter()
    result = converter.convert(project)
    
    print("=== 转换结果 ===")
    print(f"项目: {result['project']['name']}")
    print(f"实体数: {result['statistics']['total_entities']}")
    print(f"类型统计: {result['statistics']['by_type']}")
    
    return result


def demo_viewer():
    """演示 3D 查看器"""
    from core.integrations.bim.visualization import create_bim_viewer
    from core.integrations.bim.models import BIMProject, IFCVersion
    
    # 创建项目
    project = BIMProject(
        name="Demo Building",
        ifc_version=IFCVersion.IFC4
    )
    
    # 获取查看器数据
    viewer_data = create_bim_viewer(project, "demo")
    
    print("=== 查看器数据 ===")
    print(f"组件 ID: {viewer_data['component']['id(f"HTML 长度: {len']}")
    print(viewer_data['html'])} 字符")
    
    return viewer_data


if __name__ == "__main__":
    print("=== BIM 模块演示 ===\n")
    
    # 1. 解析器
    print("1. IFC 解析器")
    demo_parse()
    print()
    
    # 2. 数据转换
    print("2. 数据转换")
    demo_convert()
    print()
    
    # 3. 3D 查看器
    print("3. 3D 查看器")
    demo_viewer()
    print()
    
    print("=== 演示完成 ===")
