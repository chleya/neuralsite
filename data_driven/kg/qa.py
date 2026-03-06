from kg.engineering import EngineeringKnowledge


class QAEngine:
    """问答引擎"""
    
    def __init__(self, knowledge: EngineeringKnowledge):
        self.knowledge = knowledge
    
    def answer(self, question: str) -> dict:
        """回答问题"""
        # 1. 解析问题
        # 2. 搜索知识图谱
        # 3. 生成答案
        
        if "压实度" in question:
            return {
                "answer": "水泥稳定碎石基层压实度要求≥98%",
                "source": "JTG F80-1-2017"
            }
        
        return {"answer": "未找到相关信息"}
