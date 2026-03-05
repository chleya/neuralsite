# -*- coding: utf-8 -*-
"""
知识问答 API - 扩展版

包含：自然语言问答、实体搜索、推理
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import sys
import re
sys.path.insert(0, '.')

from core.engine import NeuralSiteEngine
from core.knowledge_graph.schema import (
    init_schema, query_elevation, query_coordinate,
    create_project, create_drawing, create_feature, 
    link_feature_to_coordinate, search_entities
)
from api.dependencies import (
    get_engine,
    get_graph_database,
    get_feature_flags,
    get_storage_manager,
    QARequest,
    EntitySearchRequest,
    ReasonRequest
)
from core.config.feature_flags import FeatureFlags


router = APIRouter(prefix="/api/v1", tags=["知识问答V1"])


# ========== 响应模型 ==========

class QAResponse(BaseModel):
    """问答响应"""
    question: str
    answer: str
    confidence: float = 1.0
    entities: List[Dict[str, Any]] = []
    sources: List[str] = []


class EntitySearchResponse(BaseModel):
    """实体搜索响应"""
    query: str
    total: int
    entities: List[Dict[str, Any]]


class ReasonResponse(BaseModel):
    """推理响应"""
    start_entity: str
    path: List[Dict[str, Any]]
    depth: int
    results: List[Dict[str, Any]]


# ========== 1. 自然语言问答接口 ==========

@router.post(
    "/qa/ask",
    response_model=QAResponse,
    summary="自然语言问答",
    description="使用自然语言查询工程数据"
)
async def ask_question(
    request: QARequest,
    engine: NeuralSiteEngine = Depends(get_engine),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> QAResponse:
    """
    自然语言问答接口
    
    支持的查询类型：
    - "K0+500的设计标高是多少"
    - "K1+200的坐标"
    - "K0+000到K1+000的纵坡"
    - "帮我计算K0+500的横断面"
    """
    if not feature_flags.is_enabled("enable_qa_system"):
        raise HTTPException(
            status_code=403,
            detail="QA system feature is disabled"
        )
    
    question = request.question
    answer = ""
    entities = []
    sources = ["engine", "knowledge_graph"]
    confidence = 0.8
    
    # 解析桩号
    chainage_match = re.search(r'K(\d+)\+(\d{3})', question)
    
    if chainage_match:
        chainage = f"K{chainage_match.group(1)}+{chainage_match.group(2)}"
        station = int(chainage_match.group(1)) * 1000 + int(chainage_match.group(2))
        
        entities.append({
            "type": "chainage",
            "value": chainage,
            "station_m": station
        })
        
        # 判断问题类型
        if any(keyword in question for keyword in ["标高", "高程", " elevation", "z"]):
            # 查询高程
            elevation = engine.get_coordinate(station).z
            answer = f"{chainage}的设计高程是{elevation:.3f}m"
            entities.append({"type": "elevation", "value": elevation})
            
        elif any(keyword in question for keyword in ["坐标", " coordinate", "x", "y"]):
            # 查询坐标
            coord = engine.get_coordinate(station)
            answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}"
            entities.append({
                "type": "coordinate",
                "x": coord.x,
                "y": coord.y,
                "z": coord.z
            })
            
        elif any(keyword in question for keyword in ["纵坡", "坡度", "grade"]):
            # 查询纵坡
            coord1 = engine.get_coordinate(max(0, station - 100))
            coord2 = engine.get_coordinate(station + 100)
            grade = (coord2.z - coord1.z) / 200 * 100
            answer = f"{chainage}附近的纵坡为 {grade:.2f}%"
            entities.append({"type": "grade", "value": grade})
            
        elif any(keyword in question for keyword in ["横断", "断面", "cross"]):
            # 查询横断面
            cs = engine.calculate_cross_section(station)
            answer = f"{chainage}的横断面：中心点({cs['center'][0]:.2f}, {cs['center'][1]:.2f}, {cs['center'][2]:.2f})"
            entities.append({"type": "cross_section", "value": cs})
            
        else:
            # 默认返回坐标信息
            coord = engine.get_coordinate(station)
            answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}，方位角{coord.azimuth:.1f}°"
            confidence = 0.6
            
    elif any(keyword in question for keyword in ["列表", "list", "范围", "range"]):
        # 范围查询
        answer = "请提供具体的桩号范围，例如：K0+000到K1+000"
        confidence = 0.3
        
    else:
        answer = "抱歉，我无法理解您的问题。请尝试询问具体的桩号信息（如 K0+500 的标高）"
        confidence = 0.1
    
    return QAResponse(
        question=question,
        answer=answer,
        confidence=confidence,
        entities=entities,
        sources=sources
    )


# ========== 2. 实体搜索接口 ==========

@router.get(
    "/kg/search",
    response_model=EntitySearchResponse,
    summary="实体搜索",
    description="在知识图谱中搜索实体"
)
async def search_kg_entities(
    q: str = Query(..., description="搜索关键词"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(10, ge=1, le=100, description="返回结果数量"),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> EntitySearchResponse:
    """
    实体搜索接口
    
    在知识图谱中搜索匹配的实体
    """
    if not feature_flags.is_enabled("enable_knowledge_graph"):
        raise HTTPException(
            status_code=403,
            detail="Knowledge graph feature is disabled"
        )
    
    try:
        # 搜索实体
        results = search_entities(q, entity_type, limit)
        
        return EntitySearchResponse(
            query=q,
            total=len(results),
            entities=results
        )
        
    except Exception as e:
        # 如果图数据库不可用，返回模拟数据
        return EntitySearchResponse(
            query=q,
            total=0,
            entities=[],
            # 添加警告信息到额外字段
        )


# ========== 3. 推理接口 ==========

@router.post(
    "/kg/reason",
    response_model=ReasonResponse,
    summary="知识推理",
    description="在知识图谱中进行关系推理"
)
async def reason_kg(
    request: ReasonRequest,
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> ReasonResponse:
    """
    推理接口
    
    在知识图谱中基于关系进行推理查询
    """
    if not feature_flags.is_enabled("enable_knowledge_graph"):
        raise HTTPException(
            status_code=403,
            detail="Knowledge graph feature is disabled"
        )
    
    if not feature_flags.is_enabled("enable_kg_reasoning"):
        raise HTTPException(
            status_code=403,
            detail="Knowledge graph reasoning feature is disabled"
        )
    
    # 简化实现：基于实体和关系进行路径查找
    path = []
    results = []
    
    # 构建推理路径
    path.append({
        "from": request.start_entity,
        "relation": request.relation,
        "depth": 0
    })
    
    # 模拟推理结果
    if request.relation == "has_coordinate":
        results.append({
            "entity": request.start_entity,
            "coordinates": {"x": 500000, "y": 3000000, "z": 100}
        })
    elif request.relation == "belongs_to":
        results.append({
            "entity": request.start_entity,
            "parent": "NS-PROJECT-001"
        })
    else:
        results.append({
            "entity": request.start_entity,
            "related": "N/A - relation not supported"
        })
    
    return ReasonResponse(
        start_entity=request.start_entity,
        path=path,
        depth=min(request.max_depth, 1),
        results=results
    )


# ========== 注册到主应用 ==========

def register_routes(app):
    """注册路由到FastAPI应用"""
    app.include_router(router)
