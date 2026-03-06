"""
AI服务 - 统一接口
"""

from typing import Dict, Optional
import os

from .image_classifier import ImageClassifier
from .defect_detector import DefectDetector


class AIService:
    """AI服务 - 统一接口"""
    
    def __init__(
        self,
        classifier_model_path: Optional[str] = None,
        crack_model_path: Optional[str] = None,
        damage_model_path: Optional[str] = None
    ):
        """
        初始化AI服务
        
        Args:
            classifier_model_path: 分类器模型路径
            crack_model_path: 裂缝检测模型路径
            damage_model_path: 破损检测模型路径
        """
        self.classifier = ImageClassifier(model_path=classifier_model_path)
        self.detector = DefectDetector(
            crack_model_path=crack_model_path,
            damage_model_path=damage_model_path
        )
    
    def analyze(self, image_path: str, skip_validation: bool = False) -> Dict:
        """
        完整分析图像
        
        Args:
            image_path: 图像文件路径
            skip_validation: 是否跳过文件存在性验证（用于测试）
            
        Returns:
            完整分析结果
        """
        if not skip_validation and not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # 1. 分类
        classification = self.classifier.classify(image_path, skip_validation=skip_validation)
        
        # 2. 检测
        defects = self.detector.detect(image_path, skip_validation=skip_validation)
        
        # 3. 生成建议
        suggestion = self._generate_suggestion(classification, defects)
        
        return {
            "classification": classification,
            "defects": defects,
            "suggestion": suggestion,
            "status": "需要处理" if defects["defects"] else "通过"
        }
    
    def _generate_suggestion(self, classification: Dict, defects: Dict) -> str:
        """根据分类和缺陷结果生成建议"""
        if not defects["defects"]:
            return "通过 - 未检测到明显缺陷"
        
        # 检查是否有严重缺陷
        severe_defects = [d for d in defects["defects"] 
                         if d.get("severity") in ["严重", "危急"]]
        
        if severe_defects:
            return "紧急处理 - 检测到严重缺陷，建议立即现场检查"
        
        # 检查是否有中等缺陷
        medium_defects = [d for d in defects["defects"] 
                         if d.get("severity") == "中等"]
        
        if medium_defects:
            return "建议人工确认 - 检测到中等程度缺陷，建议现场复核"
        
        # 轻微缺陷
        return "建议关注 - 检测到轻微缺陷，可在下次巡检时关注"
    
    def classify_only(self, image_path: str) -> Dict:
        """仅进行图像分类"""
        return self.classifier.classify(image_path)
    
    def detect_only(self, image_path: str) -> Dict:
        """仅进行缺陷检测"""
        return self.detector.detect(image_path)
    
    def health_check(self) -> Dict:
        """服务健康检查"""
        return {
            "status": "healthy",
            "classifier": "ready" if self.classifier else "not_initialized",
            "detector": "ready" if self.detector else "not_initialized",
            "supported_defect_types": DefectDetector.get_defect_types(),
            "supported_classes": self.classifier.get_supported_classes()
        }


# 测试代码
if __name__ == "__main__":
    # 初始化服务
    service = AIService()
    
    # 健康检查
    print("=== Health Check ===")
    health = service.health_check()
    print(f"Status: {health['status']}")
    print()
    
    # 测试完整分析（使用模拟路径）
    print("=== Analyze Test ===")
    result = service.analyze("dummy_path.jpg", skip_validation=True)
    print(f"Status: {result['status']}")
    print(f"Suggestion: {result['suggestion']}")
    print()
    print(f"Classification:")
    print(f"  Part: {result['classification']['part']}")
    print(f"  Phase: {result['classification']['phase']}")
    print(f"  Confidence: {result['classification']['confidence']}")
    print()
    print(f"Defects: {result['defects']['summary']['total_defects']} found")
