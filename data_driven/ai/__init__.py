"""
AI质量检测模块
"""

from .image_classifier import ImageClassifier
from .defect_detector import DefectDetector
from .service import AIService

__all__ = ["ImageClassifier", "DefectDetector", "AIService"]
__version__ = "1.0.0"
