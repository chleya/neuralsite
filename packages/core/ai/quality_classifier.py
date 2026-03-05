"""
Quality Classifier - 质量分类器
照片分类 (quality/safety/environment)
缺陷检测 (裂缝/破损/沉降)
置信度返回
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .client import AIClient, get_ai_client
from .prompts import PHOTO_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class PhotoCategory(Enum):
    """照片分类"""
    QUALITY = "quality"  # 质量检查
    SAFETY = "safety"    # 安全检查
    ENVIRONMENT = "environment"  # 环境检查
    PROGRESS = "progress"  # 施工进度
    OTHER = "other"  # 其他


class DefectType(Enum):
    """缺陷类型"""
    CRACK = "crack"  # 裂缝
    DAMAGE = "damage"  # 破损
    SETTLEMENT = "settlement"  # 沉降
    WATER_LEAKAGE = "water_leakage"  # 渗漏水
    DEFORMATION = "deformation"  # 变形
    CORROSION = "corrosion"  # 锈蚀
    NONE = "none"  # 无缺陷


@dataclass
class ClassificationResult:
    """分类结果"""
    category: PhotoCategory
    category_confidence: float  # 0-1
    defects: List[Dict[str, Any]]  # [{"type": DefectType, "confidence": float, "location": str, "severity": str}]
    overall_confidence: float  # 整体置信度
    description: str  # 描述
    raw_response: Optional[Dict[str, Any]] = None


class QualityClassifier:
    """质量分类器"""

    def __init__(self, client: Optional[AIClient] = None):
        """
        初始化质量分类器

        Args:
            client: AI客户端 (可选，默认使用全局客户端)
        """
        self.client = client or get_ai_client()

    def classify(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        context: Optional[str] = None,
    ) -> ClassificationResult:
        """
        对照片进行分类

        Args:
            image_url: 图片URL
            image_base64: base64编码的图片
            context: 上下文信息 (如施工部位、工序等)

        Returns:
            ClassificationResult对象
        """
        # 构建prompt
        prompt = self._build_prompt(image_url, image_base64, context)

        # 调用AI
        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=PHOTO_CLASSIFICATION_PROMPT,
                temperature=0.3,  # 低温度，更确定性
                max_tokens=2000,
            )

            # 解析响应
            result = self._parse_response(response)
            result.raw_response = {"prompt": prompt, "response": response}
            return result

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # 返回默认结果
            return ClassificationResult(
                category=PhotoCategory.OTHER,
                category_confidence=0.0,
                defects=[],
                overall_confidence=0.0,
                description=f"分类失败: {str(e)}",
            )

    def _build_prompt(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """构建分类prompt"""
        prompt_parts = []

        # 图片信息
        if image_url:
            prompt_parts.append(f"图片URL: {image_url}")
        if image_base64:
            prompt_parts.append("[图片数据已提供]")

        # 上下文
        if context:
            prompt_parts.append(f"上下文信息: {context}")

        prompt_parts.append("\n请分析这张施工照片，进行以下判断：")
        prompt_parts.append("1. 照片分类 (quality/safety/environment/progress/other)")
        prompt_parts.append("2. 如为质量检查，检测是否存在缺陷 (裂缝/破损/沉降/渗漏水/变形/锈蚀)")
        prompt_parts.append("3. 返回JSON格式结果")

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str) -> ClassificationResult:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_str = self._extract_json(response)
            if json_str:
                data = json.loads(json_str)
                return self._build_result_from_json(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, response: {response[:200]}")

        # 如果无法解析JSON，返回基于文本的结果
        return self._build_result_from_text(response)

    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON"""
        import re

        # 尝试找到 ```json ... ``` 块
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # 尝试找到 ``` ... ``` 块
        json_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # 尝试找到 { ... }
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return None

    def _build_result_from_json(self, data: Dict[str, Any]) -> ClassificationResult:
        """从JSON数据构建结果"""
        # 解析分类
        category_str = data.get("category", "other").lower()
        try:
            category = PhotoCategory(category_str)
        except ValueError:
            category = PhotoCategory.OTHER

        # 解析缺陷
        defects = []
        defect_list = data.get("defects", [])
        if isinstance(defect_list, list):
            for defect_data in defect_list:
                if isinstance(defect_data, dict):
                    defect_type_str = defect_data.get("type", "none").lower()
                    try:
                        defect_type = DefectType(defect_type_str)
                    except ValueError:
                        defect_type = DefectType.NONE

                    if defect_type != DefectType.NONE:
                        defects.append({
                            "type": defect_type,
                            "confidence": defect_data.get("confidence", 0.0),
                            "location": defect_data.get("location", ""),
                            "severity": defect_data.get("severity", "unknown"),
                        })

        return ClassificationResult(
            category=category,
            category_confidence=data.get("category_confidence", 0.5),
            defects=defects,
            overall_confidence=data.get("overall_confidence", 0.5),
            description=data.get("description", ""),
        )

    def _build_result_from_text(self, text: str) -> ClassificationResult:
        """从文本构建结果 (fallback)"""
        text_lower = text.lower()

        # 简单分类
        category = PhotoCategory.OTHER
        if "质量" in text or "quality" in text_lower:
            category = PhotoCategory.QUALITY
        elif "安全" in text or "safety" in text_lower:
            category = PhotoCategory.SAFETY
        elif "环境" in text or "environment" in text_lower:
            category = PhotoCategory.ENVIRONMENT
        elif "进度" in text or "progress" in text_lower:
            category = PhotoCategory.PROGRESS

        # 缺陷检测
        defects = []
        defect_keywords = {
            DefectType.CRACK: ["裂缝", "crack", "裂纹"],
            DefectType.DAMAGE: ["破损", "damage", "损坏"],
            DefectType.SETTLEMENT: ["沉降", "settlement"],
            DefectType.WATER_LEAKAGE: ["渗漏", "漏水", "water"],
            DefectType.DEFORMATION: ["变形", "deformation"],
            DefectType.CORROSION: ["锈蚀", "corrosion"],
        }

        for defect_type, keywords in defect_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    defects.append({
                        "type": defect_type,
                        "confidence": 0.5,
                        "location": "",
                        "severity": "unknown",
                    })
                    break

        return ClassificationResult(
            category=category,
            category_confidence=0.3,
            defects=defects,
            overall_confidence=0.3,
            description=text[:200],
        )

    def batch_classify(
        self,
        images: List[Dict[str, Any]],
    ) -> List[ClassificationResult]:
        """
        批量分类

        Args:
            images: 图片列表 [{"image_url": "...", "context": "..."}]

        Returns:
            分类结果列表
        """
        results = []
        for img in images:
            result = self.classify(
                image_url=img.get("image_url"),
                image_base64=img.get("image_base64"),
                context=img.get("context"),
            )
            results.append(result)

        return results


def detect_defects_from_text(description: str) -> List[Dict[str, Any]]:
    """
    从文本描述中检测缺陷 (辅助函数)

    Args:
        description: 缺陷描述文本

    Returns:
        缺陷列表
    """
    defects = []
    description_lower = description.lower()

    defect_patterns = {
        DefectType.CRACK: [
            r"裂缝[0-9.]+mm",
            r"裂缝宽度",
            r"裂纹",
            r"crack.*mm",
        ],
        DefectType.DAMAGE: [
            r"破损",
            r"损坏",
            r"缺口",
            r"damage",
        ],
        DefectType.SETTLEMENT: [
            r"沉降",
            r"下沉",
            r"settlement",
        ],
        DefectType.WATER_LEAKAGE: [
            r"渗水",
            r"漏水",
            r"渗漏",
            r"water.*leak",
        ],
    }

    for defect_type, patterns in defect_patterns.items():
        for pattern in patterns:
            import re
            if re.search(pattern, description_lower):
                defects.append({
                    "type": defect_type,
                    "confidence": 0.7,
                    "description": description,
                })
                break

    return defects
