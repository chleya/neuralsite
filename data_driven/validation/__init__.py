# -*- coding: utf-8 -*-
"""
数据校验引擎模块
"""

__version__ = "1.0.0"

from .engine import ValidationEngine, ValidationResult, ValidationRule, RuleResult, Severity, RuleType
from .rules import PREDEFINED_RULES, get_predefined_rules, RULE_MAP

__all__ = [
    "ValidationEngine",
    "ValidationResult",
    "ValidationRule",
    "RuleResult",
    "Severity", 
    "RuleType",
    "PREDEFINED_RULES",
    "get_predefined_rules",
    "RULE_MAP",
]

# API router
from .api import router as api_router
