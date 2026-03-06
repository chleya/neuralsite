# -*- coding: utf-8 -*-
"""
测试校验API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from validation.api import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_rules():
    print('=== 测试API: 获取规则列表 ===')
    
    # 获取所有规则
    response = client.get("/api/v1/validation/rules")
    print(f'获取所有规则: {response.status_code}')
    rules = response.json()
    print(f'  规则数量: {len(rules)}')
    
    # 按类型过滤
    response = client.get("/api/v1/validation/rules?data_type=earthwork")
    print(f'土石方规则: {response.status_code}')
    earthwork = response.json()
    print(f'  数量: {len(earthwork)}')
    for r in earthwork:
        print(f'    - {r["rule_id"]}: {r["rule_name"]}')
    print()


def test_get_rule_by_id():
    print('=== 测试API: 获取单条规则 ===')
    response = client.get("/api/v1/validation/rules/range_pavement_thickness")
    print(f'状态: {response.status_code}')
    rule = response.json()
    print(f'  {rule["rule_id"]}: {rule["rule_name"]}')
    print(f'  参数: {rule["parameters"]}')
    print()


def test_validate():
    print('=== 测试API: 数据校验 ===')
    
    # 正常数据
    response = client.post("/api/v1/validation/validate", json={
        "data": {"thickness": 0.30, "width": 8.0},
        "data_type": "pavement_layer"
    })
    print(f'正常数据: {response.status_code}')
    result = response.json()
    print(f'  通过: {result["passed"]}, 错误: {result["error_count"]}, 警告: {result["warning_count"]}')
    for d in result['details']:
        print(f'    [{d["passed"]}] {d["rule_id"]}: {d["message"]}')
    
    # 异常数据 (超范围)
    response = client.post("/api/v1/validation/validate", json={
        "data": {"thickness": 0.08},  # 小于最小值0.15
        "data_type": "pavement_layer"
    })
    print(f'\n异常数据: {response.status_code}')
    result = response.json()
    print(f'  通过: {result["passed"]}, 错误: {result["error_count"]}, 警告: {result["warning_count"]}')
    for d in result['details']:
        if not d['passed']:
            print(f'    [FAIL] {d["rule_id"]}: {d["message"]}')
    print()


def test_create_rule():
    print('=== 测试API: 创建规则 ===')
    
    new_rule = {
        "rule_id": "custom_range_test",
        "rule_name": "自定义测试规则",
        "data_type": "test",
        "field_name": "value",
        "rule_type": "range",
        "parameters": {"min": 0, "max": 100},
        "severity": "warning",
        "description": "测试用规则",
        "is_enabled": True
    }
    
    response = client.post("/api/v1/validation/rules", json=new_rule)
    print(f'创建规则: {response.status_code}')
    created = response.json()
    print(f'  {created["rule_id"]}: {created["rule_name"]}')
    
    # 验证创建成功
    response = client.get("/api/v1/validation/rules/custom_range_test")
    print(f'验证存在: {response.status_code}')
    print()


def test_engine_status():
    print('=== 测试API: 引擎状态 ===')
    response = client.get("/api/v1/validation/engine/status")
    print(f'状态: {response.status_code}')
    status = response.json()
    print(f'  总规则: {status["total_rules"]}')
    print(f'  启用规则: {status["enabled_rules"]}')
    print(f'  预定义规则: {status["predefined_rules"]}')
    print()


if __name__ == '__main__':
    test_get_rules()
    test_get_rule_by_id()
    test_validate()
    test_create_rule()
    test_engine_status()
    print('=== API测试完成 ===')
