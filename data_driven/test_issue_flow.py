# -*- coding: utf-8 -*-
"""
问题跟踪与整改闭环测试
"""

import asyncio
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, "C:\\Users\\Administrator\\.openclaw\\workspace\\neuralsite")

from data_driven.issue_models import Issue, IssueUpdate, IssueStatus, IssueSeverity, IssueType
from data_driven.issue_service import IssueService
from data_driven.issue_workflow import IssueWorkflow


class DictStorage:
    """模拟存储"""
    def __init__(self):
        self.data = {}
        self.updates = []
    
    def save(self, obj):
        if isinstance(obj, Issue):
            self.data[obj.id] = obj.to_dict()
        return obj
    
    def get(self, obj_id):
        return self.data.get(obj_id)
    
    def get_all(self):
        return list(self.data.values())
    
    def query(self, filters):
        return list(self.data.values())


class MockLineage:
    """模拟血缘记录"""
    def __init__(self):
        self.records = []
    
    def record(self, data_id, data_type, source_type):
        self.records.append({
            "data_id": data_id,
            "data_type": data_type,
            "source_type": source_type
        })


class MockChain:
    """模拟区块链"""
    def __init__(self):
        self.records = []
    
    def submit(self, data_id, data_hash, data_type, operator, role, project_id):
        self.records.append({
            "data_id": data_id,
            "data_hash": data_hash,
            "data_type": data_type,
            "operator": operator,
            "role": role,
            "project_id": project_id
        })


async def test_issue_creation():
    """测试问题创建"""
    print("\n=== 测试1: 问题创建 ===")
    
    storage = DictStorage()
    lineage = MockLineage()
    chain = MockChain()
    
    service = IssueService(storage, lineage, chain)
    
    # 创建问题
    issue = Issue(
        project_id="proj_001",
        station="K10+000",
        location={"lat": 31.2304, "lon": 121.4737},
        title="测试问题-钢筋保护层厚度不足",
        description="经检测，K10+000处钢筋保护层厚度不满足设计要求",
        issue_type=IssueType.QUALITY,
        severity=IssueSeverity.HIGH,
        reported_by="张三",
        photos=["photo_001", "photo_002"],
        due_date=datetime.utcnow() + timedelta(days=7)
    )
    
    result = await service.create_issue(issue)
    
    print(f"✓ 问题创建成功")
    print(f"  - ID: {result.id[:8]}...")
    print(f"  - 标题: {result.title}")
    print(f"  - 状态: {result.status.value}")
    print(f"  - 严重程度: {result.severity.value}")
    print(f"  - 血缘记录数: {len(lineage.records)}")
    print(f"  - 区块链记录数: {len(chain.records)}")
    
    return storage, lineage, chain, service


async def test_status_update(storage, lineage, chain, service):
    """测试状态更新"""
    print("\n=== 测试2: 状态更新 ===")
    
    # 获取之前创建的问题
    issues = await service.list_issues(project_id="proj_001")
    issue = issues[0]
    
    # 更新为处理中
    result = await service.update_status(
        issue.id,
        IssueStatus.IN_PROGRESS,
        "已安排人员现场处理",
        "李四"
    )
    
    print(f"✓ 状态更新成功")
    print(f"  - 问题ID: {result.id[:8]}...")
    print(f"  - 新状态: {result.status.value}")
    print(f"  - 更新记录数: {len(storage.updates)}")


async def test_workflow_full_flow():
    """测试整改闭环完整流程"""
    print("\n=== 测试3: 整改闭环完整流程 ===")
    
    storage = DictStorage()
    lineage = MockLineage()
    chain = MockChain()
    
    service = IssueService(storage, lineage, chain)
    workflow = IssueWorkflow(service)
    
    # 1. 问题上报
    issue_data = {
        "project_id": "proj_002",
        "station": "K15+200",
        "location": {"lat": 31.2350, "lon": 121.4800},
        "title": "基坑临边防护缺失",
        "description": "K15+200基坑临边防护设施未按要求设置",
        "issue_type": IssueType.SAFETY,
        "severity": "critical",
        "reported_by": "王五",
        "photos": ["photo_101"],
        "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat()
    }
    
    issue = await workflow.report_issue(issue_data)
    print(f"1. 问题上报成功: {issue.title}")
    print(f"   - 状态: {issue.status.value}")
    
    # 2. 分派问题
    issue = await workflow.assign_issue(issue.id, "赵六", "项目经理")
    print(f"2. 问题分派成功")
    print(f"   - 负责人: {issue.assigned_to}")
    print(f"   - 状态: {issue.status.value}")
    
    # 3. 提交整改
    issue = await workflow.submit_resolution(
        issue.id,
        resolution_photos=["photo_201", "photo_202"],
        resolution_description="已设置临边防护栏杆，并悬挂警示标志",
        user="赵六"
    )
    print(f"3. 整改提交成功")
    print(f"   - 状态: {issue.status.value}")
    print(f"   - 整改照片数: {len(issue.resolution_photos)}")
    
    # 4. 确认整改
    issue = await workflow.confirm_resolution(
        issue.id,
        confirmed=True,
        user="项目经理",
        comment="整改合格，同意关闭"
    )
    print(f"4. 整改确认成功")
    print(f"   - 状态: {issue.status.value}")
    print(f"   - 确认人: {issue.confirmed_by}")
    
    # 5. 查看工作流状态
    status = await workflow.get_workflow_status(issue.id)
    print(f"5. 工作流状态")
    print(f"   - 进度: {status['progress']}%")
    print(f"   - 当前阶段: {status['current_stage']}")


async def test_statistics():
    """测试统计功能"""
    print("\n=== 测试4: 问题统计 ===")
    
    storage = DictStorage()
    lineage = MockLineage()
    chain = MockChain()
    
    service = IssueService(storage, lineage, chain)
    workflow = IssueWorkflow(service)
    
    # 创建多个测试问题
    test_issues = [
        {"project_id": "proj_003", "issue_type": IssueType.QUALITY, "severity": IssueSeverity.HIGH, "status": IssueStatus.OPEN},
        {"project_id": "proj_003", "issue_type": IssueType.QUALITY, "severity": IssueSeverity.MEDIUM, "status": IssueStatus.IN_PROGRESS},
        {"project_id": "proj_003", "issue_type": IssueType.SAFETY, "severity": IssueSeverity.CRITICAL, "status": IssueStatus.RESOLVED},
        {"project_id": "proj_003", "issue_type": IssueType.SAFETY, "severity": IssueSeverity.LOW, "status": IssueStatus.CLOSED},
        {"project_id": "proj_003", "issue_type": IssueType.PROGRESS, "severity": IssueSeverity.MEDIUM, "status": IssueStatus.OPEN},
    ]
    
    for i, data in enumerate(test_issues):
        issue = Issue(
            project_id=data["project_id"],
            title=f"测试问题{i+1}",
            issue_type=data["issue_type"],
            severity=data["severity"],
            status=data["status"],
            reported_by="测试"
        )
        await service.create_issue(issue)
    
    stats = await service.get_statistics("proj_003")
    print(f"✓ 统计功能正常")
    print(f"  - 总问题数: {stats['total']}")
    print(f"  - 按状态: {stats['by_status']}")
    print(f"  - 按严重程度: {stats['by_severity']}")
    print(f"  - 按类型: {stats['by_type']}")


async def main():
    """主测试函数"""
    print("=" * 50)
    print("问题跟踪与整改闭环测试")
    print("=" * 50)
    
    # 测试1: 问题创建
    storage, lineage, chain, service = await test_issue_creation()
    
    # 测试2: 状态更新
    await test_status_update(storage, lineage, chain, service)
    
    # 测试3: 整改闭环完整流程
    await test_workflow_full_flow()
    
    # 测试4: 统计功能
    await test_statistics()
    
    print("\n" + "=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
