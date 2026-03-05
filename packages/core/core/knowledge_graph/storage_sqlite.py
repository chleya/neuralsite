# -*- coding: utf-8 -*-
"""
知识图谱SQLite存储层

使用SQLite存储图数据，支持:
- 实体存储
- 关系存储
- 图查询（通过SQL）
"""

import os
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import json

from .entities import Entity, EntityType
from .relationships import Relationship, RelationshipType


class KnowledgeGraphStore:
    """知识图谱SQLite存储"""
    
    def __init__(self, db_path: str = "knowledge_graph.db"):
        """初始化存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def _cursor(self):
        """获取cursor的上下文管理器"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self._cursor() as cursor:
            # 实体表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    entity_type TEXT NOT NULL,
                    properties TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # 关系表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    properties TEXT,
                    weight REAL DEFAULT 1.0,
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relationship_type)")
    
    # ========== 实体操作 ==========
    
    def create_entity(self, entity: Entity) -> bool:
        """创建实体"""
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT INTO entities (id, name, description, entity_type, properties, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.name,
                entity.description,
                entity.entity_type.value,
                json.dumps(entity.properties, ensure_ascii=False),
                entity.created_at.isoformat() if entity.created_at else None,
                entity.updated_at.isoformat() if entity.updated_at else None,
            ))
            return True
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取实体"""
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_entity_by_name(self, name: str, entity_type: str = None) -> Optional[Dict[str, Any]]:
        """根据名称获取实体"""
        with self._cursor() as cursor:
            if entity_type:
                cursor.execute(
                    "SELECT * FROM entities WHERE name = ? AND entity_type = ?", 
                    (name, entity_type)
                )
            else:
                cursor.execute("SELECT * FROM entities WHERE name = ?", (name,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Dict[str, Any]]:
        """根据类型获取实体列表"""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM entities WHERE entity_type = ?", 
                (entity_type.value,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_entity(self, entity: Entity) -> bool:
        """更新实体"""
        from datetime import datetime
        entity.updated_at = datetime.now()
        
        with self._cursor() as cursor:
            cursor.execute("""
                UPDATE entities 
                SET name = ?, description = ?, entity_type = ?, properties = ?, updated_at = ?
                WHERE id = ?
            """, (
                entity.name,
                entity.description,
                entity.entity_type.value,
                json.dumps(entity.properties, ensure_ascii=False),
                entity.updated_at.isoformat(),
                entity.id,
            ))
            return cursor.rowcount > 0
    
    def delete_entity(self, entity_id: str) -> bool:
        """删除实体（同时删除相关关系）"""
        with self._cursor() as cursor:
            # 先删除相关关系
            cursor.execute(
                "DELETE FROM relationships WHERE source_id = ? OR target_id = ?",
                (entity_id, entity_id)
            )
            # 再删除实体
            cursor.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
            return cursor.rowcount > 0
    
    def search_entities(self, keyword: str, entity_type: EntityType = None) -> List[Dict[str, Any]]:
        """搜索实体"""
        with self._cursor() as cursor:
            if entity_type:
                cursor.execute("""
                    SELECT * FROM entities 
                    WHERE (name LIKE ? OR description LIKE ?) AND entity_type = ?
                """, (f"%{keyword}%", f"%{keyword}%", entity_type.value))
            else:
                cursor.execute("""
                    SELECT * FROM entities 
                    WHERE name LIKE ? OR description LIKE ?
                """, (f"%{keyword}%", f"%{keyword}%"))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 关系操作 ==========
    
    def create_relationship(self, relationship: Relationship) -> bool:
        """创建关系"""
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT INTO relationships (id, source_id, target_id, relationship_type, properties, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                relationship.id,
                relationship.source_id,
                relationship.target_id,
                relationship.relationship_type.value,
                json.dumps(relationship.properties, ensure_ascii=False),
                relationship.weight,
            ))
            return True
    
    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """获取关系"""
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM relationships WHERE id = ?", (relationship_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_outgoing_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """获取实体的所有出边"""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM relationships WHERE source_id = ?", 
                (entity_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_incoming_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """获取实体的所有入边"""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM relationships WHERE target_id = ?", 
                (entity_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_related_entities(self, entity_id: str, 
                            relationship_type: RelationshipType = None) -> List[Dict[str, Any]]:
        """获取关联实体"""
        with self._cursor() as cursor:
            if relationship_type:
                cursor.execute("""
                    SELECT e.*, r.relationship_type, r.weight
                    FROM relationships r
                    JOIN entities e ON e.id = r.target_id
                    WHERE r.source_id = ? AND r.relationship_type = ?
                """, (entity_id, relationship_type.value))
            else:
                cursor.execute("""
                    SELECT e.*, r.relationship_type, r.weight
                    FROM relationships r
                    JOIN entities e ON e.id = r.target_id
                    WHERE r.source_id = ?
                """, (entity_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """删除关系"""
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM relationships WHERE id = ?", (relationship_id,))
            return cursor.rowcount > 0
    
    # ========== 图查询 ==========
    
    def execute_custom_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """执行自定义SQL查询"""
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    
    def multi_hop_query(self, start_entity_id: str, 
                       hops: List[RelationshipType],
                       limit: int = 100) -> List[Dict[str, Any]]:
        """多跳查询
        
        Args:
            start_entity_id: 起始实体ID
            hops: 跳数列表，每一 hop 的关系类型
            limit: 结果限制
        
        Returns:
            查询结果列表，每项包含路径信息
        """
        results = []
        
        with self._cursor() as cursor:
            # 构建递归查询
            if len(hops) == 1:
                cursor.execute("""
                    SELECT e.*, r.relationship_type as rel_type, 1 as hop
                    FROM relationships r
                    JOIN entities e ON e.id = r.target_id
                    WHERE r.source_id = ? AND r.relationship_type = ?
                    LIMIT ?
                """, (start_entity_id, hops[0].value, limit))
                results = [dict(row) for row in cursor.fetchall()]
            
            elif len(hops) == 2:
                cursor.execute("""
                    SELECT e2.*, e1.name as intermediate_name, 
                           r1.relationship_type as rel_type_1,
                           r2.relationship_type as rel_type_2,
                           2 as hop
                    FROM relationships r1
                    JOIN entities e1 ON e1.id = r1.target_id
                    JOIN relationships r2 ON r2.source_id = e1.id
                    JOIN entities e2 ON e2.id = r2.target_id
                    WHERE r1.source_id = ? 
                      AND r1.relationship_type = ?
                      AND r2.relationship_type = ?
                    LIMIT ?
                """, (start_entity_id, hops[0].value, hops[1].value, limit))
                results = [dict(row) for row in cursor.fetchall()]
            
            else:
                # 简化的多跳：只查第一跳
                return self.multi_hop_query(start_entity_id, hops[:1], limit)
        
        return results
    
    def find_path(self, start_entity_id: str, end_entity_id: str, 
                 max_hops: int = 3) -> List[List[str]]:
        """查找两点之间的路径
        
        Returns:
            路径列表，每条路径是实体ID列表
        """
        paths = []
        
        if max_hops < 1:
            return paths
        
        # BFS
        visited = {start_entity_id}
        queue = [(start_entity_id, [start_entity_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end_entity_id:
                paths.append(path)
                continue
            
            if len(path) >= max_hops:
                continue
            
            # 查找直接关联
            with self._cursor() as cursor:
                cursor.execute("""
                    SELECT target_id FROM relationships 
                    WHERE source_id = ?
                """, (current,))
                
                for row in cursor.fetchall():
                    next_id = row["target_id"]
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))
        
        return paths
    
    # ========== 统计 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._cursor() as cursor:
            # 实体统计
            cursor.execute("SELECT entity_type, COUNT(*) as count FROM entities GROUP BY entity_type")
            entity_stats = {row["entity_type"]: row["count"] for row in cursor.fetchall()}
            
            # 关系统计
            cursor.execute("SELECT relationship_type, COUNT(*) as count FROM relationships GROUP BY relationship_type")
            rel_stats = {row["relationship_type"]: row["count"] for row in cursor.fetchall()}
            
            # 总数
            cursor.execute("SELECT COUNT(*) as total FROM entities")
            total_entities = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM relationships")
            total_relationships = cursor.fetchone()["total"]
            
            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "entity_stats": entity_stats,
                "relationship_stats": rel_stats,
            }
    
    def close(self):
        """关闭连接（实际上不需要，连接在context中自动关闭）"""
        pass


# 全局实例
_store = None


def get_knowledge_store(db_path: str = "knowledge_graph.db") -> KnowledgeGraphStore:
    """获取知识图谱存储实例"""
    global _store
    if _store is None:
        _store = KnowledgeGraphStore(db_path)
    return _store


def init_knowledge_graph(db_path: str = "knowledge_graph.db") -> KnowledgeGraphStore:
    """初始化知识图谱"""
    store = KnowledgeGraphStore(db_path)
    
    # 导入并添加初始数据
    from .entities import create_standard, create_process, create_material, create_quality_standard
    from .relationships import create_contains_relation, create_depends_on_relation, create_references_relation
    
    # 检查是否已有数据
    stats = store.get_statistics()
    if stats["total_entities"] > 0:
        return store
    
    # 添加示例数据
    # 1. 创建规范
    standard = create_standard(
        name="公路沥青路面施工技术规范",
        code="JTG F40-2004",
        category="施工规范",
        description="规定了公路沥青路面施工的技术要求",
        version="2004"
    )
    store.create_entity(standard)
    
    standard2 = create_standard(
        name="公路工程质量检验评定标准",
        code="JTG F80/1-2017",
        category="质量标准",
        description="规定了公路工程质量检验评定的标准",
        version="2017"
    )
    store.create_entity(standard2)
    
    # 2. 创建工艺
    process = create_process(
        name="沥青路面摊铺",
        process_type="路面施工",
        steps=[
            "施工准备",
            "基层检查",
            "沥青混合料运输",
            "摊铺",
            "压实",
            "接缝处理"
        ],
        description="沥青路面摊铺施工工艺",
        duration=7
    )
    store.create_entity(process)
    
    process2 = create_process(
        name="基层施工",
        process_type="基层施工",
        steps=[
            "材料准备",
            "拌和",
            "运输",
            "摊铺",
            "压实",
            "养护"
        ],
        description="水泥稳定碎石基层施工",
        duration=14
    )
    store.create_entity(process2)
    
    # 3. 创建材料
    material = create_material(
        name="SBS改性沥青",
        material_type="沥青材料",
        specs={
            "针入度": "60-80 0.1mm",
            "软化点": "≥75 ℃",
            "延度": "≥30 cm"
        },
        description="SBS改性沥青，用于高等级公路"
    )
    store.create_entity(material)
    
    material2 = create_material(
        name="AC-16沥青混合料",
        material_type="混合料",
        specs={
            "最大粒径": "16mm",
            "油石比": "4.5-5.5%",
            "空隙率": "3-5%"
        },
        description="AC-16中粒式沥青混凝土"
    )
    store.create_entity(material2)
    
    # 4. 创建质量标准
    qstandard = create_quality_standard(
        name="压实度要求",
        standard_code="JTG F80/1-2017",
        index_name="压实度",
        index_value="≥96%",
        test_method="核子密度仪法",
        tolerance="代表值-2%，极值-4%"
    )
    store.create_entity(qstandard)
    
    # 5. 创建关系
    # 规范包含质量标准
    store.create_relationship(create_contains_relation(standard2.id, qstandard.id))
    # 工艺依赖材料
    store.create_relationship(create_depends_on_relation(process.id, material.id))
    store.create_relationship(create_depends_on_relation(process.id, material2.id))
    # 工艺引用规范
    store.create_relationship(create_references_relation(process.id, standard.id))
    
    print(f"知识图谱初始化完成: {store.get_statistics()}")
    return store
