# -*- coding: utf-8 -*-
"""
知识图谱模块

Entities:
- Standard (规范): 道路工程设计规范、施工规范
- Process (工艺): 施工工艺、操作流程
- Material (材料): 材料规格、性能参数
- QualityStandard (质量标准): 质量检验标准、验收指标

Relationships:
- CONTAINS (包含): 规范包含章节、章节包含条款
- DEPENDS_ON (依赖): 工艺依赖材料、前置工艺
- APPLIES_TO (适用于): 规范适用于道路类型
- REQUIRES (前置): 工艺需要前置工艺、材料需要存储条件
"""

from .entities import (
    Entity, Standard, Process, Material, QualityStandard,
    EntityType
)
from .relationships import (
    Relationship, RelationshipType,
    CONTAINS, DEPENDS_ON, APPLIES_TO, REQUIRES
)
from .storage_sqlite import KnowledgeGraphStore, get_knowledge_store, init_knowledge_graph
from .crud import KnowledgeGraphCRUD, get_knowledge_crud
from .reasoning import ReasoningEngine, get_reasoning_engine
from .query_builder import QueryBuilder, KnowledgeQueryEngine, create_query_builder, search_knowledge
from .integration import (
    build_knowledge_from_geometry,
    register_knowledge_routes,
    init_knowledge_from_config,
    get_knowledge_summary
)

__all__ = [
    # Entities
    'Entity', 'Standard', 'Process', 'Material', 'QualityStandard',
    'EntityType',
    
    # Relationships
    'Relationship', 'RelationshipType',
    'CONTAINS', 'DEPENDS_ON', 'APPLIES_TO', 'REQUIRES',
    
    # Storage
    'KnowledgeGraphStore', 'get_knowledge_store', 'init_knowledge_graph',
    
    # CRUD
    'KnowledgeGraphCRUD', 'get_knowledge_crud',
    
    # Reasoning
    'ReasoningEngine', 'get_reasoning_engine',
    
    # Query
    'QueryBuilder', 'KnowledgeQueryEngine', 'create_query_builder', 'search_knowledge',
    
    # Integration
    'build_knowledge_from_geometry', 'register_knowledge_routes',
    'init_knowledge_from_config', 'get_knowledge_summary',
]
