# -*- coding: utf-8 -*-
"""
测试校验规则
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import ValidationEngine, ValidationRule, PREDEFINED_RULES, get_predefined_rules, RULE_MAP, RuleType, Severity


def test_predefined_rules():
    print('=== 测试1: 预定义规则加载 ===')
    print(f'预定义规则总数: {len(PREDEFINED_RULES)}')
    print()


def test_filter_by_type():
    print('=== 测试2: 按数据类型过滤 ===')
    earthwork_rules = get_predefined_rules('earthwork')
    print(f'土石方工程规则: {len(earthwork_rules)}')
    for r in earthwork_rules:
        print(f'  - {r.rule_id}: {r.rule_name}')
    print()


def test_validation():
    print('=== 测试3: 规则校验功能 ===')
    engine = ValidationEngine()
    for rule in PREDEFINED_RULES[:3]:
        engine.add_rule(rule)

    # 测试数据
    test_cases = [
        {'data_type': 'pavement_layer', 'data': {'thickness': 0.30, 'width': 8.0}},
        {'data_type': 'earthwork', 'data': {'depth': 25, 'fill_height': 15}},
        {'data_type': 'bridge', 'data': {'span': 50, 'width': 12}},
    ]

    for tc in test_cases:
        result = engine.validate(tc['data'], tc['data_type'])
        print(f'数据类型: {tc["data_type"]}')
        print(f'  通过: {result.passed}')
        print(f'  错误: {result.error_count}, 警告: {result.warning_count}')
        for d in result.details:
            status = 'OK' if d.passed else 'FAIL'
            print(f'    [{status}] {d.rule_id}: {d.message}')
        print()


def test_range_validation():
    print('=== 测试4: 范围校验边界测试 ===')
    engine = ValidationEngine()
    
    # 添加路面厚度规则
    thickness_rule = [r for r in PREDEFINED_RULES if r.rule_id == 'range_pavement_thickness'][0]
    engine.add_rule(thickness_rule)
    
    test_values = [0.10, 0.15, 0.30, 0.50, 0.60]
    for val in test_values:
        result = engine.validate({'thickness': val}, 'pavement_layer')
        # 检查具体规则结果
        rule_result = result.details[0] if result.details else None
        if rule_result:
            status = 'PASS' if rule_result.passed else f'FAIL ({rule_result.message})'
            print(f'  thickness={val}: {status}')


if __name__ == '__main__':
    test_predefined_rules()
    test_filter_by_type()
    test_validation()
    test_range_validation()
    print('=== 所有测试完成 ===')
