# NeuralSite AI Module
# AI服务模块 - 提供照片分类、问题分析、施工建议等功能

from .client import AIClient, get_ai_client
from .quality_classifier import QualityClassifier
from .knowledge_base import KnowledgeBase
from .prompts import (
    PHOTO_CLASSIFICATION_PROMPT,
    ISSUE_ANALYSIS_PROMPT,
    CONSTRUCTION_ADVICE_PROMPT,
)

__all__ = [
    "AIClient",
    "get_ai_client",
    "QualityClassifier",
    "KnowledgeBase",
    "PHOTO_CLASSIFICATION_PROMPT",
    "ISSUE_ANALYSIS_PROMPT",
    "CONSTRUCTION_ADVICE_PROMPT",
]
