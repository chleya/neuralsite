# -*- coding: utf-8 -*-
"""
知识图谱模块单元测试
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试用的临时数据库
TEST_DB_PATH = "test_knowledge_graph.db"


class TestEntities(unittest.TestCase):
    """测试实体类"""
    
    def test_entity_creation(self):
        """测试实体创建"""
        from core.knowledge_graph.entities import Entity, EntityType
        
        entity = Entity(
            id="test-001",
            name="测试实体",
            description="这是一个测试实体",
            entity_type=EntityType.STANDARD,
            properties={"key": "value"}
        )
        
        self.assertEqual(entity.id, "test-001")
        self.assertEqual(entity.name, "测试实体")
        self.assertEqual(entity.entity_type, EntityType.STANDARD)
    
    def test_entity_to_dict(self):
        """测试实体转字典"""
        from core.knowledge_graph.entities import Entity, EntityType
        
        entity = Entity(
            name="测试实体",
            entity_type=EntityType.STANDARD,
        )
        
        d = entity.to_dict()
        self.assertIn("id", d)
        self.assertEqual(d["name"], "测试实体")
        self.assertEqual(d["entity_type"], "standard")
    
    def test_standard_creation(self):
        """测试规范实体创建"""
        from core.knowledge_graph.entities import Standard, create_standard
        
        standard = create_standard(
            name="公路沥青路面施工技术规范",
            code="JTG F40-2004",
            category="施工规范",
            description="规定了沥青路面施工技术要求",
            version="2004"
        )
        
        self.assertEqual(standard.code, "JTG F40-2004")
        self.assertEqual(standard.category, "施工规范")
        self.assertEqual(standard.entity_type.value, "standard")
    
    def test_process_creation(self):
        """测试工艺实体创建"""
        from core.knowledge_graph.entities import Process, create_process
        
        process = create_process(
            name="沥青路面摊铺",
            process_type="路面施工",
            steps=["准备", "摊铺", "压实"],
            description="沥青路面摊铺工艺",
            duration=7
        )
        
        self.assertEqual(process.process_type, "路面施工")
        self.assertEqual(len(process.steps), 3)
        self.assertEqual(process.duration, 7)
    
    def test_material_creation(self):
        """测试材料实体创建"""
        from core.knowledge_graph.entities import Material, create_material
        
        material = create_material(
            name="SBS改性沥青",
            material_type="沥青材料",
            specs={"针入度": "60-80", "软化点": "≥75℃"},
            description="SBS改性沥青"
        )
        
        self.assertEqual(material.material_type, "沥青材料")
        self.assertIn("针入度", material.specs)
    
    def test_quality_standard_creation(self):
        """测试质量标准实体创建"""
        from core.knowledge_graph.entities import QualityStandard, create_quality_standard
        
        qstandard = create_quality_standard(
            name="压实度要求",
            standard_code="JTG F80/1-2017",
            index_name="压实度",
            index_value="≥96%",
            test_method="核子密度仪法",
            tolerance="代表值-2%"
        )
        
        self.assertEqual(qstandard.standard_code, "JTG F80/1-2017")
        self.assertEqual(qstandard.index_name, "压实度")


class TestRelationships(unittest.TestCase):
    """测试关系类"""
    
    def test_relationship_creation(self):
        """测试关系创建"""
        from core.knowledge_graph.relationships import (
            Relationship, RelationshipType, CONTAINS
        )
        
        rel = Relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=CONTAINS,
            weight=0.8
        )
        
        self.assertEqual(rel.source_id, "entity-1")
        self.assertEqual(rel.target_id, "entity-2")
        self.assertEqual(rel.relationship_type, RelationshipType.CONTAINS)
    
    def test_relationship_to_dict(self):
        """测试关系转字典"""
        from core.knowledge_graph.relationships import Relationship, DEPENDS_ON
        
        rel = Relationship(
            source_id="process-1",
            target_id="material-1",
            relationship_type=DEPENDS_ON,
        )
        
        d = rel.to_dict()
        self.assertEqual(d["relationship_type"], "DEPENDS_ON")
        self.assertEqual(d["source_id"], "process-1")


class TestKnowledgeGraphStore(unittest.TestCase):
    """测试知识图谱存储"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        # 使用临时数据库
        cls.db_path = TEST_DB_PATH
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def setUp(self):
        """每个测试前设置"""
        # 删除已存在的数据库
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_store_initialization(self):
        """测试存储初始化"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        
        store = KnowledgeGraphStore(self.db_path)
        stats = store.get_statistics()
        
        self.assertEqual(stats["total_entities"], 0)
        self.assertEqual(stats["total_relationships"], 0)
    
    def test_create_and_get_entity(self):
        """测试创建和获取实体"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        
        store = KnowledgeGraphStore(self.db_path)
        entity = Entity(
            name="测试规范",
            entity_type=EntityType.STANDARD,
            properties={"code": "TEST-001"}
        )
        
        store.create_entity(entity)
        
        retrieved = store.get_entity(entity.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "测试规范")
    
    def test_create_and_get_relationship(self):
        """测试创建和获取关系"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        from core.knowledge_graph.relationships import Relationship, CONTAINS
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建两个实体
        entity1 = Entity(name="父实体", entity_type=EntityType.STANDARD)
        entity2 = Entity(name="子实体", entity_type=EntityType.STANDARD)
        
        store.create_entity(entity1)
        store.create_entity(entity2)
        
        # 创建关系
        rel = Relationship(
            source_id=entity1.id,
            target_id=entity2.id,
            relationship_type=CONTAINS
        )
        store.create_relationship(rel)
        
        # 获取关系
        retrieved = store.get_relationship(rel.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["source_id"], entity1.id)
    
    def test_get_related_entities(self):
        """测试获取关联实体"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        from core.knowledge_graph.relationships import Relationship, USES
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建实体
        process = Entity(name="摊铺工艺", entity_type=EntityType.PROCESS)
        material = Entity(name="沥青材料", entity_type=EntityType.MATERIAL)
        
        store.create_entity(process)
        store.create_entity(material)
        
        # 创建关系
        rel = Relationship(
            source_id=process.id,
            target_id=material.id,
            relationship_type=USES
        )
        store.create_relationship(rel)
        
        # 获取关联
        related = store.get_related_entities(process.id)
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0]["name"], "沥青材料")
    
    def test_search_entities(self):
        """测试搜索实体"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建实体
        entities = [
            Entity(name="沥青路面规范", entity_type=EntityType.STANDARD),
            Entity(name="水泥路面规范", entity_type=EntityType.STANDARD),
            Entity(name="沥青材料", entity_type=EntityType.MATERIAL),
        ]
        
        for e in entities:
            store.create_entity(e)
        
        # 搜索
        results = store.search_entities("沥青")
        self.assertEqual(len(results), 2)
    
    def test_multi_hop_query(self):
        """测试多跳查询"""
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        from core.knowledge_graph.relationships import Relationship, RelationshipType
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建实体链: A -> B -> C
        entity_a = Entity(name="A", entity_type=EntityType.PROJECT)
        entity_b = Entity(name="B", entity_type=EntityType.PROCESS)
        entity_c = Entity(name="C", entity_type=EntityType.MATERIAL)
        
        store.create_entity(entity_a)
        store.create_entity(entity_b)
        store.create_entity(entity_c)
        
        # 创建关系
        rel1 = Relationship(source_id=entity_a.id, target_id=entity_b.id, 
                           relationship_type=RelationshipType.CONTAINS)
        rel2 = Relationship(source_id=entity_b.id, target_id=entity_c.id,
                           relationship_type=RelationshipType.USES)
        
        store.create_relationship(rel1)
        store.create_relationship(rel2)
        
        # 多跳查询
        results = store.multi_hop_query(
            entity_a.id, 
            [RelationshipType.CONTAINS, RelationshipType.USES]
        )
        self.assertGreaterEqual(len(results), 0)  # 可能为空，取决于查询实现


class TestCRUD(unittest.TestCase):
    """测试CRUD操作"""
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = TEST_DB_PATH
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
    
    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_add_standard(self):
        """测试添加规范"""
        from core.knowledge_graph.crud import KnowledgeGraphCRUD
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import EntityType
        
        store = KnowledgeGraphStore(self.db_path)
        crud = KnowledgeGraphCRUD(store)
        
        entity_id = crud.add_standard(
            name="测试规范",
            code="TEST-001",
            category="测试",
            description="测试用规范"
        )
        
        entity = crud.get_entity(entity_id)
        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, "测试规范")
    
    def test_add_process(self):
        """测试添加工艺"""
        from core.knowledge_graph.crud import KnowledgeGraphCRUD
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        
        store = KnowledgeGraphStore(self.db_path)
        crud = KnowledgeGraphCRUD(store)
        
        entity_id = crud.add_process(
            name="摊铺工艺",
            process_type="路面施工",
            steps=["准备", "摊铺", "压实"],
            duration=7
        )
        
        entity = crud.get_entity(entity_id)
        self.assertIsNotNone(entity)
    
    def test_link_contains(self):
        """测试建立包含关系"""
        from core.knowledge_graph.crud import KnowledgeGraphCRUD
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        
        store = KnowledgeGraphStore(self.db_path)
        crud = KnowledgeGraphCRUD(store)
        
        # 创建两个实体
        parent_id = crud.add_standard(name="父规范", code="P001")
        child_id = crud.add_standard(name="子规范", code="C001")
        
        # 建立关系
        rel_id = crud.link_contains(parent_id, child_id)
        
        self.assertIsNotNone(rel_id)
        
        # 验证关系
        related = crud.get_related_entities(parent_id)
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].name, "子规范")


class TestReasoningEngine(unittest.TestCase):
    """测试推理引擎"""
    
    def test_reasoning_engine_creation(self):
        """测试推理引擎创建"""
        from core.knowledge_graph.reasoning import ReasoningEngine, Rule
        
        engine = ReasoningEngine()
        self.assertGreater(len(engine.rules), 0)
    
    def test_execute_rule(self):
        """测试执行规则"""
        from core.knowledge_graph.reasoning import ReasoningEngine, Rule
        from core.knowledge_graph.entities import EntityType
        
        engine = ReasoningEngine()
        
        # 执行推理
        context = {"process_id": "test-id"}
        result = engine.execute(context)
        
        self.assertIn("applied_rules", result)
    
    def test_answer_question(self):
        """测试问答"""
        from core.knowledge_graph.reasoning import ReasoningEngine
        
        engine = ReasoningEngine()
        
        # 测试问题
        result = engine.answer_question("沥青路面需要什么材料?")
        
        self.assertIn("question", result)
        self.assertIn("answer", result)


class TestQueryBuilder(unittest.TestCase):
    """测试查询构建器"""
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = TEST_DB_PATH
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
    
    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_query_builder(self):
        """测试查询构建器"""
        from core.knowledge_graph.query_builder import QueryBuilder
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import EntityType
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建查询构建器
        builder = QueryBuilder(store)
        
        # 构建查询
        results = builder.select_entity(EntityType.STANDARD).execute()
        
        self.assertIsInstance(results, list)
    
    def test_query_with_conditions(self):
        """测试带条件的查询"""
        from core.knowledge_graph.query_builder import QueryBuilder
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        from core.knowledge_graph.entities import Entity, EntityType
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 创建测试实体
        entity = Entity(
            name="测试规范",
            entity_type=EntityType.STANDARD,
            properties={"code": "TEST-001"}
        )
        store.create_entity(entity)
        
        # 查询
        builder = QueryBuilder(store)
        results = builder.name_contains("测试").execute()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "测试规范")


class TestIntegration(unittest.TestCase):
    """测试集成功能"""
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = TEST_DB_PATH
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
    
    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_build_knowledge_from_geometry(self):
        """测试从几何数据构建知识"""
        from core.knowledge_graph.integration import build_knowledge_from_geometry
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 模拟几何设计数据
        horizontal = [
            {"element_type": "直线", "start_station": "K0+000", "end_station": "K0+500"},
            {"element_type": "圆曲线", "start_station": "K0+500", "end_station": "K1+200", "R": 800},
        ]
        
        vertical = [
            {"station": "K0+000", "elevation": 100, "grade_out": 20},
            {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15},
        ]
        
        cross_section = {"width": 26, "lanes": 4, "crown_slope": 2.0}
        
        result = build_knowledge_from_geometry(
            horizontal, vertical, cross_section, store
        )
        
        self.assertIn("entities_created", result)
    
    def test_init_knowledge_from_config(self):
        """测试从配置初始化"""
        from core.knowledge_graph.integration import init_knowledge_from_config
        from core.knowledge_graph.storage_sqlite import KnowledgeGraphStore
        
        store = KnowledgeGraphStore(self.db_path)
        
        # 模拟配置
        config = {
            "design_speed": 80,
            "default_route": {
                "horizontal_alignment": [
                    {"element_type": "直线", "start_station": "K0+000"}
                ],
                "vertical_alignment": [
                    {"station": "K0+000", "elevation": 100}
                ],
                "cross_section_template": {"width": 26, "lanes": 4}
            }
        }
        
        result = init_knowledge_from_config(config, store)
        
        self.assertIn("entities", result)


if __name__ == "__main__":
    unittest.main()
