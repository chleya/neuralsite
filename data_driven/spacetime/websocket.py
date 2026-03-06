# -*- coding: utf-8 -*-
"""
WebSocket实时推送模块
对应规格书第3周任务
"""
from typing import Dict, List, Callable
import json
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class WSMessage:
    """WebSocket消息"""
    type: str           # state_update/event/new_photo/issue
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(uuid4()))


class WebSocketManager:
    """WebSocket管理器（内存实现）"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {
            'state_update': [],
            'event': [],
            'new_photo': [],
            'issue': [],
            'all': []
        }
        self.message_history: List[WSMessage] = []
    
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type in self.subscribers:
            self.subscribers[event_type].append(callback)
        # 也订阅all
        if 'all' in self.subscribers:
            self.subscribers['all'].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if callback in self.subscribers.get(event_type, []):
            self.subscribers[event_type].remove(callback)
    
    def broadcast(self, event_type: str, payload: dict):
        """广播消息"""
        message = WSMessage(type=event_type, payload=payload)
        self.message_history.append(message)
        
        # 保留最近100条
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        # 通知订阅者
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(message)
            except Exception as e:
                print(f"Callback error: {e}")
        
        # 通知all订阅者
        for callback in self.subscribers.get('all', []):
            try:
                callback(message)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def notify_state_update(self, entity_id: str, state_data: dict):
        """通知状态更新"""
        self.broadcast('state_update', {
            'entity_id': entity_id,
            'state': state_data
        })
    
    def notify_new_photo(self, photo_data: dict):
        """通知新照片"""
        self.broadcast('new_photo', photo_data)
    
    def notify_issue(self, issue_data: dict):
        """通知新问题"""
        self.broadcast('issue', issue_data)
    
    def notify_event(self, event_data: dict):
        """通知新事件"""
        self.broadcast('event', event_data)
    
    def get_history(self, event_type: str = None, limit: int = 20) -> List[Dict]:
        """获取消息历史"""
        messages = self.message_history
        if event_type:
            messages = [m for m in messages if m.type == event_type]
        
        return [
            {
                'id': m.id,
                'type': m.type,
                'payload': m.payload,
                'timestamp': m.timestamp
            }
            for m in messages[-limit:]
        ]


# 全局实例
ws_manager = WebSocketManager()


# 模拟客户端
class MockWebSocketClient:
    """模拟WebSocket客户端"""
    
    def __init__(self, name: str):
        self.name = name
        self.messages: List[WSMessage] = []
    
    def on_message(self, message: WSMessage):
        """收到消息"""
        self.messages.append(message)
        print(f"[{self.name}] Received: {message.type} - {message.payload}")
    
    def subscribe_all(self):
        """订阅所有事件"""
        ws_manager.subscribe('all', self.on_message)


# 测试
if __name__ == "__main__":
    # 创建客户端
    client1 = MockWebSocketClient("Client-1")
    client2 = MockWebSocketClient("Client-2")
    
    # 订阅
    client1.subscribe_all()
    ws_manager.subscribe('state_update', client2.on_message)
    
    # 模拟推送
    print("=== Simulating WebSocket Events ===\n")
    
    ws_manager.notify_state_update('entity-001', {
        'progress': 86,
        'updated_by': 'worker_zhang'
    })
    
    ws_manager.notify_new_photo({
        'photo_url': '/photos/IMG_001.jpg',
        'station': 'K5+200'
    })
    
    ws_manager.notify_issue({
        'issue_type': 'crack',
        'severity': 'medium',
        'station': 'K5+300'
    })
    
    # 查看历史
    print("\n=== Message History ===")
    history = ws_manager.get_history()
    for msg in history:
        print(f"  {msg['type']}: {msg['timestamp']}")
