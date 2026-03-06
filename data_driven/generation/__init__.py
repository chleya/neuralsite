# -*- coding: utf-8 -*-
"""
功能生成模块

你提需求，我来生成代码
"""

__version__ = "1.0.0"

from .generator import (
    RequirementParser, 
    CodeGenerator, 
    ParsedRequirement, 
    RequirementType
)

__all__ = [
    "RequirementParser", 
    "CodeGenerator", 
    "ParsedRequirement", 
    "RequirementType"
]
