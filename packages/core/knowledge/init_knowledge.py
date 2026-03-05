"""
NeuralSite Knowledge Graph Initialization
道路工程知识图谱初始化脚本

节点类型:
- Standard(规范): 技术规范、标准
- Process(工艺): 施工工艺
- Material(材料): 建筑材料
- QualityStandard(质量标准): 质量验收标准

关系类型:
- CONSTRAINS: 规范约束工艺/材料
- REQUIRES: 工艺需要材料
- ACHIEVES: 工艺达到质量标准
"""

import logging
from typing import Dict, Any, Optional
from graph_client import KnowledgeGraphClient, init_graph_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KnowledgeGraphInitializer:
    """知识图谱初始化器"""
    
    def __init__(self, client: KnowledgeGraphClient):
        self.client = client
    
    def clear_existing_data(self):
        """清除现有数据"""
        logger.info("Clearing existing knowledge graph data...")
        self.client.delete_all()
        logger.info("Existing data cleared.")
    
    def create_standards(self) -> Dict[str, str]:
        """创建规范节点"""
        logger.info("Creating Standard nodes...")
        
        standards = {
            "JTG_F40_2004": self.client.create_node("Standard", {
                "code": "JTG F40-2004",
                "name": "公路沥青路面施工技术规范",
                "category": "路面工程",
                "issuer": "交通运输部",
                "year": 2004,
                "description": "规定了沥青路面材料的选用、施工工艺、质量控制等要求"
            }),
            
            "JTG_F80_2017": self.client.create_node("Standard", {
                "code": "JTG F80/1-2017",
                "name": "公路工程质量检验评定标准",
                "category": "质量检验",
                "issuer": "交通运输部",
                "year": 2017,
                "description": "规定了公路工程质量检验评定的标准和方法"
            }),
            
            "GB_50092_2019": self.client.create_node("Standard", {
                "code": "GB 50092-2019",
                "name": "沥青路面施工及验收规范",
                "category": "路面工程",
                "issuer": "住房和城乡建设部",
                "year": 2019,
                "description": "沥青路面施工及验收的国家标准"
            })
        }
        
        logger.info(f"Created {len(standards)} Standard nodes")
        return standards
    
    def create_processes(self) -> Dict[str, str]:
        """创建工艺节点"""
        logger.info("Creating Process nodes...")
        
        processes = {
            "paving": self.client.create_node("Process", {
                "code": "P001",
                "name": "沥青混合料摊铺",
                "category": "路面施工",
                "description": "将沥青混合料均匀摊铺在路面基层上的施工工艺",
                "key_parameters": {
                    "temperature": "160-180℃",
                    "speed": "2-4m/min",
                    "thickness": "设计厚度"
                }
            }),
            
            "compaction": self.client.create_node("Process", {
                "code": "P002",
                "name": "沥青混合料压实",
                "category": "路面施工",
                "description": "对摊铺后的沥青混合料进行压实的施工工艺",
                "key_parameters": {
                    "temperature": "120-150℃",
                    "roller_types": ["钢轮压路机", "胶轮压路机"],
                    "passes": "6-10遍"
                }
            }),
            
            "mixing": self.client.create_node("Process", {
                "code": "P003",
                "name": "沥青混合料拌和",
                "category": "材料生产",
                "description": "将沥青和集料加热、拌和形成沥青混合料的生产工艺",
                "key_parameters": {
                    "temperature": "170-185℃",
                    "mixing_time": "30-60秒"
                }
            }),
            
            "transport": self.client.create_node("Process", {
                "code": "P004",
                "name": "沥青混合料运输",
                "category": "物流",
                "description": "将拌和好的沥青混合料运输到施工现场",
                "key_parameters": {
                    "vehicle": "自卸卡车",
                    "cover": "篷布覆盖",
                    "time_limit": "30分钟内"
                }
            })
        }
        
        logger.info(f"Created {len(processes)} Process nodes")
        return processes
    
    def create_materials(self) -> Dict[str, str]:
        """创建材料节点"""
        logger.info("Creating Material nodes...")
        
        materials = {
            "AC_13": self.client.create_node("Material", {
                "code": "AC-13",
                "name": "细粒式沥青混凝土",
                "category": "沥青混合料",
                "description": "最大公称粒径13.2mm的密级配沥青混凝土",
                "properties": {
                    "nominal_size": "13.2mm",
                    "binder": "70号道路石油沥青或SBS改性沥青",
                    "thickness": "30-40mm",
                    "voids": "3-5%"
                }
            }),
            
            "SMA_13": self.client.create_node("Material", {
                "code": "SMA-13",
                "name": "沥青玛蹄脂碎石混合料",
                "category": "沥青混合料",
                "description": "由沥青、纤维稳定剂、矿粉及少量细集料组成的沥青玛蹄脂填充问断级配的碎石骨架",
                "properties": {
                    "nominal_size": "13.2mm",
                    "binder": "SBS改性沥青",
                    "thickness": "30-40mm",
                    "voids": "3-4%",
                    "feature": "高温稳定性好、抗滑耐久"
                }
            }),
            
            "SBS_modifier": self.client.create_node("Material", {
                "code": "SBS",
                "name": "SBS改性剂",
                "category": "改性剂",
                "description": "苯乙烯-丁二烯-苯乙烯热塑性弹性体改性剂",
                "properties": {
                    "type": "线型/星型",
                    "dosage": "3-5%",
                    "function": "提高沥青的高低温性能"
                }
            }),
            
            "aggregate": self.client.create_node("Material", {
                "code": "AGG",
                "name": "粗集料",
                "category": "集料",
                "description": "用于沥青混合料的碎石、砾石等粗颗粒材料",
                "properties": {
                    "size": "4.75mm以上",
                    "requirements": "清洁、干燥、无风化"
                }
            })
        }
        
        logger.info(f"Created {len(materials)} Material nodes")
        return materials
    
    def create_quality_standards(self) -> Dict[str, str]:
        """创建质量标准节点"""
        logger.info("Creating QualityStandard nodes...")
        
        quality_standards = {
            "density": self.client.create_node("QualityStandard", {
                "code": "QS001",
                "name": "压实度",
                "category": "压实质量",
                "description": "沥青路面压实后密度与设计密度的比值",
                "requirements": {
                    "target": "≥96%",
                    "test_method": "钻芯取样、核子密度仪"
                }
            }),
            
            "flatness": self.client.create_node("QualityStandard", {
                "code": "QS002",
                "name": "平整度",
                "category": "路面性能",
                "description": "路面表面的平整程度",
                "requirements": {
                    "IRI": "≤2.0m/km",
                    "max_gap": "3mm/3m"
                }
            }),
            
            "thickness": self.client.create_node("QualityStandard", {
                "code": "QS003",
                "name": "厚度",
                "category": "结构质量",
                "description": "沥青面层的厚度",
                "requirements": {
                    "tolerance": "-5% ~ +10%",
                    "min_value": "设计厚度"
                }
            }),
            
            "temperature": self.client.create_node("QualityStandard", {
                "code": "QS004",
                "name": "施工温度",
                "category": "工艺控制",
                "description": "沥青混合料施工过程中的温度控制",
                "requirements": {
                    "delivery": "≥150℃",
                    "spreading": "≥140℃",
                    "compaction_start": "≥120℃"
                }
            })
        }
        
        logger.info(f"Created {len(quality_standards)} QualityStandard nodes")
        return quality_standards
    
    def create_relationships(self, 
                            standards: Dict[str, str],
                            processes: Dict[str, str],
                            materials: Dict[str, str],
                            quality_standards: Dict[str, str]):
        """创建关系"""
        logger.info("Creating relationships...")
        
        # CONSTRAINS: 规范约束工艺/材料
        # JTG F40-2004 约束 摊铺工艺
        self.client.create_relationship(
            standards["JTG_F40_2004"],
            processes["paving"],
            "CONSTRAINS",
            {"description": "规范要求摊铺温度、速度、厚度控制"}
        )
        
        # JTG F40-2004 约束 压实工艺
        self.client.create_relationship(
            standards["JTG_F40_2004"],
            processes["compaction"],
            "CONSTRAINS",
            {"description": "规范要求压实温度、遍数、方式"}
        )
        
        # JTG F40-2004 约束 AC-13材料
        self.client.create_relationship(
            standards["JTG_F40_2004"],
            materials["AC_13"],
            "CONSTRAINS",
            {"description": "规范规定AC-13的技术要求"}
        )
        
        # JTG F40-2004 约束 SMA-13材料
        self.client.create_relationship(
            standards["JTG_F40_2004"],
            materials["SMA_13"],
            "CONSTRAINS",
            {"description": "规范规定SMA-13的技术要求"}
        )
        
        # GB 50092-2019 约束 压实度质量标准
        self.client.create_relationship(
            standards["GB_50092_2019"],
            quality_standards["density"],
            "CONSTRAINS",
            {"description": "规范规定压实度标准"}
        )
        
        # REQUIRES: 工艺需要材料
        # 摊铺需要 AC-13
        self.client.create_relationship(
            processes["paving"],
            materials["AC_13"],
            "REQUIRES"
        )
        
        # 摊铺需要 SMA-13
        self.client.create_relationship(
            processes["paving"],
            materials["SMA_13"],
            "REQUIRES"
        )
        
        # 压实需要 AC-13
        self.client.create_relationship(
            processes["compaction"],
            materials["AC_13"],
            "REQUIRES"
        )
        
        # 压实需要 SMA-13
        self.client.create_relationship(
            processes["compaction"],
            materials["SMA_13"],
            "REQUIRES"
        )
        
        # 拌和需要 集料
        self.client.create_relationship(
            processes["mixing"],
            materials["aggregate"],
            "REQUIRES"
        )
        
        # SMA-13需要 SBS改性剂
        self.client.create_relationship(
            materials["SMA_13"],
            materials["SBS_modifier"],
            "REQUIRES",
            {"dosage": "3-5%"}
        )
        
        # 运输是摊铺的前提
        self.client.create_relationship(
            processes["transport"],
            processes["paving"],
            "REQUIRES",
            {"description": "运输完成后才能摊铺"}
        )
        
        # ACHIEVES: 工艺达到质量标准
        # 压实达到 压实度
        self.client.create_relationship(
            processes["compaction"],
            quality_standards["density"],
            "ACHIEVES",
            {"target": "≥96%"}
        )
        
        # 压实达到 厚度
        self.client.create_relationship(
            processes["compaction"],
            quality_standards["thickness"],
            "ACHIEVES"
        )
        
        # 摊铺达到 平整度
        self.client.create_relationship(
            processes["paving"],
            quality_standards["flatness"],
            "ACHIEVES",
            {"target": "≤2.0m/km IRI"}
        )
        
        # 压实达到 施工温度
        self.client.create_relationship(
            processes["compaction"],
            quality_standards["temperature"],
            "ACHIEVES",
            {"critical": "温度过低无法压实"}
        )
        
        logger.info("Relationships created successfully")
    
    def initialize(self, clear_existing: bool = True):
        """初始化知识图谱"""
        logger.info("Starting knowledge graph initialization...")
        
        if clear_existing:
            self.clear_existing_data()
        
        # 创建节点
        standards = self.create_standards()
        processes = self.create_processes()
        materials = self.create_materials()
        quality_standards = self.create_quality_standards()
        
        # 创建关系
        self.create_relationships(standards, processes, materials, quality_standards)
        
        # 输出统计信息
        stats = self.client.get_stats()
        logger.info(f"Knowledge graph initialization complete!")
        logger.info(f"Stats: {stats}")
        
        return stats


def main():
    """主函数"""
    # 初始化客户端
    client = init_graph_client(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    if client._driver is None:
        logger.error("Failed to connect to Neo4j. Please ensure Neo4j is running.")
        return
    
    # 初始化知识图谱
    initializer = KnowledgeGraphInitializer(client)
    stats = initializer.initialize(clear_existing=True)
    
    # 打印结果
    print("\n" + "="*60)
    print("知识图谱初始化完成!")
    print("="*60)
    print(f"总节点数: {stats.get('nodes', 0)}")
    print(f"总关系数: {stats.get('relationships', 0)}")
    print("\n各类型节点数量:")
    for label, count in stats.get('by_label', {}).items():
        print(f"  - {label}: {count}")
    print("="*60)
    
    # 关闭连接
    client.close()


if __name__ == "__main__":
    main()
