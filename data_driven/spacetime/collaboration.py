# -*- coding: utf-8 -*-
"""
协作与会话管理模块
对应V1.1规格书 - 第3周任务
解决多方同时编辑冲突
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json


@dataclass
class CollaborationLock:
    """协作锁"""
    id: UUID = field(default_factory=uuid4)
    entity_id: str = ""
    user_id: str = ""
    session_id: UUID = field(default_factory=uuid4)
    locked_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    lock_type: str = "edit"  # edit / review / simulate


@dataclass
class OperationLog:
    """操作日志"""
    id: UUID = field(default_factory=uuid4)
    entity_id: str = ""
    user_id: str = ""
    operation_type: str = ""  # update_state / upload_photo / resolve_issue / simulate
    before_snapshot: Dict = field(default_factory=dict)
    after_snapshot: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self, lock_timeout_minutes: int = 10):
        self.locks: Dict[str, CollaborationLock] = {}  # entity_id -> lock
        self.operation_logs: List[OperationLog] = []
        self.lock_timeout = timedelta(minutes=lock_timeout_minutes)
        self.sessions: Dict[UUID, Dict] = {}  # session_id -> user info
    
    # ========== 会话管理 ==========
    
    def join_session(self, user_id: str, project_id: str) -> UUID:
        """用户加入会话"""
        session_id = uuid4()
        self.sessions[session_id] = {
            'user_id': user_id,
            'project_id': project_id,
            'joined_at': datetime.now(),
            'last_active': datetime.now(),
            'current_station': None,
            'cursor_position': None
        }
        return session_id
    
    def leave_session(self, session_id: UUID):
        """用户离开会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # 释放该用户的所有锁
        locks_to_release = [
            lock_id for lock_id, lock in self.locks.items()
            if lock.session_id == session_id
        ]
        for lock_id in locks_to_release:
            del self.locks[lock_id]
    
    def update_cursor(self, session_id: UUID, station: float = None, lateral: float = None):
        """更新光标位置"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_active'] = datetime.now()
            if station is not None:
                self.sessions[session_id]['current_station'] = station
            if lateral is not None:
                self.sessions[session_id]['cursor_position'] = {'station': station, 'lateral': lateral}
    
    def get_active_users(self, project_id: str) -> List[Dict]:
        """获取项目中的在线用户"""
        users = []
        for session_id, info in self.sessions.items():
            if info['project_id'] == project_id:
                users.append({
                    'session_id': str(session_id),
                    'user_id': info['user_id'],
                    'current_station': info.get('current_station'),
                    'cursor_position': info.get('cursor_position'),
                    'last_active': info['last_active'].isoformat()
                })
        return users
    
    # ========== 锁管理 ==========
    
    def acquire_lock(self, entity_id: str, user_id: str, session_id: UUID, 
                   lock_type: str = "edit") -> Dict:
        """
        获取实体锁
        对应V1.1: 解决多方同时编辑冲突
        """
        # 检查是否已有锁
        if entity_id in self.locks:
            existing_lock = self.locks[entity_id]
            
            # 检查锁是否过期
            if existing_lock.expires_at and datetime.now() > existing_lock.expires_at:
                # 锁已过期，释放
                del self.locks[entity_id]
            elif existing_lock.session_id != session_id:
                # 锁被其他人持有
                return {
                    'success': False,
                    'locked_by': existing_lock.user_id,
                    'locked_at': existing_lock.locked_at.isoformat(),
                    'expires_at': existing_lock.expires_at.isoformat() if existing_lock.expires_at else None,
                    'message': f"该实体正被 {existing_lock.user_id} 锁定"
                }
        
        # 创建新锁
        lock = CollaborationLock(
            entity_id=entity_id,
            user_id=user_id,
            session_id=session_id,
            lock_type=lock_type,
            expires_at=datetime.now() + self.lock_timeout
        )
        self.locks[entity_id] = lock
        
        return {
            'success': True,
            'lock_id': str(lock.id),
            'expires_at': lock.expires_at.isoformat()
        }
    
    def release_lock(self, entity_id: str, session_id: UUID) -> bool:
        """释放锁"""
        if entity_id in self.locks:
            lock = self.locks[entity_id]
            if lock.session_id == session_id:
                del self.locks[entity_id]
                return True
        return False
    
    def get_lock_status(self, entity_id: str) -> Optional[Dict]:
        """获取锁状态"""
        if entity_id in self.locks:
            lock = self.locks[entity_id]
            return {
                'locked': True,
                'user_id': lock.user_id,
                'lock_type': lock.lock_type,
                'locked_at': lock.locked_at.isoformat(),
                'expires_at': lock.expires_at.isoformat() if lock.expires_at else None
            }
        return {'locked': False}
    
    # ========== 操作日志 ==========
    
    def log_operation(self, entity_id: str, user_id: str, operation_type: str,
                    before: Dict = None, after: Dict = None):
        """记录操作"""
        log = OperationLog(
            entity_id=entity_id,
            user_id=user_id,
            operation_type=operation_type,
            before_snapshot=before or {},
            after_snapshot=after or {}
        )
        self.operation_logs.append(log)
        
        # 保留最近1000条
        if len(self.operation_logs) > 1000:
            self.operation_logs = self.operation_logs[-1000:]
        
        return str(log.id)
    
    def get_entity_history(self, entity_id: str, limit: int = 20) -> List[Dict]:
        """获取实体的操作历史"""
        logs = [l for l in self.operation_logs if l.entity_id == entity_id]
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                'id': str(l.id),
                'user_id': l.user_id,
                'operation_type': l.operation_type,
                'before': l.before_snapshot,
                'after': l.after_snapshot,
                'timestamp': l.timestamp.isoformat()
            }
            for l in logs[:limit]
        ]
    
    # ========== 冲突解决 ==========
    
    def safe_update_state(self, entity_id: str, user_id: str, session_id: UUID,
                         new_data: Dict, expected_version: int = None) -> Dict:
        """
        安全更新状态（带乐观锁）
        对应V1.1: 冲突自动合并
        """
        # 先获取锁
        lock_result = self.acquire_lock(entity_id, user_id, session_id)
        if not lock_result['success']:
            return {
                'status': 'conflict',
                'message': lock_result['message'],
                'locked_by': lock_result.get('locked_by')
            }
        
        # 获取当前状态（从日志推断）
        history = self.get_entity_history(entity_id, limit=1)
        current_version = 1
        if history:
            current_version = int(history[0].get('version_number', 1)) + 1
        
        # 版本检查
        if expected_version and expected_version != current_version:
            # 冲突！自动合并
            merged_data = self._merge_states(history[0]['after'] if history else {}, new_data)
            
            # 记录合并后的操作
            self.log_operation(
                entity_id, user_id, 'update_state',
                history[0]['after'] if history else {},
                merged_data
            )
            
            # 释放锁
            self.release_lock(entity_id, session_id)
            
            return {
                'status': 'conflict_merged',
                'version': current_version + 1,
                'merged_data': merged_data,
                'message': '检测到冲突，已自动合并'
            }
        
        # 无冲突，正常更新
        self.log_operation(
            entity_id, user_id, 'update_state',
            history[0]['after'] if history else {},
            new_data
        )
        
        # 释放锁
        self.release_lock(entity_id, session_id)
        
        return {
            'status': 'success',
            'version': current_version + 1,
            'message': '状态更新成功'
        }
    
    def _merge_states(self, current: Dict, new: Dict) -> Dict:
        """合并状态（简单规则：进度取最大值，标签取最新）"""
        merged = current.copy()
        
        # 进度取最大值
        if 'progress' in current and 'progress' in new:
            merged['progress'] = max(current['progress'], new['progress'])
        
        # 标签取最新
        if 'status' in new:
            merged['status'] = new['status']
        
        # 合并spatial_snapshot
        if 'spatial_snapshot' in new:
            merged['spatial_snapshot'] = {**current.get('spatial_snapshot', {}), **new['spatial_snapshot']}
        
        return merged


# 测试
if __name__ == "__main__":
    manager = CollaborationManager()
    
    # 1. 用户加入
    session1 = manager.join_session("张施工", "project-001")
    session2 = manager.join_session("李监理", "project-001")
    print(f"Users online: {len(manager.get_active_users('project-001'))}")
    
    # 2. 尝试加锁
    result1 = manager.acquire_lock("entity-001", "张施工", session1)
    print(f"Lock result (user1): {result1}")
    
    result2 = manager.acquire_lock("entity-001", "李监理", session2)
    print(f"Lock result (user2): {result2}")
    
    # 3. 更新状态（有冲突）
    result3 = manager.safe_update_state(
        "entity-001", "李监理", session2,
        {'progress': 90, 'status': 'completed'},
        expected_version=1
    )
    print(f"Safe update: {result3}")
    
    # 4. 查看历史
    history = manager.get_entity_history("entity-001")
    print(f"History: {len(history)} records")
    
    # 5. 释放锁
    manager.release_lock("entity-001", session1)
    print(f"Lock released, status: {manager.get_lock_status('entity-001')}")
