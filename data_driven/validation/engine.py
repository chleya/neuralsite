# -*- coding: utf-8 -*-
"""
校验引擎
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """严重级别"""
    FATAL = "fatal"     # 致命错误
    ERROR = "error"     # 错误
    WARNING = "warning"  # 警告
    INFO = "info"        # 提示


class RuleType(Enum):
    """规则类型"""
    RANGE = "range"           # 范围校验
    CONSISTENCY = "consistency" # 一致性校验
    TREND = "trend"           # 趋势校验
    CUSTOM = "custom"          # 自定义校验


@dataclass
class ValidationRule:
    """校验规则"""
    rule_id: str
    rule_name: str
    data_type: str
    field_name: str
    rule_type: RuleType
    parameters: Dict[str, Any]
    severity: Severity
    description: str = ""
    is_enabled: bool = True


@dataclass
class RuleResult:
    """单条规则校验结果"""
    rule_id: str
    passed: bool
    message: str
    severity: Severity
    field_value: Any = None


@dataclass
class ValidationResult:
    """校验结果"""
    passed: bool
    fatal_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    details: List[RuleResult] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class ValidationEngine:
    """校验执行引擎"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule):
        """添加规则"""
        self.rules.append(rule)
    
    def validate(self, data: Dict[str, Any], data_type: str) -> ValidationResult:
        """
        对数据进行校验
        
        Args:
            data: 待校验数据
            data_type: 数据类型
            
        Returns:
            校验结果
        """
        # 获取适用的规则
        applicable_rules = [r for r in self.rules 
                          if r.data_type == data_type and r.is_enabled]
        
        results = []
        for rule in applicable_rules:
            result = self._apply_rule(rule, data)
            results.append(result)
        
        # 统计
        fatal_count = sum(1 for r in results 
                         if r.severity == Severity.FATAL and not r.passed)
        error_count = sum(1 for r in results 
                        if r.severity == Severity.ERROR and not r.passed)
        warning_count = sum(1 for r in results 
                          if r.severity == Severity.WARNING and not r.passed)
        
        return ValidationResult(
            passed=(fatal_count == 0 and error_count == 0),
            fatal_count=fatal_count,
            error_count=error_count,
            warning_count=warning_count,
            details=results
        )
    
    def _apply_rule(self, rule: ValidationRule, 
                   data: Dict[str, Any]) -> RuleResult:
        """应用单条规则"""
        try:
            if rule.rule_type == RuleType.RANGE:
                return self._validate_range(rule, data)
            elif rule.rule_type == RuleType.CONSISTENCY:
                return self._validate_consistency(rule, data)
            elif rule.rule_type == RuleType.TREND:
                return self._validate_trend(rule, data)
            else:
                return RuleResult(
                    rule_id=rule.rule_id,
                    passed=True,
                    message="Custom rule not implemented",
                    severity=rule.severity
                )
        except Exception as e:
            return RuleResult(
                rule_id=rule.rule_id,
                passed=False,
                message=f"Rule execution error: {str(e)}",
                severity=rule.severity
            )
    
    def _validate_range(self, rule: ValidationRule, 
                      data: Dict[str, Any]) -> RuleResult:
        """范围校验"""
        value = data.get(rule.field_name)
        if value is None:
            return RuleResult(
                rule_id=rule.rule_id,
                passed=True,
                message="Field not exists",
                severity=rule.severity
            )
        
        params = rule.parameters
        min_val = params.get("min")
        max_val = params.get("max")
        
        if min_val is not None and value < min_val:
            return RuleResult(
                rule_id=rule.rule_id,
                passed=False,
                message=f"Value {value} below minimum {min_val}",
                severity=rule.severity,
                field_value=value
            )
        
        if max_val is not None and value > max_val:
            return RuleResult(
                rule_id=rule.rule_id,
                passed=False,
                message=f"Value {value} above maximum {max_val}",
                severity=rule.severity,
                field_value=value
            )
        
        return RuleResult(
            rule_id=rule.rule_id,
            passed=True,
            message="Within range",
            severity=rule.severity,
            field_value=value
        )
    
    def _validate_consistency(self, rule: ValidationRule,
                            data: Dict[str, Any]) -> RuleResult:
        """一致性校验"""
        # TODO: 实现一致性校验逻辑
        return RuleResult(
            rule_id=rule.rule_id,
            passed=True,
            message="Consistency check passed",
            severity=rule.severity
        )
    
    def _validate_trend(self, rule: ValidationRule,
                       data: Dict[str, Any]) -> RuleResult:
        """趋势校验"""
        # TODO: 实现趋势校验逻辑
        return RuleResult(
            rule_id=rule.rule_id,
            passed=True,
            message="Trend check passed",
            severity=rule.severity
        )
