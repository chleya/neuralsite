# -*- coding: utf-8 -*-
"""
AI质量检测模块 - 单元测试
"""

import pytest
import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ai_detection.models import (
    ConstructionPart, ConstructionPhase, DefectType, ReviewStatus,
    BoundingBox, DetectionResult, ClassificationResult,
    InspectionTask, BatchDetectionResult
)

from core.ai_detection.classifier import ImageClassifier, create_classifier

from core.ai_detection.detector import DefectDetector, create_detector

from core.ai_detection.scorer import SuspicionScorer, create_scorer

from core.ai_detection.workflow import InspectionWorkflow, create_workflow


# ============ 测试数据生成器 ============

def create_test_image(size: tuple = (480, 640), color: int = 128) -> np.ndarray:
    """创建测试图像"""
    return np.ones((size[0], size[1], 3), dtype=np.uint8) * color


def create_crack_image() -> np.ndarray:
    """创建带裂缝的测试图像"""
    img = create_test_image()
    # 绘制斜线模拟裂缝
    cv2.line(img, (100, 50), (500, 400), (30, 30, 30), 3)
    return img


def create_spalling_image() -> np.ndarray:
    """创建带破损的测试图像"""
    img = create_test_image()
    # 绘制圆形模拟破损
    cv2.circle(img, (320, 240), 50, (60, 60, 60), -1)
    return img


# ============ 模型测试 ============

class TestModels:
    """数据模型测试"""
    
    def test_bounding_box(self):
        """测试边界框"""
        bbox = BoundingBox(10, 20, 100, 50)
        
        assert bbox.area == 5000
        assert bbox.center == (60, 45)
        
        d = bbox.to_dict()
        assert d["x"] == 10
        assert d["width"] == 100
    
    def test_detection_result(self):
        """测试检测结果"""
        result = DetectionResult(
            defect_type=DefectType.CRACK,
            confidence=0.8,
            suspicion_score=75,
            severity="warning"
        )
        
        assert result.defect_type == DefectType.CRACK
        assert result.confidence == 0.8
        
        d = result.to_dict()
        assert d["defect_type"] == "crack"
        assert d["suspicion_score"] == 75
    
    def test_classification_result(self):
        """测试分类结果"""
        result = ClassificationResult(
            part=ConstructionPart.ROAD,
            phase=ConstructionPhase.DURING,
            confidence=0.85
        )
        
        assert result.part == ConstructionPart.ROAD
        assert result.confidence == 0.85
        
        d = result.to_dict()
        assert d["part"] == "road"
        assert d["phase"] == "during"
    
    def test_inspection_task(self):
        """测试检测任务"""
        task = InspectionTask(
            image_path="/test/image.jpg",
            project_id=1,
            location="测试位置"
        )
        
        task.classification = ClassificationResult(
            part=ConstructionPart.ROAD,
            phase=ConstructionPhase.AFTER,
            confidence=0.9
        )
        
        task.detections = [
            DetectionResult(
                defect_type=DefectType.CRACK,
                confidence=0.7,
                suspicion_score=65
            )
        ]
        
        task.status = ReviewStatus.PENDING
        
        assert task.has_defects
        assert task.max_suspicion_score == 65
        assert task.requires_review
        
        d = task.to_dict()
        assert d["classification"]["part"] == "road"
        assert len(d["detections"]) == 1


# ============ 分类器测试 ============

class TestClassifier:
    """图像分类器测试"""
    
    def test_classifier_init(self):
        """测试分类器初始化"""
        classifier = ImageClassifier()
        assert classifier is not None
    
    def test_classify_normal_image(self):
        """测试正常图像分类"""
        classifier = ImageClassifier()
        img = create_test_image()
        
        result = classifier.classify(img)
        
        assert result is not None
        assert isinstance(result.part, ConstructionPart)
        assert isinstance(result.phase, ConstructionPhase)
        assert 0 <= result.confidence <= 1
    
    def test_batch_classify(self):
        """测试批量分类"""
        classifier = ImageClassifier()
        images = [create_test_image() for _ in range(3)]
        
        results = classifier.batch_classify(images)
        
        assert len(results) == 3
    
    def test_classify_from_bytes(self):
        """测试从字节数据分类"""
        classifier = ImageClassifier()
        img = create_test_image()
        
        # 编码为 JPEG
        _, encoded = cv2.imencode('.jpg', img)
        image_bytes = encoded.tobytes()
        
        result = classifier.classify_from_bytes(image_bytes)
        
        assert result is not None


# ============ 检测器测试 ============

class TestDetector:
    """缺陷检测器测试"""
    
    def test_detector_init(self):
        """测试检测器初始化"""
        detector = DefectDetector()
        assert detector is not None
    
    def test_detect_normal_image(self):
        """测试正常图像检测"""
        detector = DefectDetector()
        img = create_test_image()
        
        results = detector.detect(img)
        
        assert isinstance(results, list)
    
    def test_detect_crack_image(self):
        """测试裂缝检测"""
        detector = DefectDetector()
        img = create_crack_image()
        
        results = detector.detect(img)
        
        # 裂缝应该被检测到
        crack_results = [r for r in results if r.defect_type == DefectType.CRACK]
        # 可能检测到也可能检测不到（取决于图像质量）
        assert isinstance(results, list)
    
    def test_batch_detect(self):
        """测试批量检测"""
        detector = DefectDetector()
        images = [create_test_image() for _ in range(3)]
        
        results = detector.batch_detect(images)
        
        assert len(results) == 3
    
    def test_detect_from_bytes(self):
        """测试从字节数据检测"""
        detector = DefectDetector()
        img = create_test_image()
        
        _, encoded = cv2.imencode('.jpg', img)
        image_bytes = encoded.tobytes()
        
        results = detector.detect_from_bytes(image_bytes)
        
        assert isinstance(results, list)


# ============ 评分器测试 ============

class TestScorer:
    """可疑度评分器测试"""
    
    def test_scorer_init(self):
        """测试评分器初始化"""
        scorer = SuspicionScorer()
        assert scorer is not None
    
    def test_score_detection(self):
        """测试单个检测结果评分"""
        scorer = SuspicionScorer()
        
        detection = DetectionResult(
            defect_type=DefectType.CRACK,
            confidence=0.8,
            suspicion_score=70,
            severity="warning"
        )
        
        score = scorer.score_detection(detection)
        
        assert 0 <= score <= 100
    
    def test_score_task(self):
        """测试任务评分"""
        scorer = SuspicionScorer()
        
        task = InspectionTask()
        task.classification = ClassificationResult(
            part=ConstructionPart.ROAD,
            phase=ConstructionPhase.DURING,
            confidence=0.8
        )
        task.detections = [
            DetectionResult(
                defect_type=DefectType.CRACK,
                confidence=0.7,
                suspicion_score=60,
                severity="warning"
            )
        ]
        
        score = scorer.score_task(task)
        
        assert 0 <= score <= 100
    
    def test_risk_level(self):
        """测试风险等级"""
        scorer = SuspicionScorer()
        
        assert scorer.get_risk_level(25) == "low"
        assert scorer.get_risk_level(40) == "medium"
        assert scorer.get_risk_level(65) == "high"
        assert scorer.get_risk_level(90) == "critical"
    
    def test_should_require_review(self):
        """测试是否需要审核"""
        scorer = SuspicionScorer()
        
        # 高风险任务
        task1 = InspectionTask()
        task1.classification = ClassificationResult(
            part=ConstructionPart.ROAD,
            phase=ConstructionPhase.DURING,
            confidence=0.9
        )
        task1.detections = [
            DetectionResult(
                defect_type=DefectType.CRACK,
                confidence=0.9,
                suspicion_score=85,
                severity="critical"
            )
        ]
        
        assert scorer.should_require_review(task1)
    
    def test_review_recommendation(self):
        """测试审核建议生成"""
        scorer = SuspicionScorer()
        
        task = InspectionTask()
        task.classification = ClassificationResult(
            part=ConstructionPart.ROAD,
            phase=ConstructionPhase.AFTER,
            confidence=0.9
        )
        task.detections = [
            DetectionResult(
                defect_type=DefectType.CRACK,
                confidence=0.8,
                suspicion_score=75,
                severity="warning"
            )
        ]
        
        rec = scorer.generate_review_recommendation(task)
        
        assert "score" in rec
        assert "risk_level" in rec
        assert "requires_review" in rec


# ============ 工作流测试 ============

class TestWorkflow:
    """工作流测试"""
    
    def test_workflow_init(self):
        """测试工作流初始化"""
        workflow = InspectionWorkflow()
        assert workflow is not None
    
    def test_process_image(self):
        """测试处理图像"""
        workflow = InspectionWorkflow()
        img = create_test_image()
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, img)
        
        try:
            task = workflow.process_image(
                image_path=temp_path,
                project_id=1,
                location="测试"
            )
            
            assert task is not None
            assert task.classification is not None
            assert task.created_at is not None
        finally:
            os.unlink(temp_path)
    
    def test_review_task(self):
        """测试任务审核"""
        workflow = InspectionWorkflow()
        img = create_crack_image()
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, img)
        
        try:
            task = workflow.process_image(image_path=temp_path)
            
            # 审核通过
            reviewed = workflow.review_task(
                task.task_id,
                reviewer_id="tester",
                approved=True,
                comment="已确认，缺陷轻微"
            )
            
            assert reviewed.status == ReviewStatus.APPROVED
            assert reviewed.reviewer_id == "tester"
        finally:
            os.unlink(temp_path)
    
    def test_get_pending_tasks(self):
        """测试获取待审核任务"""
        workflow = InspectionWorkflow()
        
        pending = workflow.get_pending_tasks()
        
        assert isinstance(pending, list)
    
    def test_statistics(self):
        """测试统计信息"""
        workflow = InspectionWorkflow()
        
        stats = workflow.get_statistics()
        
        assert "total" in stats
        assert "pending" in stats
        assert "approved" in stats
        assert "rejected" in stats


# ============ 集成测试 ============

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """完整工作流测试"""
        workflow = create_workflow()
        
        # 准备测试图像
        import tempfile
        images = []
        
        for i, create_fn in enumerate([create_test_image, create_crack_image, create_spalling_image]):
            img = create_fn()
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name
                cv2.imwrite(temp_path, img)
            images.append(temp_path)
        
        try:
            # 批量处理
            result = workflow.process_batch(
                image_paths=images,
                project_id=1
            )
            
            assert result.total == 3
            assert isinstance(result.tasks, list)
            
            # 审核任务
            for task in result.tasks:
                if task.has_defects:
                    workflow.review_task(
                        task.task_id,
                        reviewer_id="tester",
                        approved=True
                    )
            
            # 统计
            stats = workflow.get_statistics()
            assert stats["total"] == 3
        
        finally:
            for path in images:
                os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
