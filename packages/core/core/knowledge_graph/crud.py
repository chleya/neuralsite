# -*- coding: utf-8 -*-
"""
知识图谱CRUD接口
"""

from typing import Dict, List, Any, Optional
import uuid

from .entities import (
    Entity, EntityType, 
    Standard, Process, Material, QualityStandard,
    create_standard, create_process, create_material, create_quality_standard
)
from .relationships import (
    Relationship, RelationshipType,
    create_contains_relation, create_depends_on_relation, 
    create_applies_to_relation, create_requires_relation,
    create_uses_relation, create_references_relation
)
from .storage_sqlite import KnowledgeGraphStore, get_knowledge_store


class KnowledgeGraphCRUD:
    """知识图谱CRUD操作类"""
    
    def __init__(self, store: KnowledgeGraphStore = None):
        """初始化
        
        Args:
            store: 存储实例，如果为None则获取全局实例
        """
        self.store = store or get_knowledge_store()
    
    # ========== 实体CRUD ==========
    
    def create_entity(self, entity: Entity) -> str:
        """创建实体
        
        Args:
            entity: 实体对象
            
        Returns:
            实体ID
        """
        self.store.create_entity(entity)
        return entity.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        data = self.store.get_entity(entity_id)
        if data:
            return self._row_to_entity(data)
        return None
    
    def get_entity_by_name(self, name: str, entity_type: EntityType = None) -> Optional[Entity]:
        """根据名称获取实体"""
        type_str = entity_type.value if entity_type else None
        data = self.store.get_entity_by_name(name, type_str)
        if data:
            return self._row_to_entity(data)
        return None
    
    def list_entities(self, entity_type: EntityType = None) -> List[Entity]:
        """列出实体"""
        if entity_type:
            rows = self.store.get_entities_by_type(entity_type)
        else:
            # 获取所有实体
            rows = self.store.execute_custom_query("SELECT * FROM entities")
        
        return [self._row_to_entity(row) for row in rows]
    
    def update_entity(self, entity: Entity) -> bool:
        """更新实体"""
        return self.store.update_entity(entity)
    
    def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        return self.store.delete_entity(entity_id)
    
    def search_entities(self, keyword: str, entity_type: EntityType = None) -> List[Entity]:
        """搜索实体"""
        rows = self.store.search_entities(keyword, entity_type)
        return [self._row_to_entity(row) for row in rows]
    
    # ========== 关系CRUD ==========
    
    def create_relationship(self, relationship: Relationship) -> str:
        """创建关系"""
        self.store.create_relationship(relationship)
        return relationship.id
    
    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """获取关系"""
        data = self.store.get_relationship(relationship_id)
        if data:
            return Relationship.from_dict(data)
        return None
    
    def get_outgoing_relationships(self, entity_id: str) -> List[Relationship]:
        """获取实体的出边"""
        rows = self.store.get_outgoing_relationships(entity_id)
        return [Relationship.from_dict(row) for row in rows]
    
    def get_incoming_relationships(self, entity_id: str) -> List[Relationship]:
        """获取实体的入边"""
        rows = self.store.get_incoming_relationships(entity_id)
        return [Relationship.from_dict(row) for row in rows]
    
    def get_related_entities(self, entity_id: str, 
                           relationship_type: RelationshipType = None) -> List[Entity]:
        """获取关联实体"""
        rows = self.store.get_related_entities(entity_id, relationship_type)
        result = []
        for row in rows:
            entity = self._row_to_entity(row)
            # 添加关系信息到属性
            if "relationship_type" in row:
                entity.properties["_relationship_type"] = row["relationship_type"]
            if "weight" in row:
                entity.properties["_weight"] = row["weight"]
            result.append(entity)
        return result
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """删除关系"""
        return self.store.delete_relationship(relationship_id)
    
    # ========== 便捷方法 ==========
    
    def add_standard(self, name: str, code: str, category: str = "",
                    description: str = "", version: str = "1.0") -> str:
        """添加规范"""
        standard = create_standard(name, code, category, description, version)
        return self.create_entity(standard)
    
    def add_process(self, name: str, process_type: str, steps: List[str] = None,
                  description: str = "", duration: float = 0) -> str:
        """添加工艺"""
        process = create_process(name, process_type, steps, description, duration)
        return self.create_entity(process)
    
    def add_material(self, name: str, material_type: str, 
                    specs: Dict[str, Any] = None, description: str = "") -> str:
        """添加材料"""
        material = create_material(name, material_type, specs, description)
        return self.create_entity(material)
    
    def add_quality_standard(self, name: str, standard_code: str, 
                           index_name: str, index_value: Any,
                           test_method: str = "", tolerance: str = "") -> str:
        """添加质量标准"""
        qstandard = create_quality_standard(
            name, standard_code, index_name, index_value, test_method, tolerance
        )
        return self.create_entity(qstandard)
    
    def link_contains(self, parent_id: str, child_id: str, weight: float = 1.0) -> str:
        """建立包含关系"""
        rel = create_contains_relation(parent_id, child_id, weight)
        return self.create_relationship(rel)
    
    def link_depends_on(self, process_id: str, material_id: str, 
                      weight: float = 1.0) -> str:
        """建立依赖关系"""
        rel = create_depends_on_relation(process_id, material_id, weight)
        return self.create_relationship(rel)
    
    def link_applies_to(self, standard_id: str, road_type: str,
                       weight: float = 1.0) -> str:
        """建立适用于关系"""
        rel = create_applies_to_relation(standard_id, road_type, weight)
        return self.create_relationship(rel)
    
    def link_requires(self, process_id: str, prerequisite_id: str,
                     weight: float = 1.0) -> str:
        """建立前置关系"""
        rel = create_requires_relation(process_id, prerequisite_id, weight)
        return self.create_relationship(rel)
    
    def link_uses(self, process_id: str, material_id: str,
                 weight: float = 1.0) -> str:
        """建立使用关系"""
        rel = create_uses_relation(process_id, material_id, weight)
        return self.create_relationship(rel)
    
    def link_references(self, entity_id: str, standard_id: str,
                       weight: float = 1.0) -> str:
        """建立引用关系"""
        rel = create_references_relation(entity_id, standard_id, weight)
        return self.create_relationship(rel)
    
    # ========== 查询方法 ==========
    
    def find_process_materials(self, process_id: str) -> List[Entity]:
        """查找工艺使用的材料"""
        return self.get_related_entities(process_id, RelationshipType.USES)
    
    def find_process_standards(self, process_id: str) -> List[Entity]:
        """查找工艺引用的规范"""
        return self.get_related_entities(process_id, RelationshipType.REFERENCES)
    
    def find_prerequisites(self, process_id: str) -> List[Entity]:
        """查找工艺的前置工艺"""
        return self.get_related_entities(process_id, RelationshipType.REQUIRES)
    
    def find_quality_standards(self, standard_id: str) -> List[Entity]:
        """查找规范包含的质量标准"""
        return self.get_related_entities(standard_id, RelationshipType.CONTAINS)
    
    def find_applicable_standards(self, road_type: str) -> List[Entity]:
        """查找适用于某道路类型的规范"""
        return self.get_related_entities(road_type, RelationshipType.APPLIES_TO)
    
    # ========== 统计 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.store.get_statistics()
    
    # ========== 辅助方法 ==========
    
    def _row_to_entity(self, row: Dict[str, Any]) -> Entity:
        """将数据库行转换为实体"""
        import json
        
        # 解析properties
        props = row.get("properties", "{}")
        if isinstance(props, str):
            props = json.loads(props)
        
        # 重新构建完整数据
        data = {
            "id": row.get("id"),
            "name": row.get("name"),
            "description": row.get("description"),
            "entity_type": row.get("entity_type"),
            "properties": props,
        }
        
        return Entity.from_dict(data)
    
    def _row_to_relationship(self, row: Dict[str, Any]) -> Relationship:
        """将数据库行转换为关系"""
        return Relationship.from_dict(row)


# 全局CRUD实例
_crud = None


def get_knowledge_crud(store: KnowledgeGraphStore = None) -> KnowledgeGraphCRUD:
    """获取CRUD实例"""
    global _crud
    if _crud is None:
        _crud = KnowledgeGraphCRUD(store)
    return _crud
