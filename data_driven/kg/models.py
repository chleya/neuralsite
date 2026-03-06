class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self.entities = {}  # 实体
        self.relations = []  # 关系
    
    def add_entity(self, entity_type: str, name: str, properties: dict):
        """添加实体"""
        entity_id = f"{entity_type}:{name}"
        self.entities[entity_id] = {
            "type": entity_type,
            "name": name,
            "properties": properties
        }
    
    def add_relation(self, from_id: str, to_id: str, relation_type: str):
        """添加关系"""
        self.relations.append({
            "from": from_id,
            "to": to_id,
            "type": relation_type
        })
    
    def query(self, entity_type: str = None, name: str = None) -> list:
        """查询实体"""
        results = []
        for e in self.entities.values():
            if entity_type and e["type"] != entity_type:
                continue
            if name and name not in e["name"]:
                continue
            results.append(e)
        return results
