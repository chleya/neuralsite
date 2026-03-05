# -*- coding: utf-8 -*-
"""
简单推理引擎

支持:
1. 规则推理：根据条件推导结论
2. 查询优化：支持多跳查询
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import re

from .entities import Entity, EntityType
from .relationships import RelationshipType
from .storage_sqlite import KnowledgeGraphStore


class RuleType(Enum):
    """规则类型"""
    IF_THEN = "if_then"           # 如果...则...
    DEDUCTION = "deduction"       # 演绎推理
    INDUCTION = "induction"       # 归纳推理


@dataclass
class Rule:
    """推理规则
    
    属性:
        id: 规则ID
        name: 规则名称
        description: 规则描述
        condition: 条件函数
        conclusion: 结论函数
        priority: 优先级（越高越先执行）
    """
    id: str
    name: str
    description: str
    condition: Callable[[Dict], bool]
    conclusion: Callable[[Dict], Dict]
    priority: int = 0


class ReasoningEngine:
    """推理引擎
    
    支持:
    - 规则推理
    - 多跳查询
    - 路径查找
    """
    
    def __init__(self, store: KnowledgeGraphStore = None):
        """初始化推理引擎"""
        self.store = store
        self.rules: List[Rule] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        
        # 规则1: 检查工艺是否具备施工条件
        rule1 = Rule(
            id="rule_001",
            name="检查工艺施工条件",
            description="检查工艺是否具备完整的前置工艺",
            condition=lambda ctx: "process_id" in ctx,
            conclusion=lambda ctx: self._check_prerequisites(ctx),
            priority=10
        )
        self.add_rule(rule1)
        
        # 规则2: 检查材料依赖
        rule2 = Rule(
            id="rule_002",
            name="检查材料完整性",
            description="检查工艺是否具备所需材料",
            condition=lambda ctx: "process_id" in ctx,
            conclusion=lambda ctx: self._check_materials(ctx),
            priority=5
        )
        self.add_rule(rule2)
        
        # 规则3: 推导质量标准
        rule3 = Rule(
            id="rule_003",
            name="推导质量标准",
            description="根据规范推导相关质量标准",
            condition=lambda ctx: "standard_id" in ctx,
            conclusion=lambda ctx: self._derive_quality_standards(ctx),
            priority=8
        )
        self.add_rule(rule3)
    
    def add_rule(self, rule: Rule):
        """添加规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_id: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行推理
        
        Args:
            context: 推理上下文，包含输入条件
            
        Returns:
            推理结果
        """
        results = {
            "input": context,
            "conclusions": [],
            "applied_rules": [],
            "paths": [],
        }
        
        # 遍历规则
        for rule in self.rules:
            if rule.condition(context):
                results["applied_rules"].append(rule.name)
                conclusion = rule.conclusion(context)
                if conclusion:
                    results["conclusions"].append(conclusion)
        
        return results
    
    def execute_chain(self, context: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """链式推理
        
        Args:
            context: 初始上下文
            max_depth: 最大推理深度
            
        Returns:
            推理结果
        """
        current_context = context.copy()
        all_results = []
        
        for depth in range(max_depth):
            result = self.execute(current_context)
            if not result["conclusions"]:
                break
            
            all_results.extend(result["conclusions"])
            
            # 将结论添加到上下文中
            for conc in result["conclusions"]:
                current_context.update(conc)
        
        return {
            "input": context,
            "results": all_results,
            "depth": depth + 1,
        }
    
    # ========== 规则实现 ==========
    
    def _check_prerequisites(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """检查前置工艺"""
        process_id = ctx.get("process_id")
        if not process_id or not self.store:
            return {}
        
        # 查找前置关系
        prereqs = self.store.get_related_entities(
            process_id, RelationshipType.REQUIRES
        )
        
        if prereqs:
            return {
                "has_prerequisites": True,
                "prerequisites": [p["name"] for p in prereqs],
                "prerequisite_ids": [p["id"] for p in prereqs],
            }
        
        return {"has_prerequisites": False}
    
    def _check_materials(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """检查材料依赖"""
        process_id = ctx.get("process_id")
        if not process_id or not self.store:
            return {}
        
        # 查找使用关系
        materials = self.store.get_related_entities(
            process_id, RelationshipType.USES
        ) + self.store.get_related_entities(
            process_id, RelationshipType.DEPENDS_ON
        )
        
        if materials:
            return {
                "has_materials": True,
                "materials": [m["name"] for m in materials],
                "material_ids": [m["id"] for m in materials],
            }
        
        return {"has_materials": False}
    
    def _derive_quality_standards(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """推导质量标准"""
        standard_id = ctx.get("standard_id")
        if not standard_id or not self.store:
            return {}
        
        # 查找包含的质量标准
        qstandards = self.store.get_related_entities(
            standard_id, RelationshipType.CONTAINS
        )
        
        if qstandards:
            return {
                "has_quality_standards": True,
                "quality_standards": [
                    {
                        "name": q["name"],
                        "index": q.get("properties", {}).get("index_name", ""),
                        "value": q.get("properties", {}).get("index_value", ""),
                    }
                    for q in qstandards
                ],
            }
        
        return {"has_quality_standards": False}
    
    # ========== 多跳查询 ==========
    
    def multi_hop_query(self, start_id: str, 
                        hops: List[RelationshipType]) -> List[Dict[str, Any]]:
        """多跳查询
        
        Args:
            start_id: 起始实体ID
            hops: 关系类型序列
            
        Returns:
            查询结果
        """
        if not self.store:
            return []
        
        return self.store.multi_hop_query(start_id, hops)
    
    def find_influence_path(self, source_id: str, target_id: str) -> List[List[str]]:
        """查找影响路径
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            
        Returns:
            路径列表
        """
        if not self.store:
            return []
        
        return self.store.find_path(source_id, target_id, max_hops=3)
    
    # ========== 推理链构建 ==========
    
    def build_reasoning_chain(self, entity_id: str) -> Dict[str, Any]:
        """构建推理链
        
        从实体出发，递归查找所有关联实体
        
        Args:
            entity_id: 起始实体ID
            
        Returns:
            推理链数据
        """
        if not self.store:
            return {}
        
        chain = {
            "root": entity_id,
            "entities": [],
            "relationships": [],
        }
        
        visited = {entity_id}
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= 3:  # 最大深度
                continue
            
            # 获取出边
            outgoing = self.store.get_outgoing_relationships(current_id)
            
            for rel in outgoing:
                chain["relationships"].append({
                    "source": rel["source_id"],
                    "target": rel["target_id"],
                    "type": rel["relationship_type"],
                })
                
                target_id = rel["target_id"]
                if target_id not in visited:
                    visited.add(target_id)
                    
                    # 获取目标实体
                    target_entity = self.store.get_entity(target_id)
                    if target_entity:
                        chain["entities"].append(target_entity)
                    
                    queue.append((target_id, depth + 1))
        
        return chain
    
    # ========== 智能问答支持 ==========
    
    def answer_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """智能问答
        
        根据问题内容自动选择推理策略
        
        Args:
            question: 问题文本
            context: 额外上下文
            
        Returns:
            答案
        """
        question = question.lower()
        result = {
            "question": question,
            "answer": "",
            "confidence": 0.0,
            "sources": [],
        }
        
        if not context:
            context = {}
        
        # 模式匹配
        if "工艺" in question or "施工" in question:
            if "材料" in question:
                # 工艺需要什么材料
                result["answer"] = "需要查询工艺的材料依赖关系"
                result["sources"] = ["材料数据库"]
                result["confidence"] = 0.8
                
            elif "规范" in question or "标准" in question:
                # 工艺引用什么规范
                result["answer"] = "需要查询工艺引用的规范"
                result["sources"] = ["规范数据库"]
                result["confidence"] = 0.8
                
        elif "材料" in question:
            if "规范" in question:
                # 材料相关规范
                result["answer"] = "需要查询材料的规范要求"
                result["sources"] = ["规范数据库"]
                result["confidence"] = 0.7
                
        elif "质量" in question or "标准" in question:
            result["answer"] = "需要查询质量标准"
            result["sources"] = ["质量标准数据库"]
            result["confidence"] = 0.9
        
        return result


# 全局实例
_reasoning_engine = None


def get_reasoning_engine(store: KnowledgeGraphStore = None) -> ReasoningEngine:
    """获取推理引擎实例"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine(store)
    return _reasoning_engine
