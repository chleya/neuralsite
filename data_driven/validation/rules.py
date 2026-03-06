# -*- coding: utf-8 -*-
"""
预定义校验规则
"""

from typing import List
from .engine import ValidationRule, RuleType, Severity

# 预定义规则列表
PREDEFINED_RULES: List[ValidationRule] = [
    # ==================== 路面结构层 ====================
    ValidationRule(
        rule_id="range_pavement_thickness",
        rule_name="路面结构层厚度范围校验",
        data_type="pavement_layer",
        field_name="thickness",
        rule_type=RuleType.RANGE,
        parameters={"min": 0.15, "max": 0.50},
        severity=Severity.WARNING,
        description="路面结构层厚度应在15-50cm之间"
    ),
    ValidationRule(
        rule_id="range_pavement_width",
        rule_name="路面宽度范围校验",
        data_type="pavement_layer",
        field_name="width",
        rule_type=RuleType.RANGE,
        parameters={"min": 3.0, "max": 20.0},
        severity=Severity.ERROR,
        description="路面宽度应在3-20米之间"
    ),
    
    # ==================== 土石方工程 ====================
    ValidationRule(
        rule_id="range_excavation_depth",
        rule_name="挖方深度范围校验",
        data_type="earthwork",
        field_name="depth",
        rule_type=RuleType.RANGE,
        parameters={"min": 0, "max": 50},
        severity=Severity.ERROR,
        description="挖方深度不应超过50米"
    ),
    ValidationRule(
        rule_id="range_fill_height",
        rule_name="填方高度范围校验",
        data_type="earthwork",
        field_name="fill_height",
        rule_type=RuleType.RANGE,
        parameters={"min": 0, "max": 30},
        severity=Severity.ERROR,
        description="填方高度不应超过30米"
    ),
    ValidationRule(
        rule_id="range_slope_ratio",
        rule_name="边坡坡度范围校验",
        data_type="earthwork",
        field_name="slope_ratio",
        rule_type=RuleType.RANGE,
        parameters={"min": 0.5, "max": 3.0},
        severity=Severity.WARNING,
        description="边坡坡度应在1:0.5至1:3之间"
    ),
    
    # ==================== 桥梁结构 ====================
    ValidationRule(
        rule_id="range_bridge_span",
        rule_name="桥梁跨径范围校验",
        data_type="bridge",
        field_name="span",
        rule_type=RuleType.RANGE,
        parameters={"min": 5, "max": 200},
        severity=Severity.ERROR,
        description="桥梁跨径应在5-200米之间"
    ),
    ValidationRule(
        rule_id="range_bridge_width",
        rule_name="桥梁宽度范围校验",
        data_type="bridge",
        field_name="width",
        rule_type=RuleType.RANGE,
        parameters={"min": 4.5, "max": 30},
        severity=Severity.ERROR,
        description="桥梁宽度应在4.5-30米之间"
    ),
    ValidationRule(
        rule_id="range_pier_height",
        rule_name="墩台高度范围校验",
        data_type="bridge",
        field_name="pier_height",
        rule_type=RuleType.RANGE,
        parameters={"min": 0, "max": 100},
        severity=Severity.WARNING,
        description="墩台高度不应超过100米"
    ),
    
    # ==================== 隧道工程 ====================
    ValidationRule(
        rule_id="range_tunnel_length",
        rule_name="隧道长度范围校验",
        data_type="tunnel",
        field_name="length",
        rule_type=RuleType.RANGE,
        parameters={"min": 0, "max": 20000},
        severity=Severity.WARNING,
        description="隧道长度不应超过20公里"
    ),
    ValidationRule(
        rule_id="range_tunnel_diameter",
        rule_name="隧道直径范围校验",
        data_type="tunnel",
        field_name="diameter",
        rule_type=RuleType.RANGE,
        parameters={"min": 3, "max": 20},
        severity=Severity.ERROR,
        description="隧道直径应在3-20米之间"
    ),
    
    # ==================== 排水工程 ====================
    ValidationRule(
        rule_id="range_drainage_diameter",
        rule_name="排水管直径范围校验",
        data_type="drainage",
        field_name="diameter",
        rule_type=RuleType.RANGE,
        parameters={"min": 0.3, "max": 5.0},
        severity=Severity.ERROR,
        description="排水管直径应在30cm-5m之间"
    ),
    ValidationRule(
        rule_id="range_drainage_depth",
        rule_name="排水管埋深范围校验",
        data_type="drainage",
        field_name="depth",
        rule_type=RuleType.RANGE,
        parameters={"min": 0.5, "max": 10},
        severity=Severity.WARNING,
        description="排水管埋深应在0.5-10米之间"
    ),
    
    # ==================== 涵洞工程 ====================
    ValidationRule(
        rule_id="range_culvert_span",
        rule_name="涵洞跨径范围校验",
        data_type="culvert",
        field_name="span",
        rule_type=RuleType.RANGE,
        parameters={"min": 0.5, "max": 10},
        severity=Severity.ERROR,
        description="涵洞跨径应在0.5-10米之间"
    ),
    
    # ==================== 防护工程 ====================
    ValidationRule(
        rule_id="range_retaining_wall_height",
        rule_name="挡土墙高度范围校验",
        data_type="retaining_wall",
        field_name="height",
        rule_type=RuleType.RANGE,
        parameters={"min": 0, "max": 20},
        severity=Severity.ERROR,
        description="挡土墙高度不应超过20米"
    ),
    ValidationRule(
        rule_id="range_anchor_length",
        rule_name="锚杆长度范围校验",
        data_type="anchor",
        field_name="length",
        rule_type=RuleType.RANGE,
        parameters={"min": 3, "max": 50},
        severity=Severity.WARNING,
        description="锚杆长度应在3-50米之间"
    ),
]


def get_predefined_rules(data_type: str = None) -> List[ValidationRule]:
    """
    获取预定义规则
    
    Args:
        data_type: 数据类型过滤 (可选)
        
    Returns:
        规则列表
    """
    if data_type:
        return [r for r in PREDEFINED_RULES if r.data_type == data_type]
    return PREDEFINED_RULES


def get_rule_by_id(rule_id: str) -> ValidationRule:
    """根据ID获取规则"""
    for rule in PREDEFINED_RULES:
        if rule.rule_id == rule_id:
            return rule
    return None


# 规则ID到规则的映射
RULE_MAP = {rule.rule_id: rule for rule in PREDEFINED_RULES}
