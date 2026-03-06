# -*- coding: utf-8 -*-
"""
测试数据接口模块
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("Test: Module Imports")
    print("=" * 50)
    
    try:
        from data_driven.interfaces import (
            router,
            create_rest_routes,
            manager,
            subscription_manager,
            EventType,
            websocket_endpoint
        )
        print("[OK] All modules imported successfully")
        
        # 检查路由数量
        routes = [r for r in router.routes]
        print(f"[OK] REST API routes: {len(routes)}")
        
        # 检查事件类型
        event_types = list(EventType)
        print(f"[OK] Event types: {len(event_types)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """测试数据模型"""
    print("\n" + "=" * 50)
    print("Test: Data Models")
    print("=" * 50)
    
    try:
        from data_driven.interfaces.models import (
            ProjectCreate,
            ChainRecordCreate,
            PhotoCreate,
            IssueCreate
        )
        
        # 测试项目创建
        project = ProjectCreate(
            name="Test Project",
            description="This is a test project"
        )
        print(f"[OK] ProjectCreate: {project.name}")
        
        # 测试存证创建
        record = ChainRecordCreate(
            data_type="test",
            data={"test": "data"},
            operator="tester"
        )
        print(f"[OK] ChainRecordCreate: {record.data_type}")
        
        # 测试照片创建
        photo = PhotoCreate(
            entity_id="entity-001",
            station="K0+100",
            filename="test.jpg",
            file_path="/uploads/test.jpg"
        )
        print(f"[OK] PhotoCreate: {photo.filename}")
        
        # 测试问题创建
        issue = IssueCreate(
            station="K0+200",
            issue_type="quality",
            severity="high",
            description="Test issue"
        )
        print(f"[OK] IssueCreate: {issue.issue_type}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_websocket_manager():
    """测试WebSocket管理器"""
    print("\n" + "=" * 50)
    print("Test: WebSocket Manager")
    print("=" * 50)
    
    try:
        from data_driven.interfaces.websocket import (
            ConnectionManager,
            DataSubscriptionManager,
            EventType
        )
        
        # 测试连接管理器
        mgr = ConnectionManager()
        print(f"[OK] ConnectionManager created")
        print(f"     - Initial connections: {mgr.get_connection_count()}")
        
        # 测试订阅管理器
        sub_mgr = DataSubscriptionManager()
        sub_mgr.set_manager(mgr)
        print(f"[OK] DataSubscriptionManager created")
        
        # 测试事件类型
        print(f"[OK] Supported event types:")
        for et in EventType:
            print(f"     - {et.value}")
        
        return True
    except Exception as e:
        print(f"[FAIL] WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rest_endpoints():
    """测试REST端点定义"""
    print("\n" + "=" * 50)
    print("Test: REST Endpoints")
    print("=" * 50)
    
    try:
        from data_driven.interfaces.rest import (
            list_projects,
            create_project,
            get_station_coordinates,
            get_nearest_station,
            submit_chain_record,
            verify_chain_record
        )
        
        print("[OK] Main endpoints defined:")
        print("     - list_projects")
        print("     - create_project")
        print("     - get_station_coordinates")
        print("     - get_nearest_station")
        print("     - submit_chain_record")
        print("     - verify_chain_record")
        
        return True
    except Exception as e:
        print(f"[FAIL] REST endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Running Data Interface Module Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Data Models", test_models()))
    results.append(("WebSocket Manager", test_websocket_manager()))
    results.append(("REST Endpoints", test_rest_endpoints()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed, please check errors")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
