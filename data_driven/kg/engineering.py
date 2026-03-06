from kg.models import KnowledgeGraph


class EngineeringKnowledge:
    """工程知识库"""
    
    def __init__(self):
        self.kg = KnowledgeGraph()
        self._init_standards()
        self._init_processes()
    
    def _init_standards(self):
        """初始化规范"""
        # 添加公路工程相关标准
        self.kg.add_entity("standard", "JTG F80-1-2017", {
            "name": "公路工程质量检验评定标准",
            "category": "质量标准"
        })
    
    def _init_processes(self):
        """初始化工艺"""
        # 添加施工工艺
        self.kg.add_entity("process", "水泥稳定碎石基层施工", {
            "steps": ["拌和", "运输", "摊铺", "碾压", "养生"]
        })
    
    def search(self, query: str) -> list:
        """搜索知识"""
        return self.kg.query(name=query)
