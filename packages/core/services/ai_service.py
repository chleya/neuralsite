"""
AI Service - AI服务层
照片分类接口、问题AI初筛、施工建议生成
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..ai.client import AIClient, get_ai_client
from ..ai.quality_classifier import QualityClassifier, ClassificationResult
from ..ai.knowledge_base import KnowledgeBase, get_knowledge_base
from ..ai.prompts import (
    ISSUE_ANALYSIS_PROMPT,
    CONSTRUCTION_ADVICE_PROMPT,
    KNOWLEDGE_ENHANCE_PROMPT,
    COMPREHENSIVE_ANALYSIS_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class PhotoClassificationResponse:
    """照片分类响应"""
    category: str
    category_confidence: float
    defects: List[Dict[str, Any]]
    overall_confidence: float
    description: str


@dataclass
class IssueAnalysisResponse:
    """问题分析响应"""
    problem_type: str
    severity: str
    causes: List[str]
    impact: str
    solutions: List[str]
    preventive_measures: List[str]
    related_standards: List[str]
    confidence: float


@dataclass
class ConstructionAdviceResponse:
    """施工建议响应"""
    process_name: str
    key_points: List[str]
    quality_control: List[str]
    safety_precautions: List[str]
    common_issues: List[Dict[str, str]]
    acceptance_standards: List[str]
    confidence: float


class AIService:
    """AI服务"""

    def __init__(
        self,
        client: Optional[AIClient] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        """
        初始化AI服务

        Args:
            client: AI客户端
            knowledge_base: 知识库
        """
        self.client = client or get_ai_client()
        self.knowledge_base = knowledge_base or get_knowledge_base()
        self.classifier = QualityClassifier(self.client)

    # ========== 照片分类 ==========

    def classify_photo(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        context: Optional[str] = None,
    ) -> PhotoClassificationResponse:
        """
        照片分类接口

        Args:
            image_url: 图片URL
            image_base64: base64编码的图片
            context: 上下文信息

        Returns:
            PhotoClassificationResponse对象
        """
        try:
            result = self.classifier.classify(
                image_url=image_url,
                image_base64=image_base64,
                context=context,
            )

            return PhotoClassificationResponse(
                category=result.category.value,
                category_confidence=result.category_confidence,
                defects=[
                    {
                        "type": d.get("type", {}).value if hasattr(d.get("type"), "value") else str(d.get("type", "")),
                        "confidence": d.get("confidence", 0),
                        "location": d.get("location", ""),
                        "severity": d.get("severity", "unknown"),
                    }
                    for d in result.defects
                ],
                overall_confidence=result.overall_confidence,
                description=result.description,
            )

        except Exception as e:
            logger.error(f"Photo classification failed: {e}")
            return PhotoClassificationResponse(
                category="other",
                category_confidence=0.0,
                defects=[],
                overall_confidence=0.0,
                description=f"分类失败: {str(e)}",
            )

    # ========== 问题分析 ==========

    def analyze_issue(
        self,
        problem_description: str,
        location: Optional[str] = None,
        process: Optional[str] = None,
        context: Optional[str] = None,
    ) -> IssueAnalysisResponse:
        """
        问题AI初筛

        Args:
            problem_description: 问题描述
            location: 发生部位
            process: 施工工序
            context: 其他上下文

        Returns:
            IssueAnalysisResponse对象
        """
        # 从知识库获取相关信息
        knowledge_context = ""
        if location or process:
            keyword = location or process
            knowledge_context = self.knowledge_base.get_context_for_ai(keyword)

        # 构建prompt
        prompt_parts = []

        if problem_description:
            prompt_parts.append(f"问题描述: {problem_description}")
        if location:
            prompt_parts.append(f"发生部位: {location}")
        if process:
            prompt_parts.append(f"施工工序: {process}")
        if context:
            prompt_parts.append(f"其他信息: {context}")

        if knowledge_context:
            prompt_parts.append(f"\n参考知识库:\n{knowledge_context}")

        prompt = "\n".join(prompt_parts)

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=ISSUE_ANALYSIS_PROMPT,
                temperature=0.3,
                max_tokens=2000,
            )

            # 解析响应
            data = self._parse_json_response(response)

            if data:
                return IssueAnalysisResponse(
                    problem_type=data.get("problem_type", "未知"),
                    severity=data.get("severity", "unknown"),
                    causes=data.get("causes", []),
                    impact=data.get("impact", ""),
                    solutions=data.get("solutions", []),
                    preventive_measures=data.get("preventive_measures", []),
                    related_standards=data.get("related_standards", []),
                    confidence=data.get("confidence", 0.5),
                )

        except Exception as e:
            logger.error(f"Issue analysis failed: {e}")

        return IssueAnalysisResponse(
            problem_type="分析失败",
            severity="unknown",
            causes=[],
            impact=str(e),
            solutions=[],
            preventive_measures=[],
            related_standards=[],
            confidence=0.0,
        )

    # ========== 施工建议 ==========

    def get_construction_advice(
        self,
        process: str,
        location: Optional[str] = None,
        weather: Optional[str] = None,
        materials: Optional[List[str]] = None,
        quality_requirements: Optional[str] = None,
    ) -> ConstructionAdviceResponse:
        """
        施工建议生成

        Args:
            process: 施工工序
            location: 施工部位
            weather: 天气条件
            materials: 使用材料
            quality_requirements: 质量要求

        Returns:
            ConstructionAdviceResponse对象
        """
        # 从知识库获取相关信息
        knowledge_context = self.knowledge_base.get_context_for_ai(process)

        # 构建prompt
        prompt_parts = [f"施工工序: {process}"]

        if location:
            prompt_parts.append(f"施工部位: {location}")
        if weather:
            prompt_parts.append(f"天气条件: {weather}")
        if materials:
            prompt_parts.append(f"使用材料: {', '.join(materials)}")
        if quality_requirements:
            prompt_parts.append(f"质量要求: {quality_requirements}")

        if knowledge_context:
            prompt_parts.append(f"\n参考知识库:\n{knowledge_context}")

        prompt = "\n".join(prompt_parts)

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=CONSTRUCTION_ADVICE_PROMPT,
                temperature=0.3,
                max_tokens=2000,
            )

            # 解析响应
            data = self._parse_json_response(response)

            if data:
                # 处理common_issues格式
                common_issues = data.get("common_issues", [])
                if common_issues and isinstance(common_issues[0], str):
                    common_issues = [{"issue": c, "solution": ""} for c in common_issues]

                return ConstructionAdviceResponse(
                    process_name=data.get("process_name", process),
                    key_points=data.get("key_points", []),
                    quality_control=data.get("quality_control", []),
                    safety_precautions=data.get("safety_precautions", []),
                    common_issues=common_issues,
                    acceptance_standards=data.get("acceptance_standards", []),
                    confidence=data.get("confidence", 0.5),
                )

        except Exception as e:
            logger.error(f"Construction advice failed: {e}")

        return ConstructionAdviceResponse(
            process_name=process,
            key_points=[],
            quality_control=[],
            safety_precautions=[],
            common_issues=[],
            acceptance_standards=[],
            confidence=0.0,
        )

    # ========== 综合分析 ==========

    def comprehensive_analysis(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        综合分析

        Args:
            data: 输入数据 (照片、检测数据、施工记录等)

        Returns:
            分析结果
        """
        # 构建prompt
        prompt = json.dumps(data, ensure_ascii=False, indent=2)

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=COMPREHENSIVE_ANALYSIS_PROMPT,
                temperature=0.3,
                max_tokens=3000,
            )

            result = self._parse_json_response(response)
            if result:
                return result

        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")

        return {"error": str(e)}

    # ========== 辅助方法 ==========

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            import re

            # 尝试提取JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse JSON response: {e}")

        return None


# 全局服务实例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取全局AI服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def set_ai_service(service: AIService) -> None:
    """设置全局AI服务实例"""
    global _ai_service
    _ai_service = service
