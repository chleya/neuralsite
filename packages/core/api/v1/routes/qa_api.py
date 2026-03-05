# -*- coding: utf-8 -*-
"""
NeuralSite 知识问答 API

功能:
1. POST /api/v1/qa/query - 知识问答（结合Neo4j知识图谱+规则匹配）
2. POST /api/v1/qa/drawing-query - 图纸语义查询

Neo4j: bolt://localhost:7687
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import re
import sys

sys.path.insert(0, '.')

from core.engine import NeuralSiteEngine
from storage.graph_db import get_graph_db, GraphDatabase
from core.knowledge_graph.reasoning import ReasoningEngine
from core.knowledge_graph.schema import search_entities
from api.dependencies import get_engine, get_graph_database, get_feature_flags
from core.config.feature_flags import FeatureFlags

router = APIRouter(prefix="/api/v1/qa", tags=["知识问答"])


# ========== 请求/响应模型 ==========

class QAQueryRequest(BaseModel):
    """知识问答请求"""
    question: str = Field(..., description="问题文本")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    use_knowledge_graph: bool = Field(True, description="是否使用知识图谱")
    use_rules: bool = Field(True, description="是否使用规则匹配")


class DrawingQueryRequest(BaseModel):
    """图纸语义查询请求"""
    query: str = Field(..., description="查询文本，如：'帮我找K0+500附近的挡土墙图纸'")
    drawing_type: Optional[str] = Field(None, description="图纸类型过滤")
    chainage_range: Optional[Dict[str, float]] = Field(None, description="桩号范围 {start, end}")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量")


class QAQueryResponse(BaseModel):
    """知识问答响应"""
    question: str
    answer: str
    confidence: float = 1.0
    sources: List[str] = []
    entities: List[Dict[str, Any]] = []
    reasoning: Optional[Dict[str, Any]] = None


class DrawingQueryResponse(BaseModel):
    """图纸查询响应"""
    query: str
    total: int
    drawings: List[Dict[str, Any]]
    suggestions: List[str] = []


# ========== 施工问题规则库 ==========

class ConstructionRuleEngine:
    """施工问题规则引擎"""
    
    def __init__(self):
        self.reasoning_engine = ReasoningEngine()
        self._init_construction_rules()
    
    def _init_construction_rules(self):
        """初始化施工问题规则"""
        # 规则1: 纵坡超限检查
        self.reasoning_engine.add_rule(
            type="if_then",
            condition=lambda ctx: ctx.get("check_type") == "grade_limit",
            conclusion=self._check_grade_limit
        )
        
        # 规则2: 弯沉值检查
        self.reasoning_engine.add_rule(
            type="if_then", 
            condition=lambda ctx: ctx.get("check_type") == "deflection",
            conclusion=self._check_deflection
        )
        
        # 规则3: 压实度检查
        self.reasoning_engine.add_rule(
            type="if_then",
            condition=lambda ctx: ctx.get("check_type") == "compaction",
            conclusion=self._check_compaction
        )
        
        # 规则4: 施工工艺顺序
        self.reasoning_engine.add_rule(
            type="if_then",
            condition=lambda ctx: ctx.get("check_type") == "process_sequence",
            conclusion=self._check_process_sequence
        )
    
    def _check_grade_limit(self, ctx: Dict) -> Dict:
        """检查纵坡是否超限"""
        grade = ctx.get("grade", 0)
        design_speed = ctx.get("design_speed", 80)
        
        # 根据设计速度确定最大纵坡
        max_grades = {
            20: 8, 30: 7, 40: 6, 60: 5, 80: 4, 100: 3, 120: 3
        }
        max_grade = max_grades.get(design_speed, 4)
        
        is_valid = abs(grade) <= max_grade
        return {
            "result": "通过" if is_valid else "超限",
            "actual_grade": grade,
            "max_allowed": max_grade,
            "design_speed": design_speed,
            "message": f"纵坡{grade}%符合规范" if is_valid else f"纵坡{grade}%超过最大限值{max_grade}%"
        }
    
    def _check_deflection(self, ctx: Dict) -> Dict:
        """检查弯沉值"""
        deflection = ctx.get("deflection", 0)
        layer_type = ctx.get("layer_type", "基层")
        
        # 弯沉值标准
        standards = {
            "面层": 20, "基层": 30, "底基层": 40, "路基": 100
        }
        max_deflection = standards.get(layer_type, 30)
        
        is_valid = deflection <= max_deflection
        return {
            "result": "通过" if is_valid else "不合格",
            "actual": deflection,
            "max_allowed": max_deflection,
            "layer": layer_type,
            "message": f"弯沉值{deflection}(0.01mm)符合要求" if is_valid else f"弯沉值{deflection}(0.01mm)超过标准{max_deflection}(0.01mm)"
        }
    
    def _check_compaction(self, ctx: Dict) -> Dict:
        """检查压实度"""
        compaction = ctx.get("compaction", 0)
        layer_type = ctx.get("layer_type", "路基")
        
        # 压实度标准(%)
        standards = {
            "路基": 93, "底基层": 96, "基层": 98, "面层": 98
        }
        min_compaction = standards.get(layer_type, 93)
        
        is_valid = compaction >= min_compaction
        return {
            "result": "合格" if is_valid else "不合格",
            "actual": compaction,
            "min_required": min_compaction,
            "layer": layer_type,
            "message": f"压实度{compaction}%符合要求" if is_valid else f"压实度{compaction}%低于标准{min_compaction}%"
        }
    
    def _check_process_sequence(self, ctx: Dict) -> Dict:
        """检查施工工艺顺序"""
        process = ctx.get("process", "")
        
        # 标准施工顺序
        standard_sequence = [
            "路基清理", "路基填筑", "路基压实", "底基层施工",
            "基层施工", "面层施工", "排水工程", "防护工程"
        ]
        
        if process in standard_sequence:
            idx = standard_sequence.index(process)
            return {
                "result": "正常",
                "process": process,
                "sequence": idx + 1,
                "total": len(standard_sequence),
                "message": f"{process}是第{idx+1}道工序"
            }
        
        return {
            "result": "未知",
            "process": process,
            "message": f"未找到工艺'{process}'的标准顺序"
        }
    
    def answer_construction_question(self, question: str) -> Dict[str, Any]:
        """回答施工相关问题"""
        question_lower = question.lower()
        
        # 检查纵坡问题
        if "纵坡" in question or "坡度" in question:
            grade_match = re.search(r'(\d+\.?\d*)%', question)
            if grade_match:
                grade = float(grade_match.group(1))
                ctx = {"check_type": "grade_limit", "grade": grade}
                return self._check_grade_limit(ctx)
        
        # 检查弯沉值问题
        if "弯沉" in question:
            deflection_match = re.search(r'(\d+\.?\d*)', question)
            if deflection_match:
                deflection = float(deflection_match.group(1))
                layer = "基层"
                if "面层" in question:
                    layer = "面层"
                elif "底基层" in question:
                    layer = "底基层"
                elif "路基" in question:
                    layer = "路基"
                ctx = {"check_type": "deflection", "deflection": deflection, "layer_type": layer}
                return self._check_deflection(ctx)
        
        # 检查压实度问题
        if "压实度" in question:
            compaction_match = re.search(r'(\d+\.?\d*)%', question)
            if compaction_match:
                compaction = float(compaction_match.group(1))
                layer = "路基"
                if "面层" in question:
                    layer = "面层"
                elif "基层" in question:
                    layer = "基层"
                ctx = {"check_type": "compaction", "compaction": compaction, "layer_type": layer}
                return self._check_compaction(ctx)
        
        # 检查施工工艺问题
        if "工序" in question or "施工顺序" in question or "工艺" in question:
            # 尝试提取工艺名称
            for process in ["路基清理", "路基填筑", "路基压实", "底基层", "基层", "面层", "排水", "防护"]:
                if process in question:
                    ctx = {"check_type": "process_sequence", "process": process}
                    return self._check_process_sequence(ctx)
        
        return None


# 全局规则引擎
_rule_engine = None


def get_rule_engine() -> ConstructionRuleEngine:
    """获取规则引擎实例"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = ConstructionRuleEngine()
    return _rule_engine


# ========== 知识图谱查询辅助函数 ==========

def query_from_kg(chainage: str) -> Optional[Dict]:
    """从知识图谱查询坐标信息"""
    db = get_graph_db()
    
    query = """
    MATCH (f:Feature {chainage: $chainage})-[:LOCATED_AT]->(c:Coordinate)
    RETURN c.x AS x, c.y AS y, c.z AS z, c.chainage AS chainage
    """
    
    results = db.execute_query(query, {"chainage": chainage})
    return results[0] if results else None


def query_drawings_from_kg(drawing_type: str = None, chainage: str = None) -> List[Dict]:
    """从知识图谱查询图纸"""
    db = get_graph_db()
    
    if chainage:
        query = """
        MATCH (d:Drawing)-[:HAS_FEATURE]->(f:Feature {chainage: $chainage})
        RETURN d.id AS id, d.name AS name, d.type AS type, f.chainage AS chainage
        LIMIT 20
        """
        results = db.execute_query(query, {"chainage": chainage})
    elif drawing_type:
        query = """
        MATCH (d:Drawing {type: $type})
        RETURN d.id AS id, d.name AS name, d.type AS type
        LIMIT 20
        """
        results = db.execute_query(query, {"type": drawing_type})
    else:
        query = """
        MATCH (d:Drawing)
        RETURN d.id AS id, d.name AS name, d.type AS type
        LIMIT 20
        """
        results = db.execute_query(query, {})
    
    return results


def query_kg_entities(keyword: str, entity_type: str = None) -> List[Dict]:
    """查询知识图谱实体"""
    return search_entities(keyword, entity_type, limit=10)


# ========== API 端点 ==========

@router.post(
    "/query",
    response_model=QAQueryResponse,
    summary="知识问答",
    description="结合Neo4j知识图谱和规则匹配回答施工问题"
)
async def qa_query(
    request: QAQueryRequest,
    engine: NeuralSiteEngine = Depends(get_engine),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> QAQueryResponse:
    """
    知识问答接口
    
    支持的问题类型：
    - 桩号相关："K0+500的标高/坐标/纵坡"
    - 施工检查："纵坡5%是否超限"、"弯沉值30是否合格"、"压实度95%是否达标"
    - 施工工艺："基层施工的下一道工序是什么"
    - 知识图谱查询："查找K1+000附近的桥梁"
    """
    
    if not feature_flags.is_enabled("enable_qa_system"):
        raise HTTPException(status_code=403, detail="QA system is disabled")
    
    question = request.question
    answer = ""
    confidence = 0.5
    sources = []
    entities = []
    reasoning_result = None
    
    # 1. 首先尝试施工规则匹配
    if request.use_rules:
        rule_engine = get_rule_engine()
        rule_result = rule_engine.answer_construction_question(question)
        if rule_result:
            answer = rule_result.get("message", "")
            confidence = 0.9
            sources.append("rule_engine")
            reasoning_result = {"rule_type": "construction_check", "result": rule_result}
    
    # 2. 如果规则未匹配，尝试桩号查询
    if not answer:
        chainage_match = re.search(r'K(\d+)\+(\d{3})', question)
        
        if chainage_match:
            chainage = f"K{chainage_match.group(1)}+{chainage_match.group(2)}"
            station = int(chainage_match.group(1)) * 1000 + int(chainage_match.group(2))
            
            entities.append({
                "type": "chainage",
                "value": chainage,
                "station_m": station
            })
            
            # 根据问题关键词确定查询类型
            if any(k in question for k in ["标高", "高程", "z"]):
                # 优先从知识图谱查询
                if request.use_knowledge_graph:
                    kg_result = query_from_kg(chainage)
                    if kg_result:
                        answer = f"{chainage}的设计高程是{kg_result['z']:.3f}m（来自知识图谱）"
                        sources.append("knowledge_graph")
                    else:
                        coord = engine.get_coordinate(station)
                        answer = f"{chainage}的设计高程是{coord.z:.3f}m"
                        sources.append("engine")
                else:
                    coord = engine.get_coordinate(station)
                    answer = f"{chainage}的设计高程是{coord.z:.3f}m"
                    sources.append("engine")
                confidence = 0.95
                
            elif any(k in question for k in ["坐标", "x", "y"]):
                if request.use_knowledge_graph:
                    kg_result = query_from_kg(chainage)
                    if kg_result:
                        answer = f"{chainage}的坐标为 X={kg_result['x']:.3f}, Y={kg_result['y']:.3f}, Z={kg_result['z']:.3f}（来自知识图谱）"
                        sources.append("knowledge_graph")
                    else:
                        coord = engine.get_coordinate(station)
                        answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}"
                        sources.append("engine")
                else:
                    coord = engine.get_coordinate(station)
                    answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}"
                    sources.append("engine")
                confidence = 0.95
                
            elif any(k in question for k in ["纵坡", "坡度", "grade"]):
                coord1 = engine.get_coordinate(max(0, station - 100))
                coord2 = engine.get_coordinate(station + 100)
                grade = (coord2.z - coord1.z) / 200 * 100
                answer = f"{chainage}附近的纵坡为 {grade:.2f}%"
                confidence = 0.85
                sources.append("engine")
                
            elif any(k in question for k in ["横断", "断面", "cross"]):
                cs = engine.calculate_cross_section(station)
                answer = f"{chainage}的横断面：中心点({cs['center'][0]:.2f}, {cs['center'][1]:.2f}, {cs['center'][2]:.2f})，宽度{cs['width']:.2f}m"
                confidence = 0.9
                sources.append("engine")
                
            else:
                # 默认返回坐标
                coord = engine.get_coordinate(station)
                answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}，方位角{coord.azimuth:.1f}°"
                confidence = 0.8
                sources.append("engine")
    
    # 3. 如果仍未匹配，尝试知识图谱实体搜索
    if not answer and request.use_knowledge_graph:
        # 提取关键词进行搜索
        keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', question)
        for kw in keywords:
            if len(kw) >= 2:
                kg_entities = query_kg_entities(kw)
                if kg_entities:
                    entities.extend(kg_entities[:3])
                    answer = f"找到相关实体：{', '.join([e.get('name', e.get('id', '')) for e in kg_entities[:3]])}"
                    confidence = 0.6
                    sources.append("knowledge_graph")
                    break
    
    # 4. 默认回答
    if not answer:
        answer = "抱歉，我无法理解您的问题。请尝试询问：\n- K0+500的标高/坐标\n- 纵坡5%是否超限\n- 压实度95%是否达标\n- 帮我找K1+000的桥梁图纸"
        confidence = 0.2
    
    return QAQueryResponse(
        question=question,
        answer=answer,
        confidence=confidence,
        sources=sources,
        entities=entities,
        reasoning=reasoning_result
    )


@router.post(
    "/drawing-query",
    response_model=DrawingQueryResponse,
    summary="图纸语义查询",
    description="根据语义查询相关的图纸信息"
)
async def drawing_semantic_query(
    request: DrawingQueryRequest,
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> DrawingQueryResponse:
    """
    图纸语义查询接口
    
    示例查询：
    - "帮我找K0+500附近的挡土墙图纸"
    - "查找所有桥梁图纸"
    - "K1+000到K2+000范围的排水图纸"
    """
    
    if not feature_flags.is_enabled("enable_qa_system"):
        raise HTTPException(status_code=403, detail="QA system is disabled")
    
    query = request.query
    drawings = []
    suggestions = []
    total = 0
    
    # 解析桩号
    chainage_match = re.search(r'K(\d+)\+(\d{3})', query)
    chainage = None
    if chainage_match:
        chainage = f"K{chainage_match.group(1)}+{chainage_match.group(2)}"
    
    # 解析桩号范围
    range_match = re.findall(r'K(\d+)\+(\d{3})', query)
    chainage_range = None
    if len(range_match) >= 2:
        start = int(range_match[0][0]) * 1000 + int(range_match[0][1])
        end = int(range_match[1][0]) * 1000 + int(range_match[1][1])
        chainage_range = {"start": start, "end": end}
    
    # 解析图纸类型
    drawing_type = request.drawing_type
    type_keywords = {
        "挡土墙": "挡土墙", "挡墙": "挡土墙",
        "桥梁": "桥梁", "桥": "桥梁",
        "涵洞": "涵洞",
        "排水": "排水", "雨水": "排水",
        "路面": "路面",
        "纵断面": "纵断面", "横断": "横断面",
        "平面": "平面"
    }
    
    if not drawing_type:
        for kw, dt in type_keywords.items():
            if kw in query:
                drawing_type = dt
                break
    
    # 从知识图谱查询图纸
    if chainage:
        kg_results = query_drawings_from_kg(drawing_type, chainage)
        drawings = kg_results
        total = len(drawings)
    elif drawing_type:
        kg_results = query_drawings_from_kg(drawing_type, None)
        drawings = kg_results
        total = len(drawings)
    else:
        # 通用搜索
        keywords = [k for k in type_keywords.keys() if k in query]
        if keywords:
            drawing_type = type_keywords[keywords[0]]
            kg_results = query_drawings_from_kg(drawing_type, None)
            drawings = kg_results
            total = len(drawings)
    
    # 如果没有从KG查到，返回模拟数据
    if total == 0:
        # 生成建议
        suggestions = [
            "请检查Neo4j知识图谱是否已启动",
            "可以尝试指定更具体的桩号或图纸类型",
            "例如：'K0+500的挡土墙图纸' 或 '查找桥梁图纸'"
        ]
        
        # 返回模拟数据提示
        drawings = [{
            "id": "demo_drawing_001",
            "name": f"{chainage or '全局'}{drawing_type or '综合'}图纸",
            "type": drawing_type or "综合",
            "chainage": chainage,
            "note": "这是演示数据，请确保Neo4j已启动并导入数据"
        }]
        total = 1
    
    return DrawingQueryResponse(
        query=query,
        total=total,
        drawings=drawings,
        suggestions=suggestions
    )


# ========== 注册路由 ==========

def register_routes(app):
    """注册路由到FastAPI应用"""
    app.include_router(router)
