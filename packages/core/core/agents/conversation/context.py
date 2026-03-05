# -*- coding: utf-8 -*-
"""
上下文跟踪模块

提供实体引用追踪、省略指代理解、上下文窗口管理功能
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


class EntityReferenceType(Enum):
    """实体引用类型"""
    DIRECT = "direct"           # 直接提及
    PRONOUN = "pronoun"         # 代词指代 (它/他/她)
    DEMONSTRATIVE = "demonstrative"  # 指示指代 (这个/那个)
    ELLIPSIS = "ellipsis"       # 省略 (如 "那它的纵坡呢")
    COMPARATIVE = "comparative" # 比较 (比...)


@dataclass
class TrackedEntity:
    """被追踪的实体"""
    entity_id: str
    entity_type: str
    name: str
    value: Any
    first_mentioned: str = ""  # 首次提及时间
    last_mentioned: str = ""   # 最后提及时间
    mention_count: int = 0
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "value": self.value,
            "first_mentioned": self.first_mentioned,
            "last_mentioned": self.last_mentioned,
            "mention_count": self.mention_count,
            "confidence": self.confidence
        }


@dataclass
class ContextWindow:
    """上下文窗口"""
    max_messages: int = 10
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """添加消息到窗口"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        
        # 保持窗口大小
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent(self, n: int = 5) -> List[Dict]:
        """获取最近n条消息"""
        return self.messages[-n:] if self.messages else []
    
    def clear(self):
        """清空窗口"""
        self.messages = []


class ContextTracker:
    """上下文跟踪器"""
    
    # 常见代词映射
    PRONOUN_MAPPING = {
        "它": "entity",
        "他": "entity", 
        "她": "entity",
        "这个": "entity",
        "那个": "entity",
        "这个的": "entity",
        "那个的": "entity",
        "它": "entity",
        "它们的": "entity",
        "刚才": "previous",
        "上次": "previous",
        "之前": "previous"
    }
    
    # 桩号提取模式
    CHAINAGE_PATTERN = re.compile(r'K(\d+)\+(\d{3})')
    CHAINAGE_SHORT_PATTERN = re.compile(r'^K(\d+)\+(\d{3})$')
    
    def __init__(self, window_size: int = 10):
        """
        初始化上下文跟踪器
        
        Args:
            window_size: 上下文窗口大小
        """
        self.window = ContextWindow(max_messages=window_size)
        self.tracked_entities: Dict[str, TrackedEntity] = {}
        self.last_question_type: Optional[str] = None
        self.last_entities: List[str] = []  # 最近问题涉及的实体
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """添加消息到上下文"""
        self.window.add_message(role, content, metadata)
    
    def track_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        value: Any,
        confidence: float = 1.0
    ):
        """
        追踪实体
        
        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            name: 实体名称
            value: 实体值
            confidence: 置信度
        """
        now = datetime.now().isoformat()
        
        if entity_id in self.tracked_entities:
            # 更新现有实体
            entity = self.tracked_entities[entity_id]
            entity.last_mentioned = now
            entity.mention_count += 1
            entity.value = value
            entity.confidence = confidence
        else:
            # 创建新实体
            self.tracked_entities[entity_id] = TrackedEntity(
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
                value=value,
                first_mentioned=now,
                last_mentioned=now,
                mention_count=1,
                confidence=confidence
            )
        
        # 更新最近实体列表
        if entity_id not in self.last_entities:
            self.last_entities.insert(0, entity_id)
            self.last_entities = self.last_entities[:5]  # 保留最近5个
    
    def resolve_reference(self, text: str) -> Tuple[Optional[str], EntityReferenceType, float]:
        """
        解析文本中的引用
        
        Args:
            text: 输入文本
            
        Returns:
            (解析后的实体ID, 引用类型, 置信度)
        """
        text = text.strip()
        
        # 1. 检查是否是直接桩号提及
        chainage_match = self.CHAINAGE_SHORT_PATTERN.match(text)
        if chainage_match:
            chainage = f"K{chainage_match.group(1)}+{chainage_match.group(2)}"
            return (chainage, EntityReferenceType.DIRECT, 1.0)
        
        # 2. 检查代词/指示词
        for pronoun, ref_type in self.PRONOUN_MAPPING.items():
            if pronoun in text:
                if self.last_entities:
                    return (
                        self.last_entities[0], 
                        EntityReferenceType.PRONOUN,
                        0.8
                    )
        
        # 3. 检查省略表达
        # 例如: "那它的纵坡呢" -> 需要从上一条消息推断
        if any(word in text for word in ["呢", "啊", "吗", "的", "它", "那"]):
            if self.last_entities:
                # 检查上一条消息是否是问句
                recent = self.window.get_recent(2)
                if len(recent) >= 2 and recent[-2].get("role") == "user":
                    return (
                        self.last_entities[0],
                        EntityReferenceType.ELLIPSIS,
                        0.7
                    )
        
        return (None, EntityReferenceType.DIRECT, 0.0)
    
    def extract_chainage_from_text(self, text: str) -> Optional[Tuple[str, int]]:
        """
        从文本中提取桩号
        
        Args:
            text: 输入文本
            
        Returns:
            (桩号字符串, 桩号米数) 或 None
        """
        match = self.CHAINAGE_PATTERN.search(text)
        if match:
            chainage = f"K{match.group(1)}+{match.group(2)}"
            station = int(match.group(1)) * 1000 + int(match.group(2))
            return (chainage, station)
        return None
    
    def get_entity_context(self, entity_id: str = None) -> Dict[str, Any]:
        """
        获取实体上下文
        
        Args:
            entity_id: 实体ID（默认最近实体）
            
        Returns:
            实体上下文字典
        """
        if entity_id is None and self.last_entities:
            entity_id = self.last_entities[0]
        
        if entity_id and entity_id in self.tracked_entities:
            entity = self.tracked_entities[entity_id]
            return {
                "entity_id": entity.entity_id,
                "entity_type": entity.entity_type,
                "name": entity.name,
                "value": entity.value,
                "mention_count": entity.mention_count,
                "confidence": entity.confidence
            }
        
        return {}
    
    def get_recent_entities(self, limit: int = 5) -> List[Dict]:
        """获取最近追踪的实体"""
        result = []
        for entity_id in self.last_entities[:limit]:
            if entity_id in self.tracked_entities:
                result.append(self.tracked_entities[entity_id].to_dict())
        return result
    
    def expand_query_with_context(self, query: str) -> str:
        """
        使用上下文扩展查询
        
        Args:
            query: 原始查询
            
        Returns:
            扩展后的查询
        """
        # 解析引用
        ref_entity_id, ref_type, confidence = self.resolve_reference(query)
        
        if ref_entity_id and confidence > 0.5:
            # 获取实体信息
            entity_info = self.get_entity_context(ref_entity_id)
            
            if entity_info:
                # 替换代词为实际实体
                # 例如: "它的标高" -> "K0+500的标高"
                expanded = query
                
                # 简单替换（实际可更复杂）
                for pronoun in ["它", "他", "她", "这个", "那个"]:
                    if pronoun in query:
                        expanded = query.replace(
                            pronoun,
                            entity_info.get("name", pronoun)
                        )
                
                return expanded
        
        return query
    
    def set_question_type(self, question_type: str):
        """设置问题类型"""
        self.last_question_type = question_type
    
    def get_question_type(self) -> Optional[str]:
        """获取问题类型"""
        return self.last_question_type
    
    def clear(self):
        """清空上下文"""
        self.window.clear()
        self.tracked_entities = {}
        self.last_question_type = None
        self.last_entities = []
    
    def get_summary(self) -> Dict:
        """获取上下文摘要"""
        return {
            "tracked_entities_count": len(self.tracked_entities),
            "recent_entities": self.get_recent_entities(3),
            "last_question_type": self.last_question_type,
            "window_size": len(self.window.messages),
            "recent_messages": [
                {"role": m["role"], "content": m["content"][:50]}
                for m in self.window.get_recent(3)
            ]
        }


# 创建默认的上下文跟踪器
_default_tracker: Optional[ContextTracker] = None


def get_context_tracker(window_size: int = 10) -> ContextTracker:
    """获取默认上下文跟踪器"""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = ContextTracker(window_size)
    return _default_tracker


def reset_context_tracker():
    """重置上下文跟踪器"""
    global _default_tracker
    _default_tracker = None
