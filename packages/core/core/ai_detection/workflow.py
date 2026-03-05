# -*- coding: utf-8 -*-
"""
AI质量检测 - 人机协作工作流
实现 AI初筛 → 人工确认 → 反馈闭环
"""

import cv2
import numpy as np
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import sys
sys.path.insert(0, '.')

from .models import (
    InspectionTask, DetectionResult, ClassificationResult,
    ReviewStatus, DefectType, BatchDetectionResult
)
from .classifier import ImageClassifier
from .detector import DefectDetector
from .scorer import SuspicionScorer


class InspectionWorkflow:
    """检测工作流"""
    
    def __init__(
        self,
        classifier: Optional[ImageClassifier] = None,
        detector: Optional[DefectDetector] = None,
        scorer: Optional[SuspicionScorer] = None
    ):
        """
        初始化工作流
        
        Args:
            classifier: 图像分类器
            detector: 缺陷检测器
            scorer: 评分器
        """
        self.classifier = classifier or ImageClassifier()
        self.detector = detector or DefectDetector()
        self.scorer = scorer or SuspicionScorer()
        
        # 任务存储 (内存中)
        self._tasks: Dict[str, InspectionTask] = {}
        
        # 回调函数
        self._on_task_created: Optional[Callable] = None
        self._on_task_reviewed: Optional[Callable] = None
    
    def set_task_created_callback(self, callback: Callable[[InspectionTask], None]):
        """设置任务创建回调"""
        self._on_task_created = callback
    
    def set_task_reviewed_callback(self, callback: Callable[[InspectionTask], None]):
        """设置任务审核完成回调"""
        self._on_task_reviewed = callback
    
    def process_image(
        self,
        image_path: str = "",
        image_data: Optional[bytes] = None,
        project_id: Optional[int] = None,
        location: str = "",
        inspector_id: Optional[str] = None
    ) -> InspectionTask:
        """
        处理单张图像
        
        Args:
            image_path: 图像路径
            image_data: 图像数据
            project_id: 项目ID
            location: 位置描述
            inspector_id: 巡检员ID
            
        Returns:
            InspectionTask: 检测任务
        """
        # 加载图像
        if image_path:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图像: {image_path}")
        elif image_data:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("无法解码图像数据")
        else:
            raise ValueError("必须提供 image_path 或 image_data")
        
        # 创建任务
        task = InspectionTask(
            image_path=image_path,
            image_data=image_data,
            project_id=project_id,
            location=location,
            inspector_id=inspector_id
        )
        
        # 步骤1: 图像分类
        task.classification = self.classifier.classify(image)
        
        # 步骤2: 缺陷检测
        task.detections = self.detector.detect(image)
        
        # 步骤3: 更新审核状态
        if self.scorer.should_require_review(task):
            task.status = ReviewStatus.PENDING
        else:
            # 低风险直接通过
            task.status = ReviewStatus.APPROVED
        
        # 存储任务
        self._tasks[task.task_id] = task
        
        # 触发回调
        if self._on_task_created:
            self._on_task_created(task)
        
        return task
    
    def process_batch(
        self,
        image_paths: List[str] = None,
        image_data_list: List[bytes] = None,
        project_id: Optional[int] = None,
        location: str = "",
        inspector_id: Optional[str] = None
    ) -> BatchDetectionResult:
        """
        批量处理图像
        
        Args:
            image_paths: 图像路径列表
            image_data_list: 图像数据列表
            project_id: 项目ID
            location: 位置描述
            inspector_id: 巡检员ID
            
        Returns:
            BatchDetectionResult: 批量检测结果
        """
        result = BatchDetectionResult()
        
        paths = image_paths or []
        data_list = image_data_list or []
        
        # 合并处理
        items = [(p, None) for p in paths] + [(None, d) for d in data_list]
        
        for item_path, item_data in items:
            try:
                task = self.process_image(
                    image_path=item_path or "",
                    image_data=item_data,
                    project_id=project_id,
                    location=location,
                    inspector_id=inspector_id
                )
                result.tasks.append(task)
            except Exception as e:
                print(f"处理图像失败: {e}")
        
        # 统计
        result.total = len(result.tasks)
        result.with_defects = sum(1 for t in result.tasks if t.has_defects)
        result.pending_review = sum(1 for t in result.tasks if t.status == ReviewStatus.PENDING)
        result.approved = sum(1 for t in result.tasks if t.status == ReviewStatus.APPROVED)
        result.rejected = sum(1 for t in result.tasks if t.status == ReviewStatus.REJECTED)
        
        return result
    
    def review_task(
        self,
        task_id: str,
        reviewer_id: str,
        approved: bool,
        comment: str = ""
    ) -> InspectionTask:
        """
        审核任务
        
        Args:
            task_id: 任务ID
            reviewer_id: 审核员ID
            approved: 是否通过
            comment: 审核意见
            
        Returns:
            InspectionTask: 更新后的任务
        """
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self._tasks[task_id]
        
        task.status = ReviewStatus.APPROVED if approved else ReviewStatus.REJECTED
        task.reviewer_id = reviewer_id
        task.review_comment = comment
        task.reviewed_at = datetime.now()
        
        # 触发回调
        if self._on_task_reviewed:
            self._on_task_reviewed(task)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[InspectionTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def get_tasks_by_status(self, status: ReviewStatus) -> List[InspectionTask]:
        """获取指定状态的任务"""
        return [t for t in self._tasks.values() if t.status == status]
    
    def get_pending_tasks(self) -> List[InspectionTask]:
        """获取待审核任务"""
        return self.get_tasks_by_status(ReviewStatus.PENDING)
    
    def get_rejected_tasks(self) -> List[InspectionTask]:
        """获取已驳回任务"""
        return self.get_tasks_by_status(ReviewStatus.REJECTED)
    
    def get_approved_tasks(self) -> List[InspectionTask]:
        """获取已通过任务"""
        return self.get_tasks_by_status(ReviewStatus.APPROVED)
    
    def get_tasks_by_project(self, project_id: int) -> List[InspectionTask]:
        """获取指定项目的任务"""
        return [t for t in self._tasks.values() if t.project_id == project_id]
    
    def get_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            project_id: 项目ID过滤
            
        Returns:
            Dict: 统计信息
        """
        tasks = self._tasks.values()
        if project_id is not None:
            tasks = [t for t in tasks if t.project_id == project_id]
        
        tasks = list(tasks)
        
        stats = {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t.status == ReviewStatus.PENDING),
            "approved": sum(1 for t in tasks if t.status == ReviewStatus.APPROVED),
            "rejected": sum(1 for t in tasks if t.status == ReviewStatus.REJECTED),
            "with_defects": sum(1 for t in tasks if t.has_defects),
            "avg_score": 0.0
        }
        
        if tasks:
            scores = [self.scorer.score_task(t) for t in tasks]
            stats["avg_score"] = round(sum(scores) / len(scores), 2)
        
        return stats
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def clear_all_tasks(self):
        """清空所有任务"""
        self._tasks.clear()


def create_workflow(
    classifier: Optional[ImageClassifier] = None,
    detector: Optional[DefectDetector] = None,
    scorer: Optional[SuspicionScorer] = None
) -> InspectionWorkflow:
    """创建工作流实例"""
    return InspectionWorkflow(
        classifier=classifier,
        detector=detector,
        scorer=scorer
    )
