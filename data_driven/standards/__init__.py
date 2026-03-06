# -*- coding: utf-8 -*-
"""
数据标准模块

包含：
- 格式标准
- 业务校验规则
- 语义映射
"""

__version__ = "1.0.0"

from .formats import StationFormat, CoordinateFormat, TimeFormat, FileFormat
from .business import BusinessValidator
from .semantic import SemanticMapper

__all__ = [
    # 格式标准
    "StationFormat",
    "CoordinateFormat", 
    "TimeFormat",
    "FileFormat",
    # 业务校验
    "BusinessValidator",
    # 语义映射
    "SemanticMapper",
]
