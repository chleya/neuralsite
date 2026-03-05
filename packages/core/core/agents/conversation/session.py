# -*- coding: utf-8 -*-
"""
会话管理模块

提供会话创建、保存、恢复、多会话支持功能
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: str = ""
    project_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = SessionStatus.ACTIVE.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 当前交互的实体信息
    current_entities: List[Dict[str, Any]] = field(default_factory=list)
    current_chainage: Optional[str] = None
    current_station: Optional[int] = None
    
    # 交互历史摘要
    topic_stack: List[str] = field(default_factory=list)  # 话题栈
    referenced_entities: List[str] = field(default_factory=list)  # 引用过的实体
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SessionContext":
        """从字典创建"""
        return cls(**data)


class SessionManager:
    """会话管理器"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化会话管理器
        
        Args:
            storage_path: 会话存储路径（可选）
        """
        self.storage_path = storage_path
        self._sessions: Dict[str, SessionContext] = {}
        self._active_session: Optional[str] = None
        
    def create_session(
        self, 
        user_id: str = "default",
        project_id: str = "",
        metadata: Dict[str, Any] = None
    ) -> SessionContext:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            metadata: 额外元数据
            
        Returns:
            新创建的会话上下文
        """
        session_id = str(uuid.uuid4())
        
        ctx = SessionContext(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            metadata=metadata or {}
        )
        
        self._sessions[session_id] = ctx
        self._active_session = session_id
        
        # 如果有存储路径，保存到磁盘
        if self.storage_path:
            self._save_to_disk(session_id, ctx)
        
        return ctx
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def get_active_session(self) -> Optional[SessionContext]:
        """获取当前活动会话"""
        if self._active_session:
            return self._sessions.get(self._active_session)
        return None
    
    def set_active_session(self, session_id: str) -> bool:
        """设置活动会话"""
        if session_id in self._sessions:
            self._active_session = session_id
            return True
        return False
    
    def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[SessionContext]:
        """
        更新会话
        
        Args:
            session_id: 会话ID
            updates: 更新内容
            
        Returns:
            更新后的会话，如果不存在返回None
        """
        ctx = self._sessions.get(session_id)
        if not ctx:
            return None
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)
        
        ctx.updated_at = datetime.now().isoformat()
        
        # 保存到磁盘
        if self.storage_path:
            self._save_to_disk(session_id, ctx)
        
        return ctx
    
    def update_context(
        self,
        session_id: str = None,
        current_chainage: str = None,
        current_station: int = None,
        entities: List[Dict[str, Any]] = None,
        topic: str = None,
        referenced_entity: str = None
    ) -> Optional[SessionContext]:
        """
        快速更新会话上下文
        
        Args:
            session_id: 会话ID（默认当前活动会话）
            current_chainage: 当前桩号
            current_station: 当前桩号（米）
            entities: 当前实体列表
            topic: 当前话题
            referenced_entity: 引用的实体
            
        Returns:
            更新后的会话
        """
        if session_id is None:
            session_id = self._active_session
        
        ctx = self._sessions.get(session_id)
        if not ctx:
            return None
        
        if current_chainage is not None:
            ctx.current_chainage = current_chainage
        if current_station is not None:
            ctx.current_station = current_station
        if entities is not None:
            ctx.current_entities = entities
        if topic is not None:
            if not ctx.topic_stack or ctx.topic_stack[-1] != topic:
                ctx.topic_stack.append(topic)
        if referenced_entity is not None:
            if referenced_entity not in ctx.referenced_entities:
                ctx.referenced_entities.append(referenced_entity)
        
        ctx.updated_at = datetime.now().isoformat()
        
        return ctx
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        ctx = self._sessions.get(session_id)
        if ctx:
            ctx.status = SessionStatus.CLOSED.value
            ctx.updated_at = datetime.now().isoformat()
            if self._active_session == session_id:
                self._active_session = None
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            if self._active_session == session_id:
                self._active_session = None
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(
        self, 
        user_id: str = None,
        status: SessionStatus = None
    ) -> List[SessionContext]:
        """
        列出会话
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            
        Returns:
            匹配的会话列表
        """
        sessions = list(self._sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        if status:
            sessions = [s for s in sessions if s.status == status.value]
        
        return sessions
    
    def _save_to_disk(self, session_id: str, ctx: SessionContext):
        """保存到磁盘"""
        import os
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(ctx.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 静默失败
    
    def load_from_disk(self, session_id: str) -> Optional[SessionContext]:
        """从磁盘加载会话"""
        import os
        if not self.storage_path:
            return None
        
        try:
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    ctx = SessionContext.from_dict(data)
                    self._sessions[session_id] = ctx
                    return ctx
        except Exception:
            pass
        return None
    
    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        清理过期会话
        
        Args:
            max_age_hours: 最大保留小时数
            
        Returns:
            清理的会话数量
        """
        now = datetime.now()
        cleaned = 0
        
        for session_id, ctx in list(self._sessions.items()):
            created = datetime.fromisoformat(ctx.created_at)
            age_hours = (now - created).total_seconds() / 3600
            
            if age_hours > max_age_hours and ctx.status != SessionStatus.ACTIVE.value:
                self.delete_session(session_id)
                cleaned += 1
        
        return cleaned


# 全局会话管理器实例
_session_manager: Optional[SessionManager] = None


def get_session_manager(storage_path: str = None) -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(storage_path)
    return _session_manager


def create_session(
    user_id: str = "default",
    project_id: str = ""
) -> SessionContext:
    """创建新会话的便捷函数"""
    return get_session_manager().create_session(user_id, project_id)


def get_current_session() -> Optional[SessionContext]:
    """获取当前会话"""
    return get_session_manager().get_active_session()
