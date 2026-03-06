from kg import KnowledgeGraph

def test_add_entity():
    kg = KnowledgeGraph()
    kg.add_entity("standard", "JTG", {"name": "测试"})
    assert len(kg.entities) > 0
