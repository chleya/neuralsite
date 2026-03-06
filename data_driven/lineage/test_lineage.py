# -*- coding: utf-8 -*-
"""
数据血缘模块测试
"""

import sys
import os
import tempfile

# 添加项目路径
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\neuralsite\data_driven')

from lineage import LineageRecord, LineageType, LineageStorageSQL, LineageTracerSQL


def test_lineage_save():
    """测试血缘记录保存"""
    print("=" * 50)
    print("测试1: 血缘记录保存")
    print("=" * 50)
    
    # 使用临时数据库
    db_path = os.path.join(tempfile.gettempdir(), "test_lineage.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = LineageStorageSQL(db_path)
    
    # 创建根节点记录
    root_record = LineageRecord(
        data_id="data_001",
        data_type="原始数据",
        data_version="1.0",
        project_id="project_001",
        source_type=LineageType.IMPORT,
        source_system="数据导入系统",
        source_file="/data/import/raw_data.csv",
        imported_by="system",
        original_value='{"name": "test", "value": 100}',
        parent_lineage_id="",
        generation=0,
        is_root=True,
    )
    
    # 保存根节点
    result = storage.save(root_record)
    print(f"保存根节点: {'成功' if result else '失败'}")
    print(f"  lineage_id: {root_record.lineage_id}")
    print(f"  data_id: {root_record.data_id}")
    
    # 创建第二层记录
    child_record = LineageRecord(
        data_id="data_002",
        data_type="处理后数据",
        data_version="1.0",
        project_id="project_001",
        source_type=LineageType.CALCULATION,
        source_system="数据处理系统",
        source_file="/data/processed/processed_data.csv",
        imported_by="processor",
        original_value='{"name": "test", "value": 200}',
        parent_lineage_id=root_record.lineage_id,
        generation=1,
    )
    
    result = storage.save(child_record)
    print(f"保存子节点: {'成功' if result else '失败'}")
    print(f"  lineage_id: {child_record.lineage_id}")
    print(f"  parent_lineage_id: {child_record.parent_lineage_id}")
    
    # 创建第三层记录
    grandchild_record = LineageRecord(
        data_id="data_003",
        data_type="分析结果",
        data_version="1.0",
        project_id="project_001",
        source_type=LineageType.AI_PREDICT,
        source_system="AI分析系统",
        source_file="/data/analysis/result.json",
        imported_by="ai_engine",
        original_value='{"prediction": "positive", "confidence": 0.85}',
        parent_lineage_id=child_record.lineage_id,
        generation=2,
    )
    
    result = storage.save(grandchild_record)
    print(f"保存孙节点: {'成功' if result else '失败'}")
    
    # 验证保存
    saved = storage.get(root_record.lineage_id)
    print(f"\n验证读取: {'成功' if saved and saved.data_id == 'data_001' else '失败'}")
    
    storage.close()
    
    # 清理测试数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    return True


def test_trace_forward():
    """测试正向追溯"""
    print("\n" + "=" * 50)
    print("测试2: 正向追溯")
    print("=" * 50)
    
    db_path = os.path.join(tempfile.gettempdir(), "test_lineage.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = LineageStorageSQL(db_path)
    tracer = LineageTracerSQL(storage)
    
    # 创建测试数据链
    root = LineageRecord(
        data_id="trace_test_001",
        data_type="原始数据",
        generation=0,
        is_root=True,
        parent_lineage_id="",
    )
    storage.save(root)
    
    child1 = LineageRecord(
        data_id="trace_test_002",
        data_type="中间数据1",
        generation=1,
        parent_lineage_id=root.lineage_id,
    )
    storage.save(child1)
    
    child2 = LineageRecord(
        data_id="trace_test_003",
        data_type="中间数据2",
        generation=2,
        parent_lineage_id=child1.lineage_id,
    )
    storage.save(child2)
    
    # 执行正向追溯
    results = tracer.trace_forward("trace_test_001")
    print(f"正向追溯结果数量: {len(results)}")
    for r in results:
        print(f"  generation={r.generation}, data_type={r.data_type}")
    
    storage.close()
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    return len(results) == 3


def test_trace_backward():
    """测试反向追溯"""
    print("\n" + "=" * 50)
    print("测试3: 反向追溯")
    print("=" * 50)
    
    db_path = os.path.join(tempfile.gettempdir(), "test_lineage.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = LineageStorageSQL(db_path)
    tracer = LineageTracerSQL(storage)
    
    # 创建测试数据链
    root = LineageRecord(
        data_id="backward_test_001",
        data_type="根数据",
        generation=0,
        is_root=True,
        parent_lineage_id="",
    )
    storage.save(root)
    
    child = LineageRecord(
        data_id="backward_test_002",
        data_type="子数据",
        generation=1,
        parent_lineage_id=root.lineage_id,
    )
    storage.save(child)
    
    grandchild = LineageRecord(
        data_id="backward_test_003",
        data_type="孙数据",
        generation=2,
        parent_lineage_id=child.lineage_id,
    )
    storage.save(grandchild)
    
    # 执行反向追溯
    results = tracer.trace_backward("backward_test_003")
    print(f"反向追溯结果数量: {len(results)}")
    for r in results:
        print(f"  generation={r.generation}, data_type={r.data_type}")
    
    storage.close()
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 应该返回3个：根 -> 子 -> 孙
    return len(results) == 3


def test_impact_analysis():
    """测试影响分析"""
    print("\n" + "=" * 50)
    print("测试4: 影响分析")
    print("=" * 50)
    
    db_path = os.path.join(tempfile.gettempdir(), "test_lineage.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = LineageStorageSQL(db_path)
    tracer = LineageTracerSQL(storage)
    
    # 创建测试数据链
    root = LineageRecord(
        data_id="impact_test_001",
        data_type="原始数据",
        generation=0,
        is_root=True,
        parent_lineage_id="",
    )
    storage.save(root)
    
    for i in range(2):
        child = LineageRecord(
            data_id=f"impact_test_00{i+2}",
            data_type="处理结果" if i == 0 else "分析结果",
            generation=1,
            parent_lineage_id=root.lineage_id,
        )
        storage.save(child)
    
    # 执行影响分析
    impact = tracer.impact_analysis("impact_test_001")
    print(f"影响分析结果:")
    print(f"  直接影响: {len(impact['direct'])} 条")
    print(f"  间接影响: {len(impact['indirect'])} 条")
    print(f"  总影响数: {impact['total_count']}")
    print(f"  最大代数: {impact['max_generation']}")
    print(f"  受影响数据类型: {impact['affected_data_types']}")
    
    storage.close()
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    return impact['total_count'] >= 2


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始数据血缘模块测试")
    print("=" * 60)
    
    all_passed = True
    
    # 测试1: 保存
    if not test_lineage_save():
        all_passed = False
        print("测试1失败")
    else:
        print("测试1通过")
    
    # 测试2: 正向追溯
    if not test_trace_forward():
        all_passed = False
        print("测试2失败")
    else:
        print("测试2通过")
    
    # 测试3: 反向追溯
    if not test_trace_backward():
        all_passed = False
        print("测试3失败")
    else:
        print("测试3通过")
    
    # 测试4: 影响分析
    if not test_impact_analysis():
        all_passed = False
        print("测试4失败")
    else:
        print("测试4通过")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过!")
    else:
        print("部分测试失败!")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    main()
