# -*- coding: utf-8 -*-
"""
NeuralSite 核心引擎模块

核心模块:
- geometry: 几何计算引擎
- spatial: 空间数据引擎
- ai_detection: AI质量检测
- knowledge_graph: 知识图谱
- events: 事件发布订阅机制
- sync: 跨库同步协调

使用方式:
    from core import NeuralSiteEngine
    from core.geometry import HorizontalAlignment
    from core.spatial import ChainageTransformer
"""

# 核心引擎
from .engine import NeuralSiteEngine, Coordinate3D, LODConfig

# 几何计算
from .geometry import (
    HorizontalAlignment,
    VerticalAlignment,
    CrossSectionCalculator,
    LineElement,
    CircularCurveElement,
    SpiralCurveElement,
    VerticalCurveElement,
)

# 空间数据
from .spatial import (
    ChainageTransformer,
    RTree,
    LODManager,
)

# AI检测
from .ai_detection import (
    DefectDetector,
    ImageClassifier,
    DetectionResult,
)

# 知识图谱
from .knowledge_graph import (
    Entity,
    Relationship,
    KnowledgeGraphStore,
)

# 事件
from .events import (
    EntityEvent,
    EntityCreatedEvent,
    EntityUpdatedEvent,
    EntityDeletedEvent,
    RelationshipEvent,
    EntityEventPublisher,
    get_event_publisher,
)

# 同步
from .sync import (
    SyncCoordinator,
    DataConsistencyContract,
    EntityMappingRule,
    ReconciliationTask,
    get_reconciliation_scheduler,
)

__all__ = [
    # Engine
    "NeuralSiteEngine",
    "Coordinate3D",
    "LODConfig",
    # Geometry
    "HorizontalAlignment",
    "VerticalAlignment",
    "CrossSectionCalculator",
    "LineElement",
    "CircularCurveElement",
    "SpiralCurveElement",
    "VerticalCurveElement",
    # Spatial
    "ChainageTransformer",
    "RTreeIndex",
    "LODManager",
    # AI Detection
    "DefectDetector",
    "ImageClassifier",
    "DetectionResult",
    # Knowledge Graph
    "Entity",
    "Relationship",
    "KnowledgeGraphStore",
    # Events
    "EntityEvent",
    "EntityCreatedEvent",
    "EntityUpdatedEvent",
    "EntityDeletedEvent",
    "RelationshipEvent",
    "EntityEventPublisher",
    "get_event_publisher",
    # Sync
    "SyncCoordinator",
    "DataConsistencyContract",
    "EntityMappingRule",
    "ReconciliationTask",
    "get_reconciliation_scheduler",
]
