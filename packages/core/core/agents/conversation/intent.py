# -*- coding: utf-8 -*-
"""
意图识别模块

提供问题类型分类、参数提取、置信度评估功能
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


class QuestionType(Enum):
    """问题类型"""
    # 基础查询
    QUERY_COORDINATE = "query_coordinate"      # 坐标查询
    QUERY_ELEVATION = "query_elevation"       # 标高/高程查询
    QUERY_GRADE = "query_grade"               # 纵坡/坡度查询
    QUERY_CROSS_SECTION = "query_cross_section"  # 横断面查询
    QUERY_ENTITY = "query_entity"             # 实体搜索
    
    # 推理查询
    REASONING_PATH = "reasoning_path"        # 路径推理
    REASONING_RELATION = "reasoning_relation" # 关系推理
    
    # 计算查询
    CALCULATION = "calculation"               # 计算类
    COMPARISON = "comparison"                  # 比较类
    
    # 多轮对话
    CLARIFICATION = "clarification"           # 澄清请求
    FOLLOW_UP = "follow_up"                    # 追问
    RELATED_QUERY = "related_query"            # 相关查询
    
    # 其他
    GREETING = "greeting"                     # 问候
    UNKNOWN = "unknown"                        # 未知/无法理解
    

@dataclass
class Intent:
    """意图"""
    type: QuestionType
    confidence: float
    entities: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    processed_query: str = ""
    requires_clarification: bool = False
    clarification_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "parameters": self.parameters,
            "raw_query": self.raw_query,
            "processed_query": self.processed_query,
            "requires_clarification": self.requires_clarification,
            "clarification_message": self.clarification_message
        }


class IntentRecognizer:
    """意图识别器"""
    
    # 关键词映射到问题类型
    KEYWORD_PATTERNS = {
        QuestionType.QUERY_COORDINATE: [
            "坐标", "x", "y", "coordinate", "位置", "在哪"
        ],
        QuestionType.QUERY_ELEVATION: [
            "标高", "高程", "elevation", "z", "海拔", "设计高程"
        ],
        QuestionType.QUERY_GRADE: [
            "纵坡", "坡度", "grade", "坡", "i=", "i ="
        ],
        QuestionType.QUERY_CROSS_SECTION: [
            "横断", "断面", "cross section", "横坡"
        ],
        QuestionType.QUERY_ENTITY: [
            "搜索", "查找", "list", "列表", "有哪些", "什么"
        ],
        QuestionType.CALCULATION: [
            "计算", "算", "求", "多少"
        ],
        QuestionType.COMPARISON: [
            "比较", "哪个", "哪个好", "区别", "差异"
        ],
        QuestionType.REASONING_PATH: [
            "路径", "从", "到", "经过"
        ],
    }
    
    # 桩号提取模式
    CHAINAGE_PATTERN = re.compile(r'K(\d+)\+(\d{3})')
    
    def __init__(self):
        """初始化意图识别器"""
        self.last_intent: Optional[Intent] = None
        
    def recognize(self, query: str, context: Dict = None) -> Intent:
        """
        识别意图
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            识别出的意图
        """
        query = query.strip()
        context = context or {}
        
        # 1. 检查是否是问候语
        if self._is_greeting(query):
            return Intent(
                type=QuestionType.GREETING,
                confidence=1.0,
                raw_query=query,
                processed_query=query
            )
        
        # 2. 提取桩号
        chainage_info = self._extract_chainage(query)
        
        # 3. 识别问题类型
        question_type, type_confidence = self._classify_question_type(query)
        
        # 4. 提取参数
        parameters = self._extract_parameters(query, chainage_info, context)
        
        # 5. 构建实体列表
        entities = self._build_entities(query, chainage_info, question_type)
        
        # 6. 检查是否需要澄清
        requires_clarification, clarification_message = self._check_clarification(
            query, chainage_info, question_type, context
        )
        
        # 7. 评估置信度
        confidence = self._evaluate_confidence(
            question_type, chainage_info, entities, requires_clarification
        )
        
        intent = Intent(
            type=question_type,
            confidence=confidence,
            entities=entities,
            parameters=parameters,
            raw_query=query,
            processed_query=query,  # 可以在这里做查询扩展
            requires_clarification=requires_clarification,
            clarification_message=clarification_message
        )
        
        self.last_intent = intent
        return intent
    
    def _is_greeting(self, query: str) -> bool:
        """检查是否是问候语"""
        greetings = ["你好", "hi", "hello", "在吗", "您好", "hey"]
        return any(query.lower() == g or query.startswith(g) for g in greetings)
    
    def _extract_chainage(self, query: str) -> Optional[Dict[str, Any]]:
        """提取桩号信息"""
        match = self.CHAINAGE_PATTERN.search(query)
        if match:
            chainage = f"K{match.group(1)}+{match.group(2)}"
            station = int(match.group(1)) * 1000 + int(match.group(2))
            return {
                "chainage": chainage,
                "station": station,
                "kilometer": int(match.group(1)),
                "meter": int(match.group(2))
            }
        return None
    
    def _classify_question_type(
        self, 
        query: str
    ) -> Tuple[QuestionType, float]:
        """
        分类问题类型
        
        Returns:
            (问题类型, 置信度)
        """
        scores = {}
        
        for qtype, keywords in self.KEYWORD_PATTERNS.items():
            score = 0
            for keyword in keywords:
                if keyword in query.lower():
                    score += 1
            if score > 0:
                scores[qtype] = score
        
        if not scores:
            # 默认认为是实体查询
            return (QuestionType.QUERY_ENTITY, 0.3)
        
        # 返回得分最高的类型
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # 置信度基于关键词匹配数量
        confidence = min(0.3 + best_score * 0.2, 1.0)
        
        return (best_type, confidence)
    
    def _extract_parameters(
        self,
        query: str,
        chainage_info: Optional[Dict],
        context: Dict
    ) -> Dict[str, Any]:
        """提取参数"""
        params = {}
        
        # 桩号参数
        if chainage_info:
            params["chainage"] = chainage_info["chainage"]
            params["station"] = chainage_info["station"]
        
        # 范围参数
        if "到" in query or "-" in query:
            # 尝试提取范围
            range_match = re.search(
                r'K(\d+)\+(\d{3}).*?K(\d+)\+(\d{3})',
                query
            )
            if range_match:
                params["start_station"] = int(range_match.group(1)) * 1000 + int(range_match.group(2))
                params["end_station"] = int(range_match.group(3)) * 1000 + int(range_match.group(4))
        
        # 工程项目参数
        project_keywords = ["道路", "桥梁", "隧道", "涵洞", "排水"]
        for kw in project_keywords:
            if kw in query:
                params.setdefault("project_type", []).append(kw)
        
        # 从上下文获取参数
        if "current_chainage" in context:
            params.setdefault("chainage", context["current_chainage"])
        if "current_station" in context:
            params.setdefault("station", context["current_station"])
        
        return params
    
    def _build_entities(
        self,
        query: str,
        chainage_info: Optional[Dict],
        question_type: QuestionType
    ) -> List[Dict[str, Any]]:
        """构建实体列表"""
        entities = []
        
        if chainage_info:
            entities.append({
                "type": "chainage",
                "value": chainage_info["chainage"],
                "station": chainage_info["station"]
            })
        
        # 根据问题类型添加对应实体
        if question_type == QuestionType.QUERY_COORDINATE:
            entities.append({"type": "coordinate", "required": True})
        elif question_type == QuestionType.QUERY_ELEVATION:
            entities.append({"type": "elevation", "required": True})
        elif question_type == QuestionType.QUERY_GRADE:
            entities.append({"type": "grade", "required": True})
        
        return entities
    
    def _check_clarification(
        self,
        query: str,
        chainage_info: Optional[Dict],
        question_type: QuestionType,
        context: Dict
    ) -> Tuple[bool, str]:
        """检查是否需要澄清"""
        # 如果没有桩号信息，检查上下文是否有
        if not chainage_info:
            if context.get("current_chainage"):
                # 上下文中存在，可以继续
                return (False, "")
            else:
                # 需要澄清桩号
                return (
                    True, 
                    "请提供具体的桩号，例如 K0+500"
                )
        
        # 检查问题类型是否明确
        if question_type == QuestionType.UNKNOWN:
            return (
                True,
                "我无法理解您的问题。请尝试询问具体的桩号信息。"
            )
        
        return (False, "")
    
    def _evaluate_confidence(
        self,
        question_type: QuestionType,
        chainage_info: Optional[Dict],
        entities: List[Dict],
        requires_clarification: bool
    ) -> float:
        """评估置信度"""
        if requires_clarification:
            return 0.3
        
        base_confidence = 0.5
        
        # 桩号信息存在增加置信度
        if chainage_info:
            base_confidence += 0.3
        
        # 实体识别增加置信度
        if entities:
            base_confidence += len(entities) * 0.1
        
        # 问题类型明确增加置信度
        if question_type not in [QuestionType.UNKNOWN, QuestionType.GREETING]:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def get_last_intent(self) -> Optional[Intent]:
        """获取上一次的识别结果"""
        return self.last_intent
    
    def get_related_queries(self, intent: Intent) -> List[str]:
        """
        根据当前意图推荐相关查询
        
        Args:
            intent: 当前意图
            
        Returns:
            推荐的查询列表
        """
        suggestions = []
        
        # 根据问题类型推荐
        if intent.type == QuestionType.QUERY_COORDINATE:
            suggestions = [
                "该位置的标高是多少",
                "该位置的纵坡是多少",
                "该位置的横断面"
            ]
        elif intent.type == QuestionType.QUERY_ELEVATION:
            suggestions = [
                "该位置的坐标",
                "该位置的纵坡",
                "前后100米的标高变化"
            ]
        elif intent.type == QuestionType.QUERY_GRADE:
            suggestions = [
                "该位置的坐标",
                "该位置的标高"
            ]
        
        # 如果有桩号信息，添加到建议中
        chainage = intent.parameters.get("chainage")
        if chainage:
            suggestions = [
                s.replace("该位置", chainage) 
                for s in suggestions
            ]
        
        return suggestions[:3]


# 全局识别器实例
_recognizer: Optional[IntentRecognizer] = None


def get_intent_recognizer() -> IntentRecognizer:
    """获取意图识别器"""
    global _recognizer
    if _recognizer is None:
        _recognizer = IntentRecognizer()
    return _recognizer


def recognize_intent(query: str, context: Dict = None) -> Intent:
    """识别意图的便捷函数"""
    return get_intent_recognizer().recognize(query, context)
