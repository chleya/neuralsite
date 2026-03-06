# 测试知识图谱模块
import sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\neuralsite\data_driven')

from kg.models import KnowledgeGraph
from kg.engineering import EngineeringKnowledge
from kg.qa import QAEngine

print("=" * 50)
print("测试1: 知识图谱基础功能")
print("=" * 50)

# 创建知识图谱
kg = KnowledgeGraph()

# 添加实体
kg.add_entity("standard", "JTG F80-1-2017", {
    "name": "公路工程质量检验评定标准",
    "category": "质量标准"
})

kg.add_entity("process", "水泥稳定碎石基层施工", {
    "name": "水泥稳定碎石基层施工",
    "steps": ["拌和", "运输", "摊铺", "碾压", "养生"]
})

# 添加关系
kg.add_relation("standard:JTG F80-1-2017", "process:水泥稳定碎石基层施工", "applies_to")

# 查询测试
print("\n查询所有标准:")
results = kg.query(entity_type="standard")
for r in results:
    print(f"  - {r}")

print("\n查询所有工艺:")
results = kg.query(entity_type="process")
for r in results:
    print(f"  - {r['name']}, 步骤: {r['properties'].get('steps')}")

print("\n按名称模糊查询 '水泥':")
results = kg.query(name="水泥")
for r in results:
    print(f"  - {r['name']}")

print("\n" + "=" * 50)
print("测试2: 工程知识库")
print("=" * 50)

ek = EngineeringKnowledge()
print("\n搜索 'JTG':")
results = ek.search("JTG")
for r in results:
    print(f"  - {r['name']}")

print("\n搜索 '水泥':")
results = ek.search("水泥")
for r in results:
    print(f"  - {r['name']}")

print("\n" + "=" * 50)
print("测试3: 问答引擎")
print("=" * 50)

qa = QAEngine(ek)

print("\n问题: 水泥稳定碎石基层的压实度要求是多少?")
answer = qa.answer("水泥稳定碎石基层的压实度要求是多少?")
print(f"答案: {answer['answer']}")
print(f"来源: {answer['source']}")

print("\n问题: 施工单位是谁?")
answer = qa.answer("施工单位是谁?")
print(f"答案: {answer['answer']}")

print("\n" + "=" * 50)
print("所有测试完成!")
print("=" * 50)
