# -*- coding: utf-8 -*-
"""
AI质量检测 - 可疑度评分器
对检测结果进行综合评分
"""

import numpy as np
from typing import List, Dict, Any
import sys
sys.path.insert(0, '.')

from .models import (
    DetectionResult, ClassificationResult, InspectionTask, 
    DefectType, ReviewStatus
)


class SuspicionScorer:
    """可疑度评分器"""
    
    # 缺陷类型权重
    DEFECT_WEIGHTS = {
        DefectType.CRACK: 1.2,           # 裂缝权重较高
        DefectType.REBAR_EXPOSED: 1.3,   # 钢筋外露最严重
        DefectType.SPALLING: 1.1,        # 破损
        DefectType.UNEVENNESS: 0.9,      # 不平整
        DefectType.WATER_LEAKAGE: 1.1,   # 渗漏水
        DefectType.DISCOLORATION: 0.5,   # 变色/污染
        DefectType.DEFORMATION: 1.2,      # 变形
        DefectType.NONE: 0.0,
    }
    
    # 严重程度等级
    SEVERITY_MULTIPLIERS = {
        "normal": 0.6,
        "warning": 1.0,
        "critical": 1.5,
    }
    
    # 阈值配置
    THRESHOLDS = {
        "high": 80,      # 高风险阈值
        "medium": 50,    # 中风险阈值
        "low": 30,       # 低风险阈值
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化评分器
        
        Args:
            config: 自定义配置
        """
        if config:
            self.DEFECT_WEIGHTS = config.get("defect_weights", self.DEFECT_WEIGHTS)
            self.SEVERITY_MULTIPLIERS = config.get("severity_multipliers", self.SEVERITY_MULTIPLIERS)
            self.THRESHOLDS = config.get("thresholds", self.THRESHOLDS)
    
    def score_detection(self, detection: DetectionResult) -> int:
        """
        对单个检测结果评分
        
        Args:
            detection: 检测结果
            
        Returns:
            int: 可疑度评分 (0-100)
        """
        # 基础分 = 原始可疑度评分
        base_score = detection.suspicion_score
        
        # 权重乘数
        defect_weight = self.DEFECT_WEIGHTS.get(detection.defect_type, 1.0)
        
        # 严重程度乘数
        severity_mult = self.SEVERITY_MULTIPLIERS.get(detection.severity, 1.0)
        
        # 置信度乘数
        confidence_mult = 0.5 + (detection.confidence * 0.5)  # 0.5 - 1.5
        
        # 综合评分
        score = base_score * defect_weight * severity_mult * confidence_mult
        
        # 限制在0-100
        return min(int(score), 100)
    
    def score_task(self, task: InspectionTask) -> int:
        """
        对整个检测任务评分
        
        Args:
            task: 检测任务
            
        Returns:
            int: 任务综合可疑度评分 (0-100)
        """
        if not task.classification:
            return 0
        
        # 分类置信度因子 (0.7 - 1.0)
        classification_factor = 0.7 + (task.classification.confidence * 0.3)
        
        if not task.detections:
            # 无缺陷，基于分类质量调整
            return int((1 - classification_factor) * 30)
        
        # 计算所有检测结果的加权平均分
        scores = []
        for detection in task.detections:
            score = self.score_detection(detection)
            # 考虑位置（如果有多个缺陷，位置越集中越严重）
            scores.append(score)
        
        # 平均分
        avg_score = np.mean(scores)
        
        # 多缺陷加成 (检测到多个缺陷，提高评分)
        if len(task.detections) > 1:
            multi_defect_bonus = min(len(task.detections) * 5, 20)
        else:
            multi_defect_bonus = 0
        
        # 综合评分
        final_score = (avg_score + multi_defect_bonus) * classification_factor
        
        return min(int(final_score), 100)
    
    def get_risk_level(self, score: int) -> str:
        """
        根据评分获取风险等级
        
        Args:
            score: 可疑度评分
            
        Returns:
            str: risk level (low/medium/high/critical)
        """
        if score >= self.THRESHOLDS["high"]:
            return "critical"
        elif score >= self.THRESHOLDS["medium"]:
            return "high"
        elif score >= self.THRESHOLDS["low"]:
            return "medium"
        else:
            return "low"
    
    def should_require_review(self, task: InspectionTask) -> bool:
        """
        判断是否需要人工审核
        
        Args:
            task: 检测任务
            
        Returns:
            bool: 是否需要审核
        """
        # 高风险或多个缺陷
        score = self.score_task(task)
        risk_level = self.get_risk_level(score)
        
        # 需要审核的情况：
        # 1. 风险等级为 high 或 critical
        # 2. 评分 >= 60
        # 3. 检测到多个不同类型的缺陷
        
        if risk_level in ("high", "critical"):
            return True
        
        if score >= 60:
            return True
        
        # 检查多种缺陷类型
        defect_types = set(d.defect_type for d in task.detections)
        if len(defect_types) >= 2:
            return True
        
        return False
    
    def generate_review_recommendation(self, task: InspectionTask) -> Dict[str, Any]:
        """
        生成审核建议
        
        Args:
            task: 检测任务
            
        Returns:
            Dict: 审核建议
        """
        score = self.score_task(task)
        risk_level = self.get_risk_level(score)
        
        recommendation = {
            "score": score,
            "risk_level": risk_level,
            "requires_review": self.should_require_review(task),
            "defect_summary": [],
            "priority": "normal"
        }
        
        # 缺陷摘要
        for detection in task.detections:
            recommendation["defect_summary"].append({
                "type": detection.defect_type.value,
                "score": detection.suspicion_score,
                "severity": detection.severity,
                "description": detection.description
            })
        
        # 优先级
        if risk_level == "critical":
            recommendation["priority"] = "urgent"
        elif risk_level == "high":
            recommendation["priority"] = "high"
        
        # 建议
        if risk_level in ("critical", "high"):
            recommendation["suggestion"] = "建议立即现场复核"
        elif risk_level == "medium":
            recommendation["suggestion"] = "建议尽快安排检查"
        else:
            recommendation["suggestion"] = "可安排常规巡检"
        
        return recommendation
    
    def update_detection_scores(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        批量更新检测结果的评分
        
        Args:
            detections: 检测结果列表
            
        Returns:
            List[DetectionResult]: 更新后的结果
        """
        for detection in detections:
            detection.suspicion_score = self.score_detection(detection)
        return detections


def create_scorer(config: Dict[str, Any] = None) -> SuspicionScorer:
    """创建评分器实例"""
    return SuspicionScorer(config=config)
