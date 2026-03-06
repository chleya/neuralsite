# -*- coding: utf-8 -*-
"""
问题整改闭环工作流

提供问题上报、分派、整改、确认的完整流程
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .issue_models import Issue, IssueStatus, IssueSeverity, IssueType
from .issue_service import IssueService


class IssueWorkflow:
    """问题整改闭环工作流"""
    
    def __init__(self, issue_service: IssueService):
        """
        初始化工作流
        
        Args:
            issue_service: 问题服务实例
        """
        self.issue_service = issue_service
    
    async def report_issue(self, data: dict) -> Issue:
        """
        问题上报
        
        Args:
            data: 问题数据字典
            
                {
                    "project_id": "项目ID",
                    "station": "桩号",
                    "location": {"lat": 1.0, "lon": 2.0},
                    "title": "问题标题",
                    "description": "问题描述",
                    "issue_type": "quality|safety|progress|design|material|other",
                    "severity": "low|medium|high|critical",
                    "reported_by": "上报人",
                    "photos": ["photo_id1", "photo_id2"],
                    "due_date": "2024-12-31"  # 可选
                }
            
        Returns:
            创建的问题对象
        """
        # 1. 处理严重程度
        severity = data.get("severity", "medium")
        if isinstance(severity, str):
            severity = IssueSeverity(severity)
        
        # 2. 处理截止日期
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        
        # 3. 创建问题对象
        issue = Issue(
            project_id=data.get("project_id", ""),
            station=data.get("station", ""),
            location=data.get("location", {"lat": None, "lon": None}),
            title=data.get("title", ""),
            description=data.get("description", ""),
            issue_type=data.get("issue_type", IssueType.QUALITY),
            severity=severity,
            status=IssueStatus.OPEN,
            reported_by=data.get("reported_by", ""),
            photos=data.get("photos", []),
            due_date=due_date
        )
        
        # 4. AI初筛（可选扩展点）
        # await self.ai_screen(issue)
        
        # 5. 保存并上链
        return await self.issue_service.create_issue(issue)
    
    async def assign_issue(self, issue_id: str, assignee: str, 
                          user: str) -> Issue:
        """
        分派问题
        
        Args:
            issue_id: 问题ID
            assignee: 负责人
            user: 操作用户
            
        Returns:
            更新后的问题对象
        """
        # 1. 分派给责任人
        issue = await self.issue_service.assign_issue(issue_id, assignee, user)
        
        # 2. 记录分派时间（在issue_service中已处理）
        
        # 3. 发送通知（扩展点）
        # await self._send_notification(issue, "assigned")
        
        return issue
    
    async def submit_resolution(self, issue_id: str, 
                             resolution_photos: List[str],
                             resolution_description: str,
                             user: str) -> Issue:
        """
        提交整改
        
        Args:
            issue_id: 问题ID
            resolution_photos: 整改照片ID列表
            resolution_description: 整改说明
            user: 操作用户
            
        Returns:
            更新后的问题对象
        """
        # 1. 获取问题
        issue = await self.issue_service.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        # 2. 验证问题状态
        if issue.status not in [IssueStatus.IN_PROGRESS, IssueStatus.OPEN]:
            raise ValueError(f"Cannot submit resolution for issue in status: {issue.status.value}")
        
        # 3. 记录整改信息
        resolution = {
            "description": resolution_description,
            "photos": resolution_photos,
            "submitted_at": datetime.utcnow().isoformat(),
            "submitted_by": user
        }
        
        # 4. 更新问题为已解决（等待确认）
        issue = await self.issue_service.resolve(
            issue_id, 
            resolution,
            user
        )
        
        # 5. 发送通知（扩展点）
        # await self._send_notification(issue, "resolution_submitted")
        
        return issue
    
    async def confirm_resolution(self, issue_id: str, 
                                confirmed: bool, 
                                user: str,
                                comment: str = "") -> Issue:
        """
        确认整改
        
        Args:
            issue_id: 问题ID
            confirmed: 是否确认通过
            user: 操作用户
            comment: 确认意见
            
        Returns:
            更新后的问题对象
        """
        # 1. 获取问题
        issue = await self.issue_service.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        # 2. 验证问题状态
        if issue.status != IssueStatus.RESOLVED:
            raise ValueError(f"Issue {issue_id} is not in resolved status")
        
        # 3. 确认整改
        issue = await self.issue_service.confirm_resolution(
            issue_id,
            confirmed,
            user,
            comment
        )
        
        # 4. 发送通知（扩展点）
        # if confirmed:
        #     await self._send_notification(issue, "resolved")
        # else:
        #     await self._send_notification(issue, "rejected")
        
        return issue
    
    async def get_workflow_status(self, issue_id: str) -> dict:
        """
        获取问题工作流状态
        
        Args:
            issue_id: 问题ID
            
        Returns:
            工作流状态信息
        """
        issue = await self.issue_service.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        # 计算工作流进度
        progress = 0
        current_stage = ""
        stages = []
        
        if issue.status == IssueStatus.OPEN:
            progress = 10
            current_stage = "reported"
            stages = ["reported", "assigned", "resolved", "confirmed"]
        elif issue.status == IssueStatus.IN_PROGRESS:
            progress = 40
            current_stage = "processing"
            stages = ["reported", "assigned", "processing", "resolved", "confirmed"]
        elif issue.status == IssueStatus.RESOLVED:
            progress = 70
            current_stage = "resolved"
            stages = ["reported", "assigned", "resolved", "confirmed"]
        elif issue.status == IssueStatus.CLOSED:
            progress = 100
            current_stage = "closed"
            stages = ["reported", "assigned", "resolved", "confirmed"]
        
        return {
            "issue_id": issue_id,
            "current_status": issue.status.value,
            "progress": progress,
            "current_stage": current_stage,
            "stages": stages,
            "assigned_to": issue.assigned_to,
            "reported_by": issue.reported_by,
            "resolved_by": issue.resolved_by,
            "confirmed_by": issue.confirmed_by,
            "reported_at": issue.reported_at.isoformat() if issue.reported_at else None,
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            "confirmed_at": issue.confirmed_at.isoformat() if issue.confirmed_at else None,
        }
    
    async def get_pending_confirmations(self, user: str = None) -> List[Issue]:
        """
        获取待确认的整改列表
        
        Args:
            user: 可选，按确认人过滤
            
        Returns:
            待确认的问题列表
        """
        issues = await self.issue_service.list_issues(status=IssueStatus.RESOLVED)
        
        if user:
            issues = [i for i in issues if i.resolved_by != user]
        
        return issues
    
    async def get_overdue_issues(self) -> List[Issue]:
        """
        获取逾期未解决的问题
        
        Returns:
            逾期问题列表
        """
        all_issues = await self.issue_service.list_issues()
        now = datetime.utcnow()
        
        overdue = []
        for issue in all_issues:
            # 只检查未关闭的问题
            if issue.status == IssueStatus.CLOSED:
                continue
            
            # 检查是否逾期
            if issue.due_date and issue.due_date < now:
                overdue.append(issue)
        
        return overdue
    
    async def bulk_assign(self, issue_ids: List[str], 
                         assignee: str, user: str) -> List[Issue]:
        """
        批量分派问题
        
        Args:
            issue_ids: 问题ID列表
            assignee: 负责人
            user: 操作用户
            
        Returns:
            更新后的问题列表
        """
        results = []
        for issue_id in issue_ids:
            try:
                issue = await self.assign_issue(issue_id, assignee, user)
                results.append(issue)
            except Exception as e:
                # 继续处理其他问题
                print(f"Failed to assign issue {issue_id}: {e}")
        
        return results
    
    async def reopen_issue(self, issue_id: str, reason: str, 
                          user: str) -> Issue:
        """
        重新打开问题
        
        Args:
            issue_id: 问题ID
            reason: 重新打开原因
            user: 操作用户
            
        Returns:
            更新后的问题对象
        """
        issue = await self.issue_service.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        if issue.status != IssueStatus.CLOSED:
            raise ValueError(f"Only closed issues can be reopened")
        
        # 更新状态
        issue.status = IssueStatus.OPEN
        issue.resolution = {}
        issue.resolution_photos = []
        issue.resolved_at = None
        issue.resolved_by = ""
        issue.confirmed_at = None
        issue.confirmed_by = ""
        
        # 添加重新打开的备注
        issue.description = f"{issue.description}\n\n[重新打开] {reason} (由 {user} 于 {datetime.utcnow().isoformat()} 重新打开)"
        
        if hasattr(self.issue_service.storage, 'save'):
            self.issue_service.storage.save(issue)
        
        return issue
