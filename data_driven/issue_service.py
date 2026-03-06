# -*- coding: utf-8 -*-
"""
问题跟踪服务

提供问题的创建、更新、统计等功能
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio

from .issue_models import Issue, IssueUpdate, IssueStatus, IssueSeverity


class IssueService:
    """问题跟踪服务"""
    
    def __init__(self, storage, lineage, chain):
        """
        初始化问题服务
        
        Args:
            storage: 存储适配器（需要提供save, get, get_all, delete方法）
            lineage: 血缘记录器（需要提供record方法）
            chain: 区块链存证（需要提供submit方法）
        """
        self.storage = storage
        self.lineage = lineage
        self.chain = chain
    
    async def create_issue(self, issue: Issue) -> Issue:
        """
        创建问题
        
        Args:
            issue: 问题对象
            
        Returns:
            创建后的问题对象
        """
        # 1. 记录血缘
        if hasattr(self.lineage, 'record'):
            self.lineage.record(
                data_id=issue.id,
                data_type='issue',
                source_type='manual'
            )
        
        # 2. 关键数据上链
        if hasattr(self.chain, 'submit'):
            from .blockchain import HashComputer
            issue_dict = issue.to_dict()
            hash_val = HashComputer.compute_data_hash(issue_dict, 'issue')
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.chain.submit,
                issue.id,
                hash_val,
                'issue',
                issue.reported_by,
                'reporter',
                issue.project_id
            )
        
        # 3. 保存
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
    async def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        获取问题详情
        
        Args:
            issue_id: 问题ID
            
        Returns:
            问题对象，如果不存在则返回None
        """
        if hasattr(self.storage, 'get'):
            data = self.storage.get(issue_id)
            if data:
                if isinstance(data, Issue):
                    return data
                return Issue.from_dict(data)
        return None
    
    async def list_issues(self, project_id: str = None, 
                         status: IssueStatus = None,
                         assigned_to: str = None) -> List[Issue]:
        """
        列出问题
        
        Args:
            project_id: 项目ID过滤
            status: 状态过滤
            assigned_to: 负责人过滤
            
        Returns:
            问题列表
        """
        issues = []
        
        if hasattr(self.storage, 'get_all'):
            all_issues = self.storage.get_all()
        elif hasattr(self.storage, 'query'):
            all_issues = self.storage.query({})
        else:
            return []
        
        for item in all_issues:
            if isinstance(item, Issue):
                issue = item
            else:
                issue = Issue.from_dict(item)
            
            # 过滤条件
            if project_id and issue.project_id != project_id:
                continue
            if status and issue.status != status:
                continue
            if assigned_to and issue.assigned_to != assigned_to:
                continue
                
            issues.append(issue)
        
        return issues
    
    async def update_status(self, issue_id: str, status: IssueStatus,
                          comment: str, user: str) -> Issue:
        """
        更新问题状态
        
        Args:
            issue_id: 问题ID
            status: 新状态
            comment: 更新说明
            user: 操作用户
            
        Returns:
            更新后的问题对象
        """
        # 1. 获取原问题
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        previous_status = issue.status
        
        # 2. 记录更新
        update = IssueUpdate(
            issue_id=issue_id,
            status=status,
            comment=comment,
            updated_by=user,
            previous_status=previous_status,
            changes={"status": {"from": previous_status.value, "to": status.value}}
        )
        
        # 保存更新记录
        if hasattr(self.storage, 'save_update'):
            self.storage.save_update(update)
        elif hasattr(self.storage, 'save'):
            # 保存到更新记录集合
            updates = getattr(self.storage, '_updates', [])
            updates.append(update.to_dict())
            self.storage._updates = updates
        
        # 3. 上链存证
        if hasattr(self.chain, 'submit'):
            from .blockchain import HashComputer
            
            chain_data = {
                "issue_id": issue_id,
                "previous_status": previous_status.value,
                "new_status": status.value,
                "comment": comment,
                "updated_by": user,
                "updated_at": datetime.utcnow().isoformat()
            }
            hash_val = HashComputer.compute_data_hash(chain_data, 'issue_update')
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.chain.submit,
                issue_id,
                hash_val,
                'issue_update',
                user,
                'operator',
                issue.project_id
            )
        
        # 4. 更新状态
        issue.status = status
        
        # 如果是解决状态，记录解决时间
        if status == IssueStatus.RESOLVED:
            issue.resolved_at = datetime.utcnow()
            issue.resolved_by = user
        
        # 如果是关闭状态，记录确认时间
        if status == IssueStatus.CLOSED:
            issue.confirmed_at = datetime.utcnow()
            issue.confirmed_by = user
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
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
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        issue.assigned_to = assignee
        
        # 如果是待处理状态，改为处理中
        if issue.status == IssueStatus.OPEN:
            issue.status = IssueStatus.IN_PROGRESS
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
    async def resolve(self, issue_id: str, resolution: dict, 
                    user: str) -> Issue:
        """
        解决问题
        
        Args:
            issue_id: 问题ID
            resolution: 整改措施 {"photos": [...], "description": "..."}
            user: 操作用户
            
        Returns:
            更新后的问题对象
        """
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        # 添加整改信息
        issue.resolution = resolution
        if resolution.get("photos"):
            issue.resolution_photos.extend(resolution["photos"])
        
        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.utcnow()
        issue.resolved_by = user
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
    async def confirm_resolution(self, issue_id: str, confirmed: bool,
                                user: str, comment: str = "") -> Issue:
        """
        确认整改结果
        
        Args:
            issue_id: 问题ID
            confirmed: 是否确认通过
            user: 操作用户
            comment: 确认意见
            
        Returns:
            更新后的问题对象
        """
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        if confirmed:
            # 确认通过，关闭问题
            issue.status = IssueStatus.CLOSED
            issue.confirmed_at = datetime.utcnow()
            issue.confirmed_by = user
        else:
            # 退回重新整改
            issue.status = IssueStatus.IN_PROGRESS
            issue.resolution = {}
            issue.resolution_photos = []
            issue.resolved_at = None
            issue.resolved_by = ""
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
    async def get_statistics(self, project_id: str) -> dict:
        """
        获取问题统计
        
        Args:
            project_id: 项目ID
            
        Returns:
            统计结果字典
        """
        issues = await self.list_issues(project_id=project_id)
        
        # 初始化统计
        stats = {
            "total": len(issues),
            "by_status": {},
            "by_severity": {},
            "by_type": {},
            "open_count": 0,
            "in_progress_count": 0,
            "resolved_count": 0,
            "closed_count": 0,
        }
        
        for issue in issues:
            # 按状态统计
            status_key = issue.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            if issue.status == IssueStatus.OPEN:
                stats["open_count"] += 1
            elif issue.status == IssueStatus.IN_PROGRESS:
                stats["in_progress_count"] += 1
            elif issue.status == IssueStatus.RESOLVED:
                stats["resolved_count"] += 1
            elif issue.status == IssueStatus.CLOSED:
                stats["closed_count"] += 1
            
            # 按严重程度统计
            severity_key = issue.severity.value
            stats["by_severity"][severity_key] = stats["by_severity"].get(severity_key, 0) + 1
            
            # 按类型统计
            if issue.issue_type:
                stats["by_type"][issue.issue_type] = stats["by_type"].get(issue.issue_type, 0) + 1
        
        return stats
    
    async def add_photo(self, issue_id: str, photo_id: str) -> Issue:
        """
        添加问题照片
        
        Args:
            issue_id: 问题ID
            photo_id: 照片ID
            
        Returns:
            更新后的问题对象
        """
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        if photo_id not in issue.photos:
            issue.photos.append(photo_id)
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
    
    async def add_resolution_photo(self, issue_id: str, photo_id: str) -> Issue:
        """
        添加整改照片
        
        Args:
            issue_id: 问题ID
            photo_id: 照片ID
            
        Returns:
            更新后的问题对象
        """
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        if photo_id not in issue.resolution_photos:
            issue.resolution_photos.append(photo_id)
        
        if hasattr(self.storage, 'save'):
            self.storage.save(issue)
        
        return issue
