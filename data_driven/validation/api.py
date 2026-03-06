# -*- coding: utf-8 -*-
"""
校验规则管理API
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import ValidationEngine, ValidationResult, ValidationRule, RuleType, Severity, RuleResult
from .rules import PREDEFINED_RULES, get_predefined_rules, RULE_MAP

# 创建全局校验引擎实例
validation_engine = ValidationEngine()

# 存储自定义规则
custom_rules: Dict[str, ValidationRule] = {}

# 初始化时加载预定义规则
for rule in PREDEFINED_RULES:
    validation_engine.add_rule(rule)

# ==================== Pydantic Models ====================

class RuleCreate(BaseModel):
    """创建规则请求"""
    rule_id: str
    rule_name: str
    data_type: str
    field_name: str
    rule_type: str
    parameters: Dict[str, Any]
    severity: str
    description: str = ""
    is_enabled: bool = True


class RuleResponse(BaseModel):
    """规则响应"""
    rule_id: str
    rule_name: str
    data_type: str
    field_name: str
    rule_type: str
    parameters: Dict[str, Any]
    severity: str
    description: str
    is_enabled: bool


class ValidateRequest(BaseModel):
    """校验请求"""
    data: Dict[str, Any]
    data_type: str


class RuleResultResponse(BaseModel):
    """单条规则校验结果"""
    rule_id: str
    passed: bool
    message: str
    severity: str
    field_value: Any = None


class ValidationResultResponse(BaseModel):
    """校验结果响应"""
    passed: bool
    fatal_count: int
    error_count: int
    warning_count: int
    details: List[RuleResultResponse]


# ==================== API Router ====================

router = APIRouter(prefix="/api/v1/validation", tags=["校验"])


def rule_to_response(rule: ValidationRule) -> RuleResponse:
    """将ValidationRule转换为响应模型"""
    return RuleResponse(
        rule_id=rule.rule_id,
        rule_name=rule.rule_name,
        data_type=rule.data_type,
        field_name=rule.field_name,
        rule_type=rule.rule_type.value,
        parameters=rule.parameters,
        severity=rule.severity.value,
        description=rule.description,
        is_enabled=rule.is_enabled
    )


def rule_result_to_response(result: RuleResult) -> RuleResultResponse:
    """将RuleResult转换为响应模型"""
    return RuleResultResponse(
        rule_id=result.rule_id,
        passed=result.passed,
        message=result.message,
        severity=result.severity.value,
        field_value=result.field_value
    )


def validation_result_to_response(result: ValidationResult) -> ValidationResultResponse:
    """将ValidationResult转换为响应模型"""
    return ValidationResultResponse(
        passed=result.passed,
        fatal_count=result.fatal_count,
        error_count=result.error_count,
        warning_count=result.warning_count,
        details=[rule_result_to_response(d) for d in result.details]
    )


@router.get("/rules", response_model=List[RuleResponse])
async def get_rules(data_type: Optional[str] = Query(None, description="数据类型过滤")):
    """
    获取校验规则列表
    
    - 不指定data_type: 返回所有预定义规则
    - 指定data_type: 返回该类型的所有规则
    """
    rules = get_predefined_rules(data_type)
    return [rule_to_response(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """根据ID获取单条规则"""
    # 先查预定义规则，再查自定义规则
    rule = RULE_MAP.get(rule_id) or custom_rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    return rule_to_response(rule)


@router.post("/rules", response_model=RuleResponse)
async def create_rule(rule: RuleCreate):
    """
    创建自定义校验规则
    
    创建后自动添加到校验引擎
    """
    # 检查规则ID是否已存在
    if rule.rule_id in RULE_MAP or rule.rule_id in custom_rules:
        raise HTTPException(status_code=400, detail=f"Rule {rule.rule_id} already exists")
    
    try:
        # 转换类型
        rule_type = RuleType(rule.rule_type)
        severity = Severity(rule.severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid type: {str(e)}")
    
    # 创建规则对象
    new_rule = ValidationRule(
        rule_id=rule.rule_id,
        rule_name=rule.rule_name,
        data_type=rule.data_type,
        field_name=rule.field_name,
        rule_type=rule_type,
        parameters=rule.parameters,
        severity=severity,
        description=rule.description,
        is_enabled=rule.is_enabled
    )
    
    # 添加到引擎和自定义规则字典
    validation_engine.add_rule(new_rule)
    custom_rules[rule.rule_id] = new_rule
    
    return rule_to_response(new_rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """
    删除规则 (仅删除运行时添加的自定义规则)
    
    预定义规则不可删除
    """
    # 检查是否为预定义规则
    if rule_id in RULE_MAP:
        # 预定义规则 - 只禁用不删除
        rule = RULE_MAP[rule_id]
        rule.is_enabled = False
        return {"message": f"Rule {rule_id} disabled (predefined)"}
    
    # 检查自定义规则
    if rule_id in custom_rules:
        del custom_rules[rule_id]
    
    # 运行时规则 - 从引擎中移除
    for i, rule in enumerate(validation_engine.rules):
        if rule.rule_id == rule_id:
            validation_engine.rules.pop(i)
            return {"message": f"Rule {rule_id} deleted"}
    
    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@router.post("/validate", response_model=ValidationResultResponse)
async def validate_data(request: ValidateRequest):
    """
    校验数据
    
    - 根据data_type自动匹配适用的规则
    - 返回所有规则的校验结果
    """
    result = validation_engine.validate(request.data, request.data_type)
    return validation_result_to_response(result)


@router.get("/engine/status")
async def engine_status():
    """获取引擎状态"""
    return {
        "total_rules": len(validation_engine.rules),
        "enabled_rules": sum(1 for r in validation_engine.rules if r.is_enabled),
        "predefined_rules": len(PREDEFINED_RULES)
    }


@router.post("/engine/reset")
async def reset_engine():
    """
    重置引擎
    
    重新加载预定义规则，移除所有自定义规则
    """
    validation_engine.rules.clear()
    for rule in PREDEFINED_RULES:
        validation_engine.add_rule(rule)
    return {"message": "Engine reset to predefined rules"}
