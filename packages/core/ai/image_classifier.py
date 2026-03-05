"""
Image Classifier - 图像分类器
NeuralSite AI 图像分类服务

支持分类:
- 施工状态: 正常/进行中/完成
- 部位: 路面/桥梁/隧道/护坡
- 问题类型: 裂缝/破损/沉降

基于AI大模型的图像理解能力实现
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .client import AIClient, get_ai_client
from .prompts import PHOTO_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


# ========== 分类枚举 ==========

class ConstructionStatus(Enum):
    """施工状态"""
    NORMAL = "normal"      # 正常
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 完成
    UNKNOWN = "unknown"  # 未知


class ConstructionPart(Enum):
    """施工部位"""
    PAVEMENT = "pavement"      # 路面
    BRIDGE = "bridge"           # 桥梁
    TUNNEL = "tunnel"           # 隧道
    SLOPE = "slope"             # 护坡
    UNKNOWN = "unknown"         # 未知


class ProblemType(Enum):
    """问题类型"""
    CRACK = "crack"             # 裂缝
    DAMAGE = "damage"           # 破损
    SETTLEMENT = "settlement"   # 沉降
    NONE = "none"               # 无问题
    UNKNOWN = "unknown"         # 未知


# ========== 数据结构 ==========

@dataclass
class ImageClassificationResult:
    """图像分类结果"""
    # 施工状态
    status: ConstructionStatus
    status_confidence: float  # 0-1
    
    # 施工部位
    part: ConstructionPart
    part_confidence: float  # 0-1
    
    # 问题类型
    problem: ProblemType
    problem_confidence: float  # 0-1
    
    # 问题详情
    problem_details: Optional[Dict[str, Any]] = None
    
    # 整体描述
    description: str = ""
    
    # 整体置信度
    overall_confidence: float = 0.0
    
    # 原始响应
    raw_response: Optional[Dict[str, Any]] = None


# ========== 提示词 ==========

IMAGE_CLASSIFICATION_SYSTEM_PROMPT = """你是一个专业的建筑工程图像识别AI助手。
你的任务是分析施工场景图像，进行以下分类：

## 分类维度

### 1. 施工状态 (status)
- normal: 正常施工状态，设施完好，整洁有序
- in_progress: 施工进行中，有施工人员、设备、材料
- completed: 施工已完成，设施投入使用

### 2. 施工部位 (part)
- pavement: 路面（道路、人行道、停车场等）
- bridge: 桥梁（桥面、桥墩、护栏等）
- tunnel: 隧道（洞身、洞口、排水设施等）
- slope: 护坡（边坡、挡土墙、植被护坡等）

### 3. 问题类型 (problem)
- crack: 裂缝（各种形式的裂纹、缝隙）
- damage: 破损（缺损、损坏、破碎）
- settlement: 沉降（不均匀沉降、塌陷、下沉）
- none: 未发现问题

## 输出格式
请返回JSON格式结果：
```json
{
  "status": "in_progress",
  "status_confidence": 0.92,
  "part": "bridge",
  "part_confidence": 0.88,
  "problem": "crack",
  "problem_confidence": 0.85,
  "problem_details": {
    "crack_width_mm": 2.5,
    "crack_length_m": 3.2,
    "crack_pattern": "网状裂缝",
    "severity": "medium"
  },
  "description": "桥梁桥面正在施工，发现网状裂缝",
  "overall_confidence": 0.88
}
```

请只返回JSON，不要其他内容。"""


# ========== 分类器 ==========

class ImageClassifier:
    """图像分类器 - NeuralSite AI 图像分类服务"""
    
    # 中文标签映射
    STATUS_LABELS = {
        ConstructionStatus.NORMAL: "正常",
        ConstructionStatus.IN_PROGRESS: "进行中",
        ConstructionStatus.COMPLETED: "完成",
        ConstructionStatus.UNKNOWN: "未知",
    }
    
    PART_LABELS = {
        ConstructionPart.PAVEMENT: "路面",
        ConstructionPart.BRIDGE: "桥梁",
        ConstructionPart.TUNNEL: "隧道",
        ConstructionPart.SLOPE: "护坡",
        ConstructionPart.UNKNOWN: "未知",
    }
    
    PROBLEM_LABELS = {
        ProblemType.CRACK: "裂缝",
        ProblemType.DAMAGE: "破损",
        ProblemType.SETTLEMENT: "沉降",
        ProblemType.NONE: "无问题",
        ProblemType.UNKNOWN: "未知",
    }
    
    def __init__(self, client: Optional[AIClient] = None):
        """
        初始化图像分类器
        
        Args:
            client: AI客户端 (可选，默认使用全局客户端)
        """
        self.client = client or get_ai_client()
    
    def classify(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        context: Optional[str] = None,
    ) -> ImageClassificationResult:
        """
        对图像进行分类
        
        Args:
            image_url: 图片URL
            image_base64: base64编码的图片
            context: 上下文信息 (如工程名称、标段等)
        
        Returns:
            ImageClassificationResult对象
        """
        # 构建prompt
        prompt = self._build_prompt(image_url, image_base64, context)
        
        # 调用AI
        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=IMAGE_CLASSIFICATION_SYSTEM_PROMPT,
                temperature=0.3,  # 低温度，更确定性
                max_tokens=2000,
            )
            
            # 解析响应
            result = self._parse_response(response)
            result.raw_response = {"prompt": prompt, "response": response}
            return result
            
        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            # 返回默认结果
            return ImageClassificationResult(
                status=ConstructionStatus.UNKNOWN,
                status_confidence=0.0,
                part=ConstructionPart.UNKNOWN,
                part_confidence=0.0,
                problem=ProblemType.UNKNOWN,
                problem_confidence=0.0,
                description=f"分类失败: {str(e)}",
                overall_confidence=0.0,
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
        
        prompt_parts.append("\n请分析这张施工照片，进行以下分类判断：")
        prompt_parts.append("1. 施工状态 (normal/in_progress/completed)")
        prompt_parts.append("2. 施工部位 (pavement/bridge/tunnel/slope)")
        prompt_parts.append("3. 问题类型 (crack/damage/settlement/none)")
        prompt_parts.append("4. 如有问题，提供详细信息")
        prompt_parts.append("\n请返回JSON格式结果")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response: str) -> ImageClassificationResult:
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
    
    def _build_result_from_json(self, data: Dict[str, Any]) -> ImageClassificationResult:
        """从JSON数据构建结果"""
        # 解析施工状态
        status_str = data.get("status", "unknown").lower()
        status = self._parse_status(status_str)
        
        # 解析施工部位
        part_str = data.get("part", "unknown").lower()
        part = self._parse_part(part_str)
        
        # 解析问题类型
        problem_str = data.get("problem", "unknown").lower()
        problem = self._parse_problem(problem_str)
        
        # 解析置信度
        status_confidence = data.get("status_confidence", 0.5)
        part_confidence = data.get("part_confidence", 0.5)
        problem_confidence = data.get("problem_confidence", 0.5)
        
        # 解析问题详情
        problem_details = data.get("problem_details")
        
        return ImageClassificationResult(
            status=status,
            status_confidence=status_confidence,
            part=part,
            part_confidence=part_confidence,
            problem=problem,
            problem_confidence=problem_confidence,
            problem_details=problem_details,
            description=data.get("description", ""),
            overall_confidence=data.get("overall_confidence", 0.5),
        )
    
    def _parse_status(self, status_str: str) -> ConstructionStatus:
        """解析施工状态"""
        status_map = {
            "normal": ConstructionStatus.NORMAL,
            "normal/正常": ConstructionStatus.NORMAL,
            "进行中": ConstructionStatus.IN_PROGRESS,
            "in_progress": ConstructionStatus.IN_PROGRESS,
            "in-progress": ConstructionStatus.IN_PROGRESS,
            "completed": ConstructionStatus.COMPLETED,
            "完成": ConstructionStatus.COMPLETED,
        }
        return status_map.get(status_str, ConstructionStatus.UNKNOWN)
    
    def _parse_part(self, part_str: str) -> ConstructionPart:
        """解析施工部位"""
        part_map = {
            "pavement": ConstructionPart.PAVEMENT,
            "pavement/路面": ConstructionPart.PAVEMENT,
            "路面": ConstructionPart.PAVEMENT,
            "道路": ConstructionPart.PAVEMENT,
            "bridge": ConstructionPart.BRIDGE,
            "bridge/桥梁": ConstructionPart.BRIDGE,
            "桥梁": ConstructionPart.BRIDGE,
            "tunnel": ConstructionPart.TUNNEL,
            "tunnel/隧道": ConstructionPart.TUNNEL,
            "隧道": ConstructionPart.TUNNEL,
            "slope": ConstructionPart.SLOPE,
            "slope/护坡": ConstructionPart.SLOPE,
            "护坡": ConstructionPart.SLOPE,
            "边坡": ConstructionPart.SLOPE,
            "挡土墙": ConstructionPart.SLOPE,
        }
        return part_map.get(part_str, ConstructionPart.UNKNOWN)
    
    def _parse_problem(self, problem_str: str) -> ProblemType:
        """解析问题类型"""
        problem_map = {
            "crack": ProblemType.CRACK,
            "crack/裂缝": ProblemType.CRACK,
            "裂缝": ProblemType.CRACK,
            "裂纹": ProblemType.CRACK,
            "damage": ProblemType.DAMAGE,
            "damage/破损": ProblemType.DAMAGE,
            "破损": ProblemType.DAMAGE,
            "损坏": ProblemType.DAMAGE,
            "settlement": ProblemType.SETTLEMENT,
            "settlement/沉降": ProblemType.SETTLEMENT,
            "沉降": ProblemType.SETTLEMENT,
            "下沉": ProblemType.SETTLEMENT,
            "none": ProblemType.NONE,
            "无": ProblemType.NONE,
            "无问题": ProblemType.NONE,
            "正常": ProblemType.NONE,
        }
        return problem_map.get(problem_str, ProblemType.UNKNOWN)
    
    def _build_result_from_text(self, text: str) -> ImageClassificationResult:
        """从文本构建结果 (fallback)"""
        text_lower = text.lower()
        
        # 解析施工状态
        status = ConstructionStatus.UNKNOWN
        status_confidence = 0.2
        
        if "正常" in text and "进行中" not in text and "完成" not in text:
            status = ConstructionStatus.NORMAL
            status_confidence = 0.5
        elif "进行中" in text or "施工" in text:
            status = ConstructionStatus.IN_PROGRESS
            status_confidence = 0.5
        elif "完成" in text or "完工" in text or "投入使用" in text:
            status = ConstructionStatus.COMPLETED
            status_confidence = 0.5
        
        # 解析施工部位
        part = ConstructionPart.UNKNOWN
        part_confidence = 0.2
        
        if "路面" in text or "道路" in text or "人行道" in text:
            part = ConstructionPart.PAVEMENT
            part_confidence = 0.5
        elif "桥" in text:
            part = ConstructionPart.BRIDGE
            part_confidence = 0.5
        elif "隧道" in text or "洞" in text:
            part = ConstructionPart.TUNNEL
            part_confidence = 0.5
        elif "护坡" in text or "边坡" in text or "挡土墙" in text:
            part = ConstructionPart.SLOPE
            part_confidence = 0.5
        
        # 解析问题类型
        problem = ProblemType.UNKNOWN
        problem_confidence = 0.2
        
        if "裂缝" in text or "裂纹" in text or "crack" in text_lower:
            problem = ProblemType.CRACK
            problem_confidence = 0.5
        elif "破损" in text or "损坏" in text or "damage" in text_lower:
            problem = ProblemType.DAMAGE
            problem_confidence = 0.5
        elif "沉降" in text or "下沉" in text or "settlement" in text_lower:
            problem = ProblemType.SETTLEMENT
            problem_confidence = 0.5
        elif "正常" in text or "无问题" in text or "完好" in text:
            problem = ProblemType.NONE
            problem_confidence = 0.5
        
        return ImageClassificationResult(
            status=status,
            status_confidence=status_confidence,
            part=part,
            part_confidence=part_confidence,
            problem=problem,
            problem_confidence=problem_confidence,
            description=text[:200],
            overall_confidence=0.3,
        )
    
    def batch_classify(
        self,
        images: List[Dict[str, Any]],
    ) -> List[ImageClassificationResult]:
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
    
    def get_label(self, result: ImageClassificationResult) -> Dict[str, str]:
        """
        获取分类标签 (中文)
        
        Args:
            result: 分类结果
        
        Returns:
            标签字典 {"status": "进行中", "part": "桥梁", "problem": "裂缝"}
        """
        return {
            "status": self.STATUS_LABELS.get(result.status, "未知"),
            "part": self.PART_LABELS.get(result.part, "未知"),
            "problem": self.PROBLEM_LABELS.get(result.problem, "未知"),
        }


# ========== 规则匹配分类器 (备用) ==========

class RuleBasedClassifier:
    """
    基于规则的分类器 (备用/快速模式)
    适用于无法调用AI API时的简单分类
    """
    
    # 关键词匹配规则
    STATUS_KEYWORDS = {
        ConstructionStatus.NORMAL: ["正常", "完好", "整洁", "规范", "合格"],
        ConstructionStatus.IN_PROGRESS: ["施工", "进行中", "作业", "浇筑", "绑扎", "开挖"],
        ConstructionStatus.COMPLETED: ["完成", "完工", "竣工", "投入使用", "已建"],
    }
    
    PART_KEYWORDS = {
        ConstructionPart.PAVEMENT: ["路面", "道路", "人行道", "车道", "沥青", "水泥路面"],
        ConstructionPart.BRIDGE: ["桥", "桥面", "桥墩", "梁", "护栏", "伸缩缝"],
        ConstructionPart.TUNNEL: ["隧道", "洞身", "洞口", "排水沟", "衬砌"],
        ConstructionPart.SLOPE: ["护坡", "边坡", "挡土墙", "植被", "锚杆", "格构"],
    }
    
    PROBLEM_KEYWORDS = {
        ProblemType.CRACK: ["裂缝", "裂纹", "缝隙", "龟裂", "网裂"],
        ProblemType.DAMAGE: ["破损", "损坏", "缺损", "破碎", "脱落", "啃边"],
        ProblemType.SETTLEMENT: ["沉降", "下沉", "塌陷", "不均匀"],
    }
    
    def classify_from_text(self, text: str) -> ImageClassificationResult:
        """
        从文本描述进行分类 (无需图片)
        
        Args:
            text: 文本描述
        
        Returns:
            ImageClassificationResult对象
        """
        text_lower = text.lower()
        
        # 分类施工状态
        status, status_conf = self._match_keywords(text, self.STATUS_KEYWORDS)
        
        # 分类施工部位
        part, part_conf = self._match_keywords(text, self.PART_KEYWORDS)
        
        # 分类问题类型
        problem, problem_conf = self._match_keywords(text, self.PROBLEM_KEYWORDS)
        
        # 如果没有匹配到问题，默认为无问题
        if problem == ProblemType.UNKNOWN:
            problem = ProblemType.NONE
            problem_conf = 0.5
        
        return ImageClassificationResult(
            status=status,
            status_confidence=status_conf,
            part=part,
            part_confidence=part_conf,
            problem=problem,
            problem_confidence=problem_conf,
            description=text,
            overall_confidence=min(status_conf, part_conf, problem_conf),
        )
    
    def _match_keywords(
        self,
        text: str,
        keyword_dict: Dict[Enum, List[str]]
    ) -> tuple:
        """匹配关键词"""
        best_match = None
        best_confidence = 0.0
        
        for enum_value, keywords in keyword_dict.items():
            match_count = 0
            for keyword in keywords:
                if keyword in text:
                    match_count += 1
            
            if match_count > 0:
                confidence = min(0.3 + match_count * 0.2, 0.9)
                if confidence > best_confidence:
                    best_match = enum_value
                    best_confidence = confidence
        
        return best_match or type(list(keyword_dict.keys())[0])(list(keyword_dict.keys())[0].value), best_confidence


# ========== 便捷函数 ==========

_classifier: Optional[ImageClassifier] = None
_rule_classifier: Optional[RuleBasedClassifier] = None


def get_image_classifier() -> ImageClassifier:
    """获取图像分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = ImageClassifier()
    return _classifier


def get_rule_classifier() -> RuleBasedClassifier:
    """获取规则分类器实例"""
    global _rule_classifier
    if _rule_classifier is None:
        _rule_classifier = RuleBasedClassifier()
    return _rule_classifier


def classify_image(
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
    context: Optional[str] = None,
    use_rules: bool = False,
) -> ImageClassificationResult:
    """
    便捷分类函数
    
    Args:
        image_url: 图片URL
        image_base64: base64编码的图片
        context: 上下文信息
        use_rules: 是否使用规则匹配 (用于无法调用AI时)
    
    Returns:
        ImageClassificationResult对象
    """
    if use_rules:
        # 规则匹配需要文本描述
        if context:
            return get_rule_classifier().classify_from_text(context)
        else:
            raise ValueError("Rule-based classification requires context text")
    
    return get_image_classifier().classify(
        image_url=image_url,
        image_base64=image_base64,
        context=context,
    )
