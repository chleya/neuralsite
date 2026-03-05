# -*- coding: utf-8 -*-
"""
NeuralSite Core
公路参数化几何计算引擎
"""

from .engine import NeuralSiteEngine, Coordinate3D, LODConfig, create_engine_from_json
from .geometry import (
    HorizontalAlignment, VerticalAlignment, CrossSectionCalculator,
    LineElement, CircularCurveElement, SpiralCurveElement,
    VerticalCurveElement, CrossSectionTemplate
)

# AI质量检测模块
from .ai_detection import (
    # 模型
    ConstructionPart, ConstructionPhase, DefectType, ReviewStatus,
    BoundingBox, DetectionResult, ClassificationResult,
    InspectionTask, BatchDetectionResult,
    # 组件
    ImageClassifier, create_classifier,
    DefectDetector, create_detector,
    SuspicionScorer, create_scorer,
    InspectionWorkflow, create_workflow,
)


__version__ = "1.0.0"
__author__ = "NeuralSite Team"


__all__ = [
    'NeuralSiteEngine', 'Coordinate3D', 'LODConfig', 'create_engine_from_json',
    'HorizontalAlignment', 'VerticalAlignment', 'CrossSectionCalculator',
    'LineElement', 'CircularCurveElement', 'SpiralCurveElement',
    'VerticalCurveElement', 'CrossSectionTemplate',
    # AI检测模块
    'ConstructionPart', 'ConstructionPhase', 'DefectType', 'ReviewStatus',
    'BoundingBox', 'DetectionResult', 'ClassificationResult',
    'InspectionTask', 'BatchDetectionResult',
    'ImageClassifier', 'create_classifier',
    'DefectDetector', 'create_detector',
    'SuspicionScorer', 'create_scorer',
    'InspectionWorkflow', 'create_workflow',
]
