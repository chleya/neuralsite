# -*- coding: utf-8 -*-
"""
数据接口模块

包含:
- REST API: 基于FastAPI的HTTP接口
- WebSocket: 实时数据订阅
"""

__version__ = "1.0.0"

from .rest import router, create_rest_routes
from .models import (
    Project, ProjectCreate, ProjectResponse,
    SpatialStation, SpatialStationResponse,
    ChainRecord, ChainRecordCreate, ChainRecordResponse,
    Entity, EntityResponse,
    Photo, PhotoCreate, PhotoResponse,
    Issue, IssueCreate, IssueResponse
)
from .websocket import (
    manager,
    subscription_manager,
    ConnectionManager,
    DataSubscriptionManager,
    EventType,
    websocket_endpoint,
    publish_project_event,
    publish_entity_event,
    publish_photo_event,
    publish_issue_event,
    publish_chain_event
)

__all__ = [
    # 版本
    "__version__",
    
    # REST
    "router",
    "create_rest_routes",
    
    # 模型
    "Project", "ProjectCreate", "ProjectResponse",
    "SpatialStation", "SpatialStationResponse",
    "ChainRecord", "ChainRecordCreate", "ChainRecordResponse",
    "Entity", "EntityResponse",
    "Photo", "PhotoCreate", "PhotoResponse",
    "Issue", "IssueCreate", "IssueResponse",
    
    # WebSocket
    "manager",
    "subscription_manager",
    "ConnectionManager",
    "DataSubscriptionManager",
    "EventType",
    "websocket_endpoint",
    "publish_project_event",
    "publish_entity_event",
    "publish_photo_event",
    "publish_issue_event",
    "publish_chain_event",
]
