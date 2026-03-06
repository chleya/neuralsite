# -*- coding: utf-8 -*-
"""
WebSocket 数据订阅模块
实现实时数据变更推送
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect


class EventType(str, Enum):
    """事件类型"""
    # 项目事件
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    
    # 实体事件
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"
    
    # 照片事件
    PHOTO_UPLOADED = "photo.uploaded"
    PHOTO_VERIFIED = "photo.verified"
    
    # 问题事件
    ISSUE_CREATED = "issue.created"
    ISSUE_UPDATED = "issue.updated"
    ISSUE_RESOLVED = "issue.resolved"
    
    # 区块链事件
    CHAIN_RECORDED = "chain.recorded"
    CHAIN_VERIFIED = "chain.verified 空间数据"
    
    #事件
    STATION_UPDATED = "station.updated"
    
    # 系统事件
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEARTBEAT = "system.heartbeat"


@dataclass
class Subscription:
    """订阅信息"""
    websocket: WebSocket
    event_types: Set[str] = field(default_factory=set)
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    connected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class EventMessage:
    """事件消息"""
    event_type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "data_interface"


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接
        self.active_connections: Dict[WebSocket, Subscription] = {}
        
        # 事件订阅: event_type -> set of WebSockets
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # 用户订阅: user_id -> set of WebSockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
        # 项目订阅: project_id -> set of WebSockets
        self.project_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket) -> Subscription:
        """
        处理新连接
        
        Args:
            websocket: WebSocket连接
            
        Returns:
            Subscription对象
        """
        await websocket.accept()
        
        # 创建订阅对象
        subscription = Subscription(websocket=websocket)
        self.active_connections[websocket] = subscription
        
        return subscription
    
    def disconnect(self, websocket: WebSocket):
        """
        处理断开连接
        
        Args:
            websocket: WebSocket连接
        """
        if websocket in self.active_connections:
            subscription = self.active_connections[websocket]
            
            # 从所有订阅中移除
            for event_type in subscription.event_types:
                if event_type in self.subscriptions:
                    self.subscriptions[event_type].discard(websocket)
            
            # 从用户订阅中移除
            if subscription.user_id and subscription.user_id in self.user_connections:
                self.user_connections[subscription.user_id].discard(websocket)
            
            # 从项目订阅中移除
            if subscription.project_id and subscription.project_id in self.project_connections:
                self.project_connections[subscription.project_id].discard(websocket)
            
            del self.active_connections[websocket]
    
    async def subscribe(
        self, 
        websocket: WebSocket, 
        event_types: Set[str],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        订阅事件
        
        Args:
            websocket: WebSocket连接
            event_types: 事件类型集合
            user_id: 用户ID（可选）
            project_id: 项目ID（可选）
        """
        if websocket not in self.active_connections:
            raise ValueError("WebSocket not connected")
        
        subscription = self.active_connections[websocket]
        
        # 添加事件类型订阅
        for event_type in event_types:
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = set()
            self.subscriptions[event_type].add(websocket)
        
        subscription.event_types.update(event_types)
        
        # 添加用户订阅
        if user_id:
            subscription.user_id = user_id
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        # 添加项目订阅
        if project_id:
            subscription.project_id = project_id
            if project_id not in self.project_connections:
                self.project_connections[project_id] = set()
            self.project_connections[project_id].add(websocket)
    
    async def unsubscribe(self, websocket: WebSocket, event_types: Optional[Set[str]] = None):
        """
        取消订阅
        
        Args:
            websocket: WebSocket连接
            event_types: 要取消的事件类型（None表示取消所有）
        """
        if websocket not in self.active_connections:
            return
        
        subscription = self.active_connections[websocket]
        
        if event_types is None:
            # 取消所有订阅
            for event_type in subscription.event_types:
                if event_type in self.subscriptions:
                    self.subscriptions[event_type].discard(websocket)
            subscription.event_types.clear()
        else:
            # 取消指定订阅
            for event_type in event_types:
                if event_type in self.subscriptions:
                    self.subscriptions[event_type].discard(websocket)
                subscription.event_types.discard(event_type)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        发送个人消息
        
        Args:
            message: 消息内容
            websocket: 目标WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            # 连接可能已关闭
            self.disconnect(websocket)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """
        向指定用户发送消息
        
        Args:
            message: 消息内容
            user_id: 用户ID
        """
        if user_id in self.user_connections:
            tasks = [
                self.send_personal_message(message, ws)
                for ws in self.user_connections[user_id]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_project(self, message: Dict[str, Any], project_id: str):
        """
        向指定项目相关用户发送消息
        
        Args:
            message: 消息内容
            project_id: 项目ID
        """
        if project_id in self.project_connections:
            tasks = [
                self.send_personal_message(message, ws)
                for ws in self.project_connections[project_id]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish(self, event_type: str, data: Dict[str, Any], target: Optional[str] = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            target: 目标用户或项目ID（可选）
        """
        message = EventMessage(
            event_type=event_type,
            data=data
        )
        
        message_dict = {
            "event_type": message.event_type,
            "data": message.data,
            "timestamp": message.timestamp,
            "source": message.source
        }
        
        # 发送给特定用户
        if target and target in self.user_connections:
            await self.send_to_user(message_dict, target)
            return
        
        # 发送给特定项目
        if target and target in self.project_connections:
            await self.send_to_project(message_dict, target)
            return
        
        # 广播给所有订阅该事件类型的客户端
        if event_type in self.subscriptions:
            tasks = [
                self.send_personal_message(message_dict, ws)
                for ws in self.subscriptions[event_type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息给所有连接
        
        Args:
            message: 消息内容
        """
        tasks = [
            self.send_personal_message(message, ws)
            for ws in self.active_connections.keys()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)
    
    def get_subscriber_count(self, event_type: str) -> int:
        """获取指定事件的订阅者数量"""
        return len(self.subscriptions.get(event_type, set()))


class DataSubscriptionManager:
    """
    数据订阅管理器（兼容旧接口）
    
    简化版接口，保持向后兼容
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self._manager: Optional[ConnectionManager] = None
    
    def set_manager(self, manager: ConnectionManager):
        """设置连接管理器"""
        self._manager = manager
    
    async def subscribe(self, websocket: WebSocket, event_type: str):
        """订阅数据变更"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()
        self.subscriptions[event_type].add(websocket)
        
        # 同时更新manager
        if self._manager and websocket in self._manager.active_connections:
            await self._manager.subscribe(websocket, {event_type})
    
    async def unsubscribe(self, websocket: WebSocket, event_type: str):
        """取消订阅"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(websocket)
    
    async def publish(self, event_type: str, data: dict):
        """发布数据变更"""
        if event_type in self.subscriptions:
            tasks = [
                ws.send_json({
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                for ws in self.subscriptions[event_type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)


# 全局连接管理器实例
manager = ConnectionManager()
subscription_manager = DataSubscriptionManager()
subscription_manager.set_manager(manager)


# ==================== WebSocket 端点处理 ====================

async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点
    
    处理连接、订阅和消息收发
    """
    subscription = await manager.connect(websocket)
    
    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket连接已建立",
            "connection_id": id(websocket),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 处理消息循环
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(websocket, message, subscription)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # 发送错误消息
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass
        manager.disconnect(websocket)


async def handle_websocket_message(
    websocket: WebSocket, 
    message: Dict[str, Any],
    subscription: Subscription
):
    """
    处理WebSocket消息
    
    支持的操作:
    - subscribe: 订阅事件
    - unsubscribe: 取消订阅
    - ping: 心跳
    """
    msg_type = message.get("type")
    
    if msg_type == "subscribe":
        # 订阅事件
        event_types = message.get("events", [])
        user_id = message.get("user_id")
        project_id = message.get("project_id")
        
        await manager.subscribe(
            websocket, 
            set(event_types),
            user_id,
            project_id
        )
        
        await websocket.send_json({
            "type": "subscribed",
            "events": event_types,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif msg_type == "unsubscribe":
        # 取消订阅
        event_types = message.get("events")
        await manager.unsubscribe(websocket, set(event_types) if event_types else None)
        
        await websocket.send_json({
            "type": "unsubscribed",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif msg_type == "ping":
        # 心跳
        await websocket.send_json({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    else:
        # 未知消息类型
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
            "timestamp": datetime.utcnow().isoformat()
        })


# ==================== 便捷发布函数 ====================

async def publish_project_event(event_type: str, project_data: Dict[str, Any]):
    """发布项目事件"""
    await manager.publish(event_type, project_data)


async def publish_entity_event(event_type: str, entity_data: Dict[str, Any]):
    """发布实体事件"""
    await manager.publish(event_type, entity_data)


async def publish_photo_event(event_type: str, photo_data: Dict[str, Any]):
    """发布照片事件"""
    await manager.publish(event_type, photo_data)


async def publish_issue_event(event_type: str, issue_data: Dict[str, Any]):
    """发布问题事件"""
    await manager.publish(event_type, issue_data)


async def publish_chain_event(event_type: str, chain_data: Dict[str, Any]):
    """发布区块链事件"""
    await manager.publish(event_type, chain_data)
