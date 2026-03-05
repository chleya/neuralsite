# -*- coding: utf-8 -*-
"""
BIM 数据导入模块

支持 IFC2x3/IFC4 格式的 BIM 数据导入
"""

from .ifc_parser import IFCParser, IFCVersion
from .converter import BIMConverter, NeuralSiteEntity
from .models import (
    BIMProject,
    BIMBuilding,
    BIMStorey,
    BIMElement,
    BIMProperty,
    BIMGeometry,
    ImportProgress,
    ImportError,
    ElementType,
    PropertyType,
    IFCVersion as ModelIFCVersion
)

__all__ = [
    "IFCParser",
    "IFCVersion",
    "BIMConverter",
    "NeuralSiteEntity",
    "BIMProject",
    "BIMBuilding",
    "BIMStorey",
    "BIMElement",
    "BIMProperty",
    "BIMGeometry",
    "ImportProgress",
    "ImportError",
    "ElementType",
    "PropertyType"
]
