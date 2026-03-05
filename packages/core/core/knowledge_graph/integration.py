# -*- coding: utf-8 -*-
"""
知识图谱与现有系统集成

1. 与 geometry 模块联动（从设计数据构建知识）
2. 与 API 层对接
"""

from typing import Dict, List, Any, Optional, Callable
import json

from .entities import Entity, EntityType, create_standard, create_process, create_material
from .relationships import RelationshipType, create_references_relation, create_contains_relation
from .storage_sqlite import KnowledgeGraphStore, get_knowledge_store
from .crud import KnowledgeGraphCRUD, get_knowledge_crud


# ========== 与 Geometry 模块集成 ==========

def build_knowledge_from_geometry(
    horizontal_alignment: List[Dict] = None,
    vertical_alignment: List[Dict] = None,
    cross_section: Dict = None,
    store: KnowledgeGraphStore = None
) -> Dict[str, Any]:
    """从几何设计数据构建知识图谱
    
    Args:
        horizontal_alignment: 平曲线数据
        vertical_alignment: 纵曲线数据
        cross_section: 横断面数据
        store: 存储实例
        
    Returns:
        构建结果
    """
    if store is None:
        store = get_knowledge_store()
    
    crud = KnowledgeGraphCRUD(store)
    
    result = {
        "entities_created": [],
        "relationships_created": [],
        "errors": [],
    }
    
    # 1. 分析平曲线，创建知识
    if horizontal_alignment:
        for element in horizontal_alignment:
            element_type = element.get("element_type", "")
            
            if element_type == "圆曲线":
                # 创建圆曲线知识
                radius = element.get("R", 0)
                if radius < 0:
                    result["errors"].append(f"圆曲线半径不能为负: {radius}")
                elif radius < 100:
                    result["errors"].append(f"圆曲线半径过小: {radius}")
                
                # 查找相关规范
                standards = crud.search_entities("曲线半径", EntityType.STANDARD)
                if standards:
                    result["entities_created"].extend(standards)
            
            elif element_type == "缓和曲线":
                A = element.get("A", 0)
                R = element.get("R", 0)
                if R > 0 and A > 0:
                    # 检查A^2/R是否在合理范围
                    ratio = A * A / R
                    if ratio < 30 or ratio > 300:
                        result["errors"].append(
                            f"缓和曲线参数异常: A={A}, R={R}, A²/R={ratio:.1f}"
                        )
    
    # 2. 分析纵曲线
    if vertical_alignment:
        prev_grade = None
        for i, elem in enumerate(vertical_alignment):
            # 检查坡度
            if "grade_out" in elem:
                grade = elem["grade_out"]
                if abs(grade) > 8:  # 超过8%需要检查
                    result["errors"].append(
                        f"纵坡过陡: {elem.get('station', '')} 坡度{grade}%"
                    )
            
            # 检查竖曲线长度
            if "length" in elem and elem["length"]:
                length = elem["length"]
                if length < 50:
                    result["errors"].append(
                        f"竖曲线长度不足: {elem.get('station', '')} 长度{length}m"
                    )
    
    # 3. 分析横断面
    if cross_section:
        width = cross_section.get("width", 0)
        lanes = cross_section.get("lanes", 0)
        
        if width > 50:
            result["errors"].append(f"路面过宽: {width}m")
        
        if lanes > 8:
            result["errors"].append(f"车道数过多: {lanes}")
    
    # 4. 创建设计知识实体
    design_entity = Entity(
        name="道路几何设计",
        description=f"包含{len(horizontal_alignment or [])}个平曲线元素，{len(vertical_alignment or [])}个纵曲线元素",
        entity_type=EntityType.PROJECT,
    )
    crud.create_entity(design_entity)
    result["entities_created"].append(design_entity.to_dict())
    
    return result


def infer_quality_standards_from_design(
    design_data: Dict[str, Any],
    store: KnowledgeGraphStore = None
) -> List[Dict[str, Any]]:
    """从设计数据推断质量标准
    
    Args:
        design_data: 设计数据
        store: 存储实例
        
    Returns:
        质量标准列表
    """
    if store is None:
        store = get_knowledge_store()
    
    crud = KnowledgeGraphCRUD(store)
    quality_standards = []
    
    # 从设计速度推断
    design_speed = design_data.get("design_speed", 80)
    if design_speed >= 100:
        # 高速公路质量标准
        standards = crud.search_entities("高速公路", EntityType.QUALITY_STANDARD)
        quality_standards.extend(standards)
    elif design_speed >= 60:
        # 一级公路质量标准
        standards = crud.search_entities("一级公路", EntityType.QUALITY_STANDARD)
        quality_standards.extend(standards)
    
    # 从路面类型推断
    road_type = design_data.get("road_type", "")
    if "沥青" in road_type:
        standards = crud.search_entities("沥青", EntityType.QUALITY_STANDARD)
        quality_standards.extend(standards)
    
    return quality_standards


# ========== 与 API 层集成 ==========

def register_knowledge_routes(app, store: KnowledgeGraphStore = None):
    """注册知识图谱API路由
    
    Args:
        app: FastAPI应用实例
        store: 存储实例
    """
    try:
        from fastapi import APIRouter, HTTPException, Query
        from typing import Optional
    except ImportError:
        print("Warning: FastAPI not installed, skipping route registration")
        return
    
    router = APIRouter(prefix="/knowledge", tags=["knowledge"])
    
    if store is None:
        store = get_knowledge_store()
    
    crud = KnowledgeGraphCRUD(store)
    
    # ========== 实体API ==========
    
    @router.post("/entities")
    def create_entity(entity: Dict):
        """创建实体"""
        e = Entity.from_dict(entity)
        entity_id = crud.create_entity(e)
        return {"id": entity_id, "status": "created"}
    
    @router.get("/entities/{entity_id}")
    def get_entity(entity_id: str):
        """获取实体"""
        entity = crud.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity.to_dict()
    
    @router.get("/entities")
    def list_entities(
        type: Optional[str] = Query(None, description="实体类型"),
        limit: int = Query(100, le=500)
    ):
        """列出实体"""
        entity_type = EntityType(type) if type else None
        entities = crud.list_entities(entity_type)
        return [e.to_dict() for e in entities[:limit]]
    
    @router.put("/entities/{entity_id}")
    def update_entity(entity_id: str, entity: Dict):
        """更新实体"""
        entity_obj = Entity.from_dict(entity)
        entity_obj.id = entity_id
        success = crud.update_entity(entity_obj)
        return {"status": "updated" if success else "failed"}
    
    @router.delete("/entities/{entity_id}")
    def delete_entity(entity_id: str):
        """删除实体"""
        success = crud.delete_entity(entity_id)
        return {"status": "deleted" if success else "failed"}
    
    @router.get("/entities/search")
    def search_entities(
        q: str = Query(..., description="搜索关键词"),
        type: Optional[str] = Query(None, description="实体类型")
    ):
        """搜索实体"""
        entity_type = EntityType(type) if type else None
        entities = crud.search_entities(q, entity_type)
        return [Entity.from_dict(e).to_dict() for e in entities]
    
    # ========== 关系API ==========
    
    @router.post("/relationships")
    def create_relationship(relationship: Dict):
        """创建关系"""
        from .relationships import Relationship
        rel = Relationship.from_dict(relationship)
        rel_id = crud.create_relationship(rel)
        return {"id": rel_id, "status": "created"}
    
    @router.get("/entities/{entity_id}/relationships")
    def get_relationships(entity_id: str):
        """获取实体的关系"""
        outgoing = crud.get_outgoing_relationships(entity_id)
        incoming = crud.get_incoming_relationships(entity_id)
        return {
            "outgoing": outgoing,
            "incoming": incoming,
        }
    
    @router.get("/entities/{entity_id}/related")
    def get_related_entities(
        entity_id: str,
        type: Optional[str] = Query(None, description="关系类型")
    ):
        """获取关联实体"""
        rel_type = RelationshipType(type) if type else None
        entities = crud.get_related_entities(entity_id, rel_type)
        return [e.to_dict() for e in entities]
    
    # ========== 推理API ==========
    
    @router.post("/reason")
    def reason(context: Dict):
        """推理"""
        from .reasoning import get_reasoning_engine
        engine = get_reasoning_engine(store)
        result = engine.execute(context)
        return result
    
    @router.get("/reason/chain/{entity_id}")
    def get_reasoning_chain(entity_id: str):
        """获取推理链"""
        from .reasoning import get_reasoning_engine
        engine = get_reasoning_engine(store)
        return engine.build_reasoning_chain(entity_id)
    
    @router.post("/reason/question")
    def answer_question(question: Dict):
        """问答"""
        from .reasoning import get_reasoning_engine
        engine = get_reasoning_engine(store)
        result = engine.answer_question(
            question.get("text", ""),
            question.get("context", {})
        )
        return result
    
    # ========== 统计API ==========
    
    @router.get("/statistics")
    def get_statistics():
        """获取统计"""
        return crud.get_statistics()
    
    # 注册路由
    app.include_router(router)
    
    return router


# ========== 便捷函数 ==========

def init_knowledge_from_config(config: Dict, store: KnowledgeGraphStore = None) -> Dict[str, Any]:
    """从配置文件初始化知识图谱
    
    从项目的 config.json 初始化基本知识
    """
    if store is None:
        store = get_knowledge_store()
    
    result = {
        "initialized": True,
        "entities": 0,
        "relationships": 0,
    }
    
    # 解析设计数据
    default_route = config.get("default_route", {})
    
    if default_route:
        # 构建知识
        build_result = build_knowledge_from_geometry(
            horizontal_alignment=default_route.get("horizontal_alignment"),
            vertical_alignment=default_route.get("vertical_alignment"),
            cross_section=default_route.get("cross_section_template"),
            store=store,
        )
        
        result["entities"] = len(build_result.get("entities_created", []))
        result["relationships"] = len(build_result.get("relationships_created", []))
        result["errors"] = build_result.get("errors", [])
    
    return result


def get_knowledge_summary(store: KnowledgeGraphStore = None) -> Dict[str, Any]:
    """获取知识图谱摘要"""
    if store is None:
        store = get_knowledge_store()
    
    stats = store.get_statistics()
    
    return {
        "total_entities": stats["total_entities"],
        "total_relationships": stats["total_relationships"],
        "by_type": stats["entity_stats"],
        "relationship_types": stats["relationship_stats"],
    }
