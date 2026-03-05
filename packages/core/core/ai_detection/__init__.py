# -*- coding: utf-8 -*-
"""
NeuralSite AI质量检测模块

功能：
1. 照片分类 - 施工部位、施工阶段、问题类型
2. 缺陷检测 - 裂缝、破损、钢筋外露、不平整
3. 可疑度评分 - 0-100分，分类置信度
4. 人机协作工作流 - AI初筛 → 人工确认 → 反馈闭环
"""

from .models import (
    ConstructionPart, ConstructionPhase, DefectType, ReviewStatus,
    BoundingBox, DetectionResult, ClassificationResult,
    InspectionTask, BatchDetectionResult
)

from .classifier import ImageClassifier, create_classifier

from .detector import DefectDetector, create_detector

from .scorer import SuspicionScorer, create_scorer

from .workflow import InspectionWorkflow, create_workflow


__version__ = "1.0.0"
__author__ = "NeuralSite Team"


__all__ = [
    # 模型
    'ConstructionPart', 'ConstructionPhase', 'DefectType', 'ReviewStatus',
    'BoundingBox', 'DetectionResult', 'ClassificationResult',
    'InspectionTask', 'BatchDetectionResult',
    
    # 分类器
    'ImageClassifier', 'create_classifier',
    
    # 检测器
    'DefectDetector', 'create_detector',
    
    # 评分器
    'SuspicionScorer', 'create_scorer',
    
    # 工作流
    'InspectionWorkflow', 'create_workflow',
]
