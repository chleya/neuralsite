# -*- coding: utf-8 -*-
"""
AI质量检测模块 - 数据模型定义
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ConstructionPart(str, Enum):
    """施工部位分类"""
    ROAD = "road"           # 路面
    BRIDGE = "bridge"        # 桥梁
    TUNNEL = "tunnel"       # 隧道
    CULVERT = "culvert"     # 涵洞
    DRAINAGE = "drainage"   # 排水设施
    SLOPE = "slope"         # 边坡
    UNKNOWN = "unknown"     # 未知


class ConstructionPhase(str, Enum):
    """施工阶段分类"""
    BEFORE = "before"       # 施工前
    DURING = "during"       # 施工中
    AFTER = "after"         # 施工后
    UNKNOWN = "unknown"     # 未知


class DefectType(str, Enum):
    """问题类型分类"""
    CRACK = "crack"         # 裂缝
    SPALLING = "spalling"   # 破损/剥落
    REBAR_EXPOSED = "rebar_exposed"  # 钢筋外露
    UNEVENNESS = "unevenness"  # 不平整
    WATER_LEAKAGE = "water_leakage"  # 渗漏水
    DISCOLORATION = "discoloration"  # 变色/污染
    DEFORMATION = "deformation"  # 变形
    NONE = "none"           # 无缺陷


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"         # 待审核
    APPROVED = "approved"       # 已确认(合格)
    REJECTED = "rejected"       # 已确认(不合格)
    REVISED = "revised"         # 已修订(重新检测)


@dataclass
class BoundingBox:
    """检测框"""
    x: int          # 左上角x
    y: int          # 左上角y
    width: int      # 宽度
    height: int     # 高度
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> tuple:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }


@dataclass
class DetectionResult:
    """缺陷检测结果"""
    defect_type: DefectType
    confidence: float          # 置信度 0-1
    suspicion_score: int       # 可疑度评分 0-100
    bounding_box: Optional[BoundingBox] = None
    description: str = ""
    severity: str = "normal"   # normal, warning, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "defect_type": self.defect_type.value,
            "confidence": round(self.confidence, 3),
            "suspicion_score": self.suspicion_score,
            "severity": self.severity,
            "description": self.description
        }
        if self.bounding_box:
            result["bounding_box"] = self.bounding_box.to_dict()
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class ClassificationResult:
    """照片分类结果"""
    part: ConstructionPart
    phase: ConstructionPhase
    confidence: float          # 分类置信度 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "part": self.part.value,
            "phase": self.phase.value,
            "confidence": round(self.confidence, 3),
            "metadata": self.metadata
        }


@dataclass
class InspectionTask:
    """检测任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    image_path: str = ""
    image_data: Optional[bytes] = None
    
    # 分类结果
    classification: Optional[ClassificationResult] = None
    
    # 检测结果列表
    detections: List[DetectionResult] = field(default_factory=list)
    
    # 工作流状态
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_id: Optional[str] = None
    review_comment: str = ""
    reviewed_at: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    project_id: Optional[int] = None
    location: str = ""          # 位置描述
    inspector_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "image_path": self.image_path,
            "classification": self.classification.to_dict() if self.classification else None,
            "detections": [d.to_dict() for d in self.detections],
            "status": self.status.value,
            "reviewer_id": self.reviewer_id,
            "review_comment": self.review_comment,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat(),
            "project_id": self.project_id,
            "location": self.location,
            "inspector_id": self.inspector_id
        }
    
    @property
    def has_defects(self) -> bool:
        """是否有检测到缺陷"""
        return len(self.detections) > 0
    
    @property
    def max_suspicion_score(self) -> int:
        """最高可疑度评分"""
        if not self.detections:
            return 0
        return max(d.suspicion_score for d in self.detections)
    
    @property
    def requires_review(self) -> bool:
        """是否需要人工审核"""
        # 可疑度超过阈值或检测到多个缺陷
        return self.max_suspicion_score >= 60 or len(self.detections) >= 2


@dataclass
class BatchDetectionResult:
    """批量检测结果"""
    total: int = 0
    with_defects: int = 0
    pending_review: int = 0
    approved: int = 0
    rejected: int = 0
    tasks: List[InspectionTask] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "with_defects": self.with_defects,
            "pending_review": self.pending_review,
            "approved": self.approved,
            "rejected": self.rejected,
            "tasks": [t.to_dict() for t in self.tasks]
        }
