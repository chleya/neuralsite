# -*- coding: utf-8 -*-
"""
对话历史存储模块

提供对话历史的持久化和检索功能
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path


@dataclass
class DialogueMessage:
    """对话消息"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent_type: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DialogueMessage":
        return cls(**data)


@dataclass
class DialogueHistory:
    """对话历史"""
    session_id: str
    user_id: str = ""
    messages: List[DialogueMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Dict = None,
        intent_type: str = "",
        confidence: float = 0.0
    ):
        """添加消息"""
        self.messages.append(DialogueMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            intent_type=intent_type,
            confidence=confidence
        ))
        self.updated_at = datetime.now().isoformat()
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        """获取消息"""
        if limit:
            return [m.to_dict() for m in self.messages[-limit:]]
        return [m.to_dict() for m in self.messages]
    
    def get_last_user_message(self) -> Optional[DialogueMessage]:
        """获取最后用户消息"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[DialogueMessage]:
        """获取最后助手消息"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DialogueHistory":
        messages = [DialogueMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id", ""),
            messages=messages,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class DialogueMemory:
    """对话记忆管理器"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化对话记忆管理器
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path or "storage/conversations"
        self._histories: Dict[str, DialogueHistory] = {}
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
    
    def create_history(
        self,
        session_id: str,
        user_id: str = "",
        metadata: Dict = None
    ) -> DialogueHistory:
        """创建对话历史"""
        history = DialogueHistory(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        self._histories[session_id] = history
        self._save_to_disk(session_id, history)
        return history
    
    def get_history(
        self,
        session_id: str,
        load_from_disk: bool = True
    ) -> Optional[DialogueHistory]:
        """获取对话历史"""
        # 内存中查找
        if session_id in self._histories:
            return self._histories[session_id]
        
        # 从磁盘加载
        if load_from_disk:
            history = self._load_from_disk(session_id)
            if history:
                self._histories[session_id] = history
                return history
        
        return None
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict = None,
        intent_type: str = "",
        confidence: float = 0.0
    ):
        """添加消息到历史"""
        history = self.get_history(session_id, load_from_disk=False)
        
        if history is None:
            history = self.create_history(session_id)
        
        history.add_message(role, content, metadata, intent_type, confidence)
        self._histories[session_id] = history
        self._save_to_disk(session_id, history)
    
    def get_messages(
        self,
        session_id: str,
        limit: int = None
    ) -> List[Dict]:
        """获取消息列表"""
        history = self.get_history(session_id)
        if history:
            return history.get_messages(limit)
        return []
    
    def get_context_window(
        self,
        session_id: str,
        window_size: int = 5
    ) -> List[Dict]:
        """
        获取上下文窗口
        
        Args:
            session_id: 会话ID
            window_size: 窗口大小
            
        Returns:
            最近N条消息
        """
        return self.get_messages(session_id, limit=window_size)
    
    def search_history(
        self,
        session_id: str,
        keyword: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        搜索历史记录
        
        Args:
            session_id: 会话ID
            keyword: 关键词
            limit: 返回数量
            
        Returns:
            匹配的消息
        """
        history = self.get_history(session_id)
        if not history:
            return []
        
        results = []
        for msg in history.messages:
            if keyword.lower() in msg.content.lower():
                results.append(msg.to_dict())
                if len(results) >= limit:
                    break
        
        return results
    
    def get_session_summary(
        self,
        session_id: str
    ) -> Dict:
        """获取会话摘要"""
        history = self.get_history(session_id)
        if not history:
            return {}
        
        user_messages = [m for m in history.messages if m.role == "user"]
        assistant_messages = [m for m in history.messages if m.role == "assistant"]
        
        # 提取涉及的实体
        entities = []
        for msg in history.messages:
            if msg.metadata.get("entities"):
                entities.extend(msg.metadata["entities"])
        
        return {
            "session_id": session_id,
            "message_count": len(history.messages),
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "entities_mentioned": list(set(entities)),
            "created_at": history.created_at,
            "updated_at": history.updated_at
        }
    
    def delete_history(self, session_id: str) -> bool:
        """删除对话历史"""
        if session_id in self._histories:
            del self._histories[session_id]
        
        # 删除磁盘文件
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    def list_sessions(self, user_id: str = None) -> List[str]:
        """列出会话ID"""
        sessions = set(self._histories.keys())
        
        # 扫描磁盘上的会话
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                sessions.add(session_id)
        
        # 按用户过滤
        if user_id:
            filtered = []
            for sid in sessions:
                history = self.get_history(sid)
                if history and history.user_id == user_id:
                    filtered.append(sid)
            return filtered
        
        return list(sessions)
    
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        清理旧会话
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的会话数量
        """
        now = datetime.now()
        cleaned = 0
        
        sessions = self.list_sessions()
        
        for session_id in sessions:
            history = self.get_history(session_id)
            if history:
                created = datetime.fromisoformat(history.created_at)
                age_days = (now - created).days
                
                if age_days > max_age_days:
                    self.delete_history(session_id)
                    cleaned += 1
        
        return cleaned
    
    def _save_to_disk(self, session_id: str, history: DialogueHistory):
        """保存到磁盘"""
        try:
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _load_from_disk(self, session_id: str) -> Optional[DialogueHistory]:
        """从磁盘加载"""
        try:
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return DialogueHistory.from_dict(data)
        except Exception:
            pass
        return None


# 全局实例
_memory: Optional[DialogueMemory] = None


def get_dialogue_memory(storage_path: str = None) -> DialogueMemory:
    """获取对话记忆管理器"""
    global _memory
    if _memory is None:
        _memory = DialogueMemory(storage_path)
    return _memory
