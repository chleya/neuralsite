# NeuralSite 问题服务
# 问题CRUD + 状态流转 + AI初筛占位

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from api.deps import CurrentUser, NotFoundError
from models.p0_models import (
    Issue, IssueCreate, IssueUpdate, IssueResponse,
    IssueType, IssueSeverity, IssueStatus, SyncStatus, PhotoRecord
)


# ==================== AI初筛服务 ====================

class AIScreeningService:
    """AI问题初筛服务"""
    
    @staticmethod
    def screen_issue(issue_data: IssueCreate) -> Dict[str, Any]:
        """
        AI初筛问题
        
        这是一个占位实现，实际需要：
        1. 分析问题描述和照片
        2. 判断风险等级
        3. 给出整改建议
        
        Args:
            issue_data: 问题创建数据
            
        Returns:
            初筛结果字典
        """
        # 基于严重程度的初步判断
        severity_to_risk = {
            IssueSeverity.CRITICAL: "high",
            IssueSeverity.MAJOR: "medium",
            IssueSeverity.MINOR: "low"
        }
        
        risk_level = severity_to_risk.get(issue_data.severity, "medium")
        
        # 基于问题类型的建议
        type_to_category = {
            IssueType.QUALITY: "质量缺陷",
            IssueType.SAFETY: "安全隐患",
            IssueType.PROGRESS: "进度问题"
        }
        
        category = type_to_category.get(issue_data.issue_type, "其他")
        
        # 生成整改建议
        suggestions = {
            "high": "建议立即处理，24小时内完成整改",
            "medium": "建议计划整改，一周内完成",
            "low": "纳入例行维护，定期处理"
        }
        
        # TODO: 实际实现应调用AI模型分析照片和描述
        # return {
        #     "category": category,
        #     "risk_level": risk_level,
        #     "suggestion": suggestions.get(risk_level),
        #     "confidence": 0.75,  # AI置信度
        #     "keywords": [],  # 提取的关键词
        #     "related_standards": []  # 相关规范
        # }
        
        return {
            "category": category,
            "risk_level": risk_level,
            "suggestion": suggestions.get(risk_level, "按计划整改"),
            "confidence": 0.7,
            "keywords": [],
            "related_standards": []
        }


# ==================== 问题服务类 ====================

class IssueService:
    """问题服务"""
    
    def __init__(self, db: Session, current_user: Optional[CurrentUser] = None):
        self.db = db
        self.current_user = current_user
    
    # ==================== 创建 ====================
    
    def create_issue(self, issue_data: IssueCreate) -> Issue:
        """
        创建问题
        
        完整流程:
        1. 创建问题记录
        2. AI初筛（自动）
        3. 返回创建结果
        """
        # AI初筛
        ai_screening = AIScreeningService.screen_issue(issue_data)
        
        # 创建问题记录
        issue = Issue(
            issue_id=uuid.uuid4(),
            project_id=issue_data.project_id,
            issue_type=issue_data.issue_type.value,
            title=issue_data.title,
            description=issue_data.description,
            severity=issue_data.severity.value if isinstance(issue_data.severity, IssueSeverity) else issue_data.severity,
            station=issue_data.station,
            station_display=issue_data.station_display,
            latitude=issue_data.latitude,
            longitude=issue_data.longitude,
            location_description=issue_data.location_description,
            photo_ids=issue_data.photo_ids or [],
            status=IssueStatus.OPEN.value,
            reported_by=issue_data.reported_by,
            reported_at=datetime.utcnow(),
            assigned_to=issue_data.assigned_to,
            deadline=issue_data.deadline,
            ai_screening=ai_screening,
            sync_status=SyncStatus.PENDING if issue_data.local_id else SyncStatus.SYNCED,
            local_id=issue_data.local_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    # ==================== 查询 ====================
    
    def get_issue(self, issue_id: uuid.UUID) -> Issue:
        """获取单个问题"""
        issue = self.db.query(Issue).filter(Issue.issue_id == issue_id).first()
        if not issue:
            raise NotFoundError("问题", str(issue_id))
        return issue
    
    def list_issues(
        self,
        project_id: Optional[uuid.UUID] = None,
        issue_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        assigned_to: Optional[uuid.UUID] = None,
        reported_by: Optional[uuid.UUID] = None,
        station_start: Optional[float] = None,
        station_end: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Issue]:
        """查询问题列表"""
        query = self.db.query(Issue)
        
        if project_id:
            query = query.filter(Issue.project_id == project_id)
        
        if issue_type:
            query = query.filter(Issue.issue_type == issue_type)
        
        if severity:
            query = query.filter(Issue.severity == severity)
        
        if status:
            status_value = status.value if isinstance(status, IssueStatus) else status
            query = query.filter(Issue.status == status_value)
        
        if assigned_to:
            query = query.filter(Issue.assigned_to == assigned_to)
        
        if reported_by:
            query = query.filter(Issue.reported_by == reported_by)
        
        if station_start is not None and station_end is not None:
            query = query.filter(
                and_(
                    Issue.station >= station_start,
                    Issue.station <= station_end
                )
            )
        elif station_start is not None:
            query = query.filter(Issue.station >= station_start)
        elif station_end is not None:
            query = query.filter(Issue.station <= station_end)
        
        return query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
    
    def count_issues(
        self,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        assigned_to: Optional[uuid.UUID] = None
    ) -> int:
        """统计问题数量"""
        query = self.db.query(Issue)
        
        if project_id:
            query = query.filter(Issue.project_id == project_id)
        if status:
            query = query.filter(Issue.status == status)
        if severity:
            query = query.filter(Issue.severity == severity)
        if assigned_to:
            query = query.filter(Issue.assigned_to == assigned_to)
        
        return query.count()
    
    def get_statistics(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """获取问题统计"""
        # 按状态统计
        status_counts = {}
        for status in IssueStatus:
            count = self.count_issues(project_id=project_id, status=status.value)
            status_counts[status.value] = count
        
        # 按严重程度统计
        severity_counts = {}
        for severity in ["critical", "major", "minor"]:
            count = self.count_issues(project_id=project_id, severity=severity)
            severity_counts[severity] = count
        
        # 按类型统计
        type_counts = {}
        for issue_type in IssueType:
            count = self.list_issues(
                project_id=project_id,
                issue_type=issue_type.value,
                limit=10000
            )
            type_counts[issue_type.value] = len(count)
        
        return {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "by_severity": severity_counts,
            "by_type": type_counts
        }
    
    # ==================== 更新 ====================
    
    def update_issue(
        self,
        issue_id: uuid.UUID,
        issue_update: IssueUpdate
    ) -> Issue:
        """更新问题"""
        issue = self.get_issue(issue_id)
        
        if issue_update.title is not None:
            issue.title = issue_update.title
        if issue_update.description is not None:
            issue.description = issue_update.description
        if issue_update.severity is not None:
            issue.severity = issue_update.severity.value if isinstance(issue_update.severity, IssueSeverity) else issue_update.severity
        if issue_update.status is not None:
            issue.status = issue_update.status.value if isinstance(issue_update.status, IssueStatus) else issue_update.status
        if issue_update.assigned_to is not None:
            issue.assigned_to = issue_update.assigned_to
        if issue_update.resolved_by is not None:
            issue.resolved_by = issue_update.resolved_by
        if issue_update.resolution_note is not None:
            issue.resolution_note = issue_update.resolution_note
        if issue_update.deadline is not None:
            issue.deadline = issue_update.deadline
        if issue_update.photo_ids is not None:
            issue.photo_ids = issue_update.photo_ids
        
        issue.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    # ==================== 状态流转 ====================
    
    def assign_issue(
        self,
        issue_id: uuid.UUID,
        assigned_to: uuid.UUID
    ) -> Issue:
        """
        分配问题给责任人
        
        状态: OPEN -> IN_PROGRESS
        """
        issue = self.get_issue(issue_id)
        
        if issue.status != IssueStatus.OPEN.value:
            raise ValueError(f"只有OPEN状态的问题可以分配，当前状态: {issue.status}")
        
        issue.assigned_to = assigned_to
        issue.assigned_at = datetime.utcnow()
        issue.status = IssueStatus.IN_PROGRESS.value
        issue.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    def resolve_issue(
        self,
        issue_id: uuid.UUID,
        resolved_by: uuid.UUID,
        resolution_note: str
    ) -> Issue:
        """
        解决问题
        
        状态: IN_PROGRESS -> RESOLVED
        """
        issue = self.get_issue(issue_id)
        
        if issue.status != IssueStatus.IN_PROGRESS.value:
            raise ValueError(f"只有IN_PROGRESS状态的问题可以解决，当前状态: {issue.status}")
        
        issue.resolved_by = resolved_by
        issue.resolved_at = datetime.utcnow()
        issue.resolution_note = resolution_note
        issue.status = IssueStatus.RESOLVED.value
        issue.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    def close_issue(self, issue_id: uuid.UUID) -> Issue:
        """
        闭环问题
        
        状态: RESOLVED -> CLOSED
        """
        issue = self.get_issue(issue_id)
        
        if issue.status != IssueStatus.RESOLVED.value:
            raise ValueError(f"只有RESOLVED状态的问题可以闭环，当前状态: {issue.status}")
        
        issue.status = IssueStatus.CLOSED.value
        issue.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    def reopen_issue(self, issue_id: uuid.UUID, reason: str) -> Issue:
        """
        重新打开问题
        
        状态: RESOLVED/CLOSED -> OPEN
        """
        issue = self.get_issue(issue_id)
        
        if issue.status not in [IssueStatus.RESOLVED.value, IssueStatus.CLOSED.value]:
            raise ValueError(f"只有RESOLVED或CLOSED状态的问题可以重新打开，当前状态: {issue.status}")
        
        # 记录重新打开的原因
        issue.resolution_note = f"重新打开 - 原因: {reason}"
        issue.status = IssueStatus.OPEN.value
        issue.resolved_by = None
        issue.resolved_at = None
        issue.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    # ==================== 关联照片 ====================
    
    def add_photo(self, issue_id: uuid.UUID, photo_id: uuid.UUID) -> Issue:
        """为问题添加关联照片"""
        issue = self.get_issue(issue_id)
        
        # 验证照片存在
        photo = self.db.query(PhotoRecord).filter(PhotoRecord.photo_id == photo_id).first()
        if not photo:
            raise NotFoundError("照片", str(photo_id))
        
        # 添加到关联列表
        photo_ids = issue.photo_ids or []
        if photo_id not in photo_ids:
            photo_ids.append(photo_id)
            issue.photo_ids = photo_ids
            issue.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(issue)
        
        return issue
    
    def remove_photo(self, issue_id: uuid.UUID, photo_id: uuid.UUID) -> Issue:
        """移除问题的关联照片"""
        issue = self.get_issue(issue_id)
        
        photo_ids = issue.photo_ids or []
        if photo_id in photo_ids:
            photo_ids.remove(photo_id)
            issue.photo_ids = photo_ids
            issue.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(issue)
        
        return issue
    
    # ==================== AI初筛 ====================
    
    def rerun_ai_screening(self, issue_id: uuid.UUID) -> Issue:
        """重新运行AI初筛"""
        issue = self.get_issue(issue_id)
        
        # 构建IssueCreate用于AI初筛
        issue_data = IssueCreate(
            project_id=issue.project_id,
            issue_type=IssueType(issue.issue_type),
            title=issue.title,
            description=issue.description,
            severity=IssueSeverity(issue.severity),
            station=issue.station,
            station_display=issue.station_display,
            latitude=issue.latitude,
            longitude=issue.longitude,
            location_description=issue.location_description
        )
        
        # 重新运行AI初筛
        ai_screening = AIScreeningService.screen_issue(issue_data)
        
        issue.ai_screening = ai_screening
        issue.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    # ==================== 同步相关 ====================
    
    def get_pending_sync_issues(
        self,
        limit: int = 100
    ) -> List[Issue]:
        """获取待同步的问题"""
        return self.db.query(Issue).filter(
            and_(
                Issue.sync_status == SyncStatus.PENDING,
                Issue.local_id.isnot(None)
            )
        ).limit(limit).all()
    
    def mark_as_synced(self, issue_id: uuid.UUID) -> None:
        """标记为已同步"""
        issue = self.get_issue(issue_id)
        issue.sync_status = SyncStatus.SYNCED
        issue.local_id = None
        issue.updated_at = datetime.utcnow()
        self.db.commit()
