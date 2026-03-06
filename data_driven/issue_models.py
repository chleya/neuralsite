# -*- coding: utf-8 -*-
"""
问题数据模型

包含问题Issue和IssueUpdate模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


class IssueStatus(Enum):
    """问题状态"""
    OPEN = "open"           # 待处理
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"   # 已解决
    CLOSED = "closed"       # 已关闭


class IssueSeverity(Enum):
    """严重程度"""
    LOW = "low"         # 轻微
    MEDIUM = "medium"   # 一般
    HIGH = "high"       # 严重
    CRITICAL = "critical"  # 紧急


@dataclass
class Issue:
    """问题数据模型"""
    id: str = ""
    project_id: str = ""
    station: str = ""  # 桩号
    location: dict = field(default_factory=lambda: {"lat": None, "lon": None})  # 坐标 {lat, lon}
    
    title: str = ""
    description: str = ""
    issue_type: str = ""  # 质量问题/安全问题/进度问题
    
    severity: IssueSeverity = IssueSeverity.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    
    reported_by: str = ""
    reported_at: datetime = None
    
    assigned_to: str = ""
    due_date: datetime = None
    
    photos: List[str] = field(default_factory=list)  # 关联照片IDs
    
    # 整改相关字段
    resolution: dict = field(default_factory=dict)  # 整改措施
    resolution_photos: List[str] = field(default_factory=list)  # 整改照片
    resolved_at: datetime = None
    resolved_by: str = ""
    confirmed_at: datetime = None
    confirmed_by: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.reported_at:
            self.reported_at = datetime.utcnow()
        if self.location is None:
            self.location = {"lat": None, "lon": None}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "station": self.station,
            "location": self.location,
            "title": self.title,
            "description": self.description,
            "issue_type": self.issue_type,
            "severity": self.severity.value if isinstance(self.severity, IssueSeverity) else self.severity,
            "status": self.status.value if isinstance(self.status, IssueStatus) else self.status,
            "reported_by": self.reported_by,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "photos": self.photos,
            "resolution": self.resolution,
            "resolution_photos": self.resolution_photos,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "confirmed_by": self.confirmed_by,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Issue":
        """从字典创建"""
        # 处理枚举类型
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = IssueSeverity(data["severity"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = IssueStatus(data["status"])
        
        # 处理datetime字段
        for field_name in ["reported_at", "due_date", "resolved_at", "confirmed_at"]:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)


@dataclass
class IssueUpdate:
    """问题更新记录"""
    issue_id: str
    status: IssueStatus
    comment: str
    updated_by: str
    updated_at: datetime = None
    
    # 额外字段
    previous_status: IssueStatus = None
    changes: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "issue_id": self.issue_id,
            "status": self.status.value if isinstance(self.status, IssueStatus) else self.status,
            "comment": self.comment,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "previous_status": self.previous_status.value if isinstance(self.previous_status, IssueStatus) else self.previous_status,
            "changes": self.changes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "IssueUpdate":
        """从字典创建"""
        if "status" in data and isinstance(data["status"], str):
            data["status"] = IssueStatus(data["status"])
        if "previous_status" in data and isinstance(data.get("previous_status"), str):
            data["previous_status"] = IssueStatus(data["previous_status"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)


# 问题类型常量
class IssueType:
    """问题类型常量"""
    QUALITY = "quality"      # 质量问题
    SAFETY = "safety"        # 安全问题
    PROGRESS = "progress"   # 进度问题
    DESIGN = "design"       # 设计问题
    MATERIAL = "material"   # 材料问题
    OTHER = "other"         # 其他
    
    @classmethod
    def all(cls) -> List[str]:
        return [cls.QUALITY, cls.SAFETY, cls.PROGRESS, cls.DESIGN, cls.MATERIAL, cls.OTHER]
