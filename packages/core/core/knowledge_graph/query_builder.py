# -*- coding: utf-8 -*-
"""
查询构建器

支持:
- 灵活的多条件查询
- 图遍历查询
- 自然语言查询解析
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .entities import Entity, EntityType
from .relationships import RelationshipType
from .storage_sqlite import KnowledgeGraphStore


class QueryType(Enum):
    """查询类型"""
    ENTITY = "entity"           # 实体查询
    RELATIONSHIP = "relationship"  # 关系查询
    PATH = "path"               # 路径查询
    MULTI_HOP = "multi_hop"     # 多跳查询
    FULL_TEXT = "full_text"     # 全文搜索


@dataclass
class QueryCondition:
    """查询条件"""
    field: str                  # 字段名
    operator: str              # 操作符: =, !=, >, <, >=, <=, LIKE, IN
    value: Any                 # 值


@dataclass
class KnowledgeQuery:
    """知识查询"""
    query_type: QueryType = QueryType.ENTITY
    entity_type: EntityType = None
    conditions: List[QueryCondition] = field(default_factory=list)
    relationship_type: RelationshipType = None
    hops: int = 1              # 跳数
    limit: int = 100           # 限制数量
    offset: int = 0            # 偏移量


class QueryBuilder:
    """查询构建器
    
    链式调用构建查询
    """
    
    def __init__(self, store: KnowledgeGraphStore):
        self.store = store
        self.query = KnowledgeQuery()
    
    def select_entity(self, entity_type: EntityType) -> 'QueryBuilder':
        """选择实体类型"""
        self.query.query_type = QueryType.ENTITY
        self.query.entity_type = entity_type
        return self
    
    def where(self, field: str, operator: str, value: Any) -> 'QueryBuilder':
        """添加条件"""
        self.query.conditions.append(
            QueryCondition(field=field, operator=operator, value=value)
        )
        return self
    
    def name_equals(self, name: str) -> 'QueryBuilder':
        """名称等于"""
        return self.where("name", "=", name)
    
    def name_contains(self, keyword: str) -> 'QueryBuilder':
        """名称包含"""
        return self.where("name", "LIKE", f"%{keyword}%")
    
    def description_contains(self, keyword: str) -> 'QueryBuilder':
        """描述包含"""
        return self.where("description", "LIKE", f"%{keyword}%")
    
    def type_equals(self, entity_type: EntityType) -> 'QueryBuilder':
        """类型等于"""
        self.query.entity_type = entity_type
        return self
    
    def related_to(self, entity_id: str, 
                  rel_type: RelationshipType = None) -> 'QueryBuilder':
        """关联查询"""
        self.query.query_type = QueryType.RELATIONSHIP
        self.query.relationship_type = rel_type
        self.query.conditions.append(
            QueryCondition(field="source_id", operator="=", value=entity_id)
        )
        return self
    
    def hop(self, hops: int) -> 'QueryBuilder':
        """设置跳数"""
        self.query.query_type = QueryType.MULTI_HOP
        self.query.hops = hops
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """限制数量"""
        self.query.limit = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """设置偏移"""
        self.query.offset = offset
        return self
    
    def execute(self) -> List[Dict[str, Any]]:
        """执行查询"""
        if self.query.query_type == QueryType.ENTITY:
            return self._execute_entity_query()
        elif self.query.query_type == QueryType.RELATIONSHIP:
            return self._execute_relationship_query()
        elif self.query.query_type == QueryType.MULTI_HOP:
            return self._execute_multi_hop_query()
        elif self.query.query_type == QueryType.FULL_TEXT:
            return self._execute_full_text_query()
        
        return []
    
    def _execute_entity_query(self) -> List[Dict[str, Any]]:
        """执行实体查询"""
        # 构建SQL
        sql = "SELECT * FROM entities WHERE 1=1"
        params = []
        
        if self.query.entity_type:
            sql += " AND entity_type = ?"
            params.append(self.query.entity_type.value)
        
        for cond in self.query.conditions:
            if cond.operator == "=":
                sql += f" AND {cond.field} = ?"
            elif cond.operator == "!=":
                sql += f" AND {cond.field} != ?"
            elif cond.operator == "LIKE":
                sql += f" AND {cond.field} LIKE ?"
                params.append(cond.value)
            elif cond.operator == ">":
                sql += f" AND {cond.field} > ?"
            elif cond.operator == "<":
                sql += f" AND {cond.field} < ?"
            elif cond.operator == ">=":
                sql += f" AND {cond.field} >= ?"
            elif cond.operator == "<=":
                sql += f" AND {cond.field} <= ?"
            else:
                continue
            
            if cond.operator != "LIKE":
                params.append(cond.value)
        
        sql += f" LIMIT {self.query.limit} OFFSET {self.query.offset}"
        
        return self.store.execute_custom_query(sql, tuple(params))
    
    def _execute_relationship_query(self) -> List[Dict[str, Any]]:
        """执行关系查询"""
        sql = "SELECT * FROM relationships WHERE 1=1"
        params = []
        
        for cond in self.query.conditions:
            sql += f" AND {cond.field} = ?"
            params.append(cond.value)
        
        if self.query.relationship_type:
            sql += " AND relationship_type = ?"
            params.append(self.query.relationship_type.value)
        
        sql += f" LIMIT {self.query.limit}"
        
        return self.store.execute_custom_query(sql, tuple(params))
    
    def _execute_multi_hop_query(self) -> List[Dict[str, Any]]:
        """执行多跳查询"""
        if not self.query.conditions:
            return []
        
        # 获取起始实体
        start_id = None
        for cond in self.query.conditions:
            if cond.field == "source_id":
                start_id = cond.value
                break
        
        if not start_id:
            return []
        
        # 构建hops列表
        rel_types = []
        if self.query.relationship_type:
            rel_types = [self.query.relationship_type] * self.query.hops
        else:
            rel_types = [RelationshipType.LINKED_TO] * self.query.hops
        
        return self.store.multi_hop_query(start_id, rel_types, self.query.limit)
    
    def _execute_full_text_query(self) -> List[Dict[str, Any]]:
        """执行全文搜索"""
        keyword = ""
        for cond in self.query.conditions:
            if cond.field in ("name", "description"):
                keyword = cond.value.replace("%", "")
        
        if not keyword:
            return []
        
        return self.store.search_entities(keyword, self.query.entity_type)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """获取第一条"""
        results = self.limit(1).execute()
        return results[0] if results else None
    
    def count(self) -> int:
        """计数"""
        sql = "SELECT COUNT(*) as cnt FROM entities WHERE 1=1"
        params = []
        
        if self.query.entity_type:
            sql += " AND entity_type = ?"
            params.append(self.query.entity_type.value)
        
        for cond in self.query.conditions:
            if cond.operator == "LIKE":
                sql += f" AND {cond.field} LIKE ?"
            else:
                sql += f" AND {cond.field} = ?"
            params.append(cond.value)
        
        result = self.store.execute_custom_query(sql, tuple(params))
        return result[0]["cnt"] if result else 0


class KnowledgeQueryEngine:
    """知识查询引擎
    
    高级查询接口
    """
    
    def __init__(self, store: KnowledgeGraphStore):
        self.store = store
    
    def builder(self) -> QueryBuilder:
        """创建查询构建器"""
        return QueryBuilder(self.store)
    
    def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找"""
        return self.store.get_entity(entity_id)
    
    def find_by_name(self, name: str, 
                    entity_type: EntityType = None) -> Optional[Dict[str, Any]]:
        """根据名称查找"""
        type_str = entity_type.value if entity_type else None
        return self.store.get_entity_by_name(name, type_str)
    
    def find_all(self, entity_type: EntityType = None,
                limit: int = 100) -> List[Dict[str, Any]]:
        """查找所有"""
        if entity_type:
            return self.store.get_entities_by_type(entity_type)
        
        return self.store.execute_custom_query(
            f"SELECT * FROM entities LIMIT {limit}"
        )
    
    def find_related(self, entity_id: str, 
                   rel_type: RelationshipType = None) -> List[Dict[str, Any]]:
        """查找关联实体"""
        return self.store.get_related_entities(entity_id, rel_type)
    
    def find_path(self, source_id: str, target_id: str) -> List[List[str]]:
        """查找路径"""
        return self.store.find_path(source_id, target_id, max_hops=3)
    
    def search(self, keyword: str, 
              entity_type: EntityType = None) -> List[Dict[str, Any]]:
        """搜索"""
        return self.store.search_entities(keyword, entity_type)
    
    def multi_hop(self, start_id: str, 
                 hops: List[RelationshipType]) -> List[Dict[str, Any]]:
        """多跳查询"""
        return self.store.multi_hop_query(start_id, hops)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return self.store.get_statistics()


# 便捷函数
def create_query_builder(store: KnowledgeGraphStore) -> QueryBuilder:
    """创建查询构建器"""
    return QueryBuilder(store)


def search_knowledge(keyword: str, 
                    entity_type: EntityType = None,
                    store: KnowledgeGraphStore = None) -> List[Dict[str, Any]]:
    """便捷搜索函数"""
    if store is None:
        from .storage_sqlite import get_knowledge_store
        store = get_knowledge_store()
    
    return store.search_entities(keyword, entity_type)
