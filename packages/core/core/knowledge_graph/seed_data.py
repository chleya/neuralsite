# -*- coding: utf-8 -*-
"""
道路工程领域知识图谱初始数据填充脚本

包含:
1. 规范数据 - JTG D20-2017, JTG F40-2004, 公路工程质量检验评定标准
2. 施工工艺 - 水泥稳定碎石基层、沥青路面面层、混凝土桥面铺装
3. 材料规格 - 道路石油沥青、水泥、集料
4. 质量标准 - 压实度、平整度、厚度允许偏差
"""

# 判断是否作为主模块运行
if __name__ == "__main__":
    # 作为主模块运行时
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from knowledge_graph.entities import (
        Entity, EntityType,
        Standard, Process, Material, QualityStandard,
        create_standard, create_process, create_material, create_quality_standard
    )
    from knowledge_graph.relationships import (
        Relationship, RelationshipType,
        CONTAINS, DEPENDS_ON, APPLIES_TO, REQUIRES, USES, REFERENCES,
        create_relationship, create_contains_relation, create_depends_on_relation,
        create_applies_to_relation, create_requires_relation, create_uses_relation,
        create_references_relation
    )
    from knowledge_graph.storage_sqlite import KnowledgeGraphStore
else:
    # 作为包导入时
    from .entities import (
        Entity, EntityType,
        Standard, Process, Material, QualityStandard,
        create_standard, create_process, create_material, create_quality_standard
    )
    from .relationships import (
        Relationship, RelationshipType,
        CONTAINS, DEPENDS_ON, APPLIES_TO, REQUIRES, USES, REFERENCES,
        create_relationship, create_contains_relation, create_depends_on_relation,
        create_applies_to_relation, create_requires_relation, create_uses_relation,
        create_references_relation
    )
    from .storage_sqlite import KnowledgeGraphStore

from typing import Dict, List, Any, Tuple
import json


class RoadEngineeringSeedData:
    """道路工程领域知识数据填充器"""
    
    def __init__(self, store: KnowledgeGraphStore):
        self.store = store
        self.entity_ids: Dict[str, str] = {}  # 名称到ID的映射
    
    def seed_all(self) -> Dict[str, int]:
        """填充所有知识数据
        
        Returns:
            统计信息
        """
        # 1. 创建规范数据
        self._create_standards()
        
        # 2. 创建材料规格
        self._create_materials()
        
        # 3. 创建施工工艺
        self._create_processes()
        
        # 4. 创建质量标准
        self._create_quality_standards()
        
        # 5. 创建关系
        self._create_relationships()
        
        stats = self.store.get_statistics()
        return {
            "entities": stats["total_entities"],
            "relationships": stats["total_relationships"]
        }
    
    def _create_standards(self):
        """创建规范数据"""
        standards = [
            # 设计规范
            Standard(
                name="公路路线设计规范",
                code="JTG D20-2017",
                category="设计规范",
                version="2017",
                description="规定了公路路线设计的技术要求，包括平面、纵断面、横断面设计等",
                scope="适用于新建和改扩建各级公路"
            ),
            # 施工规范
            Standard(
                name="公路沥青路面施工技术规范",
                code="JTG F40-2004",
                category="施工规范",
                version="2004",
                description="规定了公路沥青路面施工的技术要求、施工工艺和质量标准",
                scope="适用于各等级公路沥青路面施工"
            ),
            Standard(
                name="公路水泥混凝土路面施工技术规范",
                code="JTG F30-2003",
                category="施工规范",
                version="2003",
                description="规定了公路水泥混凝土路面施工的技术要求",
                scope="适用于各等级公路水泥混凝土路面施工"
            ),
            Standard(
                name="公路路面基层施工技术规范",
                code="JTG 034-2000",
                category="施工规范",
                version="2000",
                description="规定了公路路面基层施工的技术要求",
                scope="适用于公路基层施工"
            ),
            # 质量评定标准
            Standard(
                name="公路工程质量检验评定标准 第一册 土建工程",
                code="JTG F80/1-2017",
                category="质量标准",
                version="2017",
                description="规定了公路工程质量检验评定的标准和方法",
                scope="适用于各等级公路工程"
            ),
            Standard(
                name="公路工程质量检验评定标准 第二册 机电工程",
                code="JTG F80/2-2017",
                category="质量标准",
                version="2017",
                description="规定了公路机电工程质量检验评定的标准",
                scope="适用于公路机电工程"
            ),
            # 施工安全规范
            Standard(
                name="公路工程施工安全技术规范",
                code="JTG F90-2015",
                category="安全规范",
                version="2015",
                description="规定了公路工程施工安全技术要求",
                scope="适用于各等级公路工程施工"
            ),
        ]
        
        for std in standards:
            self.store.create_entity(std)
            self.entity_ids[std.code] = std.id
            self.entity_ids[std.name] = std.id
    
    def _create_materials(self):
        """创建材料规格"""
        materials = [
            # 道路石油沥青
            Material(
                name="道路石油沥青AH-70",
                material_type="沥青材料",
                description="70号道路石油沥青，适用于炎热地区",
                specs={
                    "针入度(25℃, 100g, 5s)": "60-80 (0.1mm)",
                    "软化点(环球法)": "44-54 (℃)",
                    "延度(15℃, 5cm/min)": "≥100 (cm)",
                    "闪点(开口)": "≥230 (℃)",
                    "溶解度(三氯乙烯)": "≥99.5 (%)",
                    "蜡含量(蒸馏法)": "≤2.2 (%)",
                    "薄膜烘箱试验后质量变化": "-0.8~+0.8 (%)",
                    "薄膜烘箱试验后针入度比": "≥55 (%)",
                    "薄膜烘箱试验后延度(15℃)": "≥20 (cm)"
                },
                storage_conditions="储存温度宜控制在130-170℃，加热时间不宜超过6h"
            ),
            Material(
                name="道路石油沥青AH-90",
                material_type="沥青材料",
                description="90号道路石油沥青，适用于温和地区",
                specs={
                    "针入度(25℃, 100g, 5s)": "80-100 (0.1mm)",
                    "软化点(环球法)": "42-52 (℃)",
                    "延度(15℃, 5cm/min)": "≥100 (cm)",
                    "延度(10℃, 5cm/min)": "≥45 (cm)",
                    "闪点(开口)": "≥230 (℃)",
                    "溶解度(三氯乙烯)": "≥99.5 (%)",
                    "蜡含量(蒸馏法)": "≤2.0 (%)",
                    "薄膜烘箱试验后质量变化": "-0.8~+0.8 (%)",
                    "薄膜烘箱试验后针入度比": "≥57 (%)",
                    "薄膜烘箱试验后延度(10℃)": "≥8 (cm)"
                },
                storage_conditions="储存温度宜控制在130-170℃，加热时间不宜超过6h"
            ),
            Material(
                name="SBS改性沥青I-D",
                material_type="改性沥青",
                description="SBS I-D类改性沥青，用于高性能沥青路面",
                specs={
                    "针入度(25℃, 100g, 5s)": "30-60 (0.1mm)",
                    "软化点(环球法)": "≥70 (℃)",
                    "延度(5℃, 5cm/min)": "≥30 (cm)",
                    "运动粘度(135℃)": "≤3 (Pa·s)",
                    "闪点(开口)": "≥230 (℃)",
                    "溶解度(三氯乙烯)": "≥99 (%)",
                    "弹性恢复(25℃)": "≥75 (%)",
                    "离析(48h软化点差)": "≤2.5 (℃)",
                    "薄膜烘箱试验后质量变化": "≤1.0 (%)",
                    "薄膜烘箱试验后针入度比": "≥65 (%)"
                },
                storage_conditions="储存温度宜控制在150-180℃，使用前充分搅拌"
            ),
            # 水泥
            Material(
                name="普通硅酸盐水泥42.5",
                material_type="水泥",
                description="42.5级普通硅酸盐水泥，适用于道路基层",
                specs={
                    "强度等级": "42.5",
                    "细度(比表面积)": "≥300 (m²/kg)",
                    "初凝时间": "≥45 (min)",
                    "终凝时间": "≤600 (min)",
                    "安定性(沸煮法)": "合格",
                    "3d抗压强度": "≥17.0 (MPa)",
                    "28d抗压强度": "≥42.5 (MPa)",
                    "3d抗折强度": "≥3.5 (MPa)",
                    "28d抗折强度": "≥6.5 (MPa)"
                },
                storage_conditions="防潮储存，超过3个月需重新检验"
            ),
            Material(
                name="矿渣硅酸盐水泥32.5",
                material_type="水泥",
                description="32.5级矿渣硅酸盐水泥，适用于大体积混凝土",
                specs={
                    "强度等级": "32.5",
                    "细度(80μm筛余)": "≤12 (%)",
                    "初凝时间": "≥45 (min)",
                    "终凝时间": "≤600 (min)",
                    "安定性(沸煮法)": "合格",
                    "3d抗压强度": "≥11.0 (MPa)",
                    "28d抗压强度": "≥32.5 (MPa)"
                },
                storage_conditions="防潮储存，不同品种水泥分开存放"
            ),
            # 集料
            Material(
                name="粗集料(碎石)",
                material_type="集料",
                description="用于沥青路面和混凝土的粗集料",
                specs={
                    "石料压碎值": "≤26 (%)",
                    "洛杉矶磨耗损失": "≤28 (%)",
                    "表观密度": "≥2.6 (t/m³)",
                    "吸水率": "≤2.0 (%)",
                    "与沥青的粘附性": "≥4 级",
                    "针片状颗粒含量": "≤12 (%)",
                    "粉尘含量": "≤1 (%)",
                    "软石含量": "≤3 (%)",
                    "级配范围": "9.5-31.5mm连续级配"
                },
                storage_conditions="分规格堆放，避免离析和污染"
            ),
            Material(
                name="细集料(机制砂)",
                material_type="集料",
                description="用于沥青路面和混凝土的细集料",
                specs={
                    "表观密度": "≥2.6 (t/m³)",
                    "坚固性(硫酸钠溶液循环)": "≤8 (%)",
                    "含泥量(小于0.075mm)": "≤3 (%)",
                    "砂当量": "≥65 (%)",
                    "亚甲蓝值": "≤2.5 (g/kg)",
                    "棱角性(流动时间)": "≥30 (s)",
                    "级配范围": "0-4.75mm中粗砂"
                },
                storage_conditions="避免露天堆放导致含水率变化"
            ),
            Material(
                name="水泥稳定碎石混合料",
                material_type="混合料",
                description="水泥稳定碎石基层用混合料",
                specs={
                    "水泥剂量": "3-6 (%)",
                    "集料最大粒径": "31.5 (mm)",
                    "级配范围": "通过率符合规范要求",
                    "压实度": "≥96 (%)",
                    "7d无侧限抗压强度": "3-5 (MPa)",
                    "洛杉矶磨耗损失": "≤30 (%)",
                    "液限": "≤28 (%)",
                    "塑限": "≤9 (%)",
                    "塑性指数": "≤9"
                },
                storage_conditions="随拌随用，延迟时间不超过2h"
            ),
            Material(
                name="AC-16沥青混合料",
                material_type="混合料",
                description="AC-16中粒式沥青混凝土",
                specs={
                    "公称最大粒径": "16 (mm)",
                    "级配类型": "悬浮密实型",
                    "油石比": "4.5-5.5 (%)",
                    "设计空隙率": "3-5 (%)",
                    "稳定度": "≥7.5 (kN)",
                    "流值": "2-4 (mm)",
                    "VMA": "≥13.5 (%)",
                    "VFA": "65-75 (%)",
                    "残留稳定度": "≥80 (%)",
                    "冻融劈裂强度比": "≥75 (%)"
                },
                storage_conditions="运输温度≥150℃，摊铺温度≥140℃"
            ),
            Material(
                name="SMA-13沥青混合料",
                material_type="混合料",
                description="SMA-13沥青玛蹄脂碎石混合料",
                specs={
                    "公称最大粒径": "13.2 (mm)",
                    "级配类型": "骨架密实型",
                    "油石比": "5.5-6.5 (%)",
                    "设计空隙率": "2-4 (%)",
                    "稳定度": "≥6.0 (kN)",
                    "VMA": "≥17 (%)",
                    "VFA": "75-85 (%)",
                    "粗集料骨架间隙率": "≤VCAdrc",
                    "残留稳定度": "≥80 (%)",
                    "冻融劈裂强度比": "≥80 (%)",
                    "析漏损失": "≤0.1 (%)",
                    "肯特堡飞散损失": "≤15 (%)"
                },
                storage_conditions="运输温度≥160℃，摊铺温度≥150℃"
            ),
            Material(
                name="C40混凝土(桥面铺装)",
                material_type="混凝土",
                description="用于桥面铺装的C40混凝土",
                specs={
                    "强度等级": "C40",
                    "设计抗压强度": "40 (MPa)",
                    "抗折强度": "≥5.0 (MPa)",
                    "坍落度": "120-160 (mm)",
                    "含气量": "2-4 (%)",
                    "最大水胶比": "0.55",
                    "最小胶凝材料用量": "320 (kg/m³)",
                    "粗集料最大粒径": "20 (mm)",
                    "电通量": "≤1000 (C)",
                    "抗渗等级": "≥P8"
                },
                storage_conditions="及时养护，养护时间不少于14d"
            ),
        ]
        
        for mat in materials:
            self.store.create_entity(mat)
            self.entity_ids[mat.name] = mat.id
    
    def _create_processes(self):
        """创建施工工艺"""
        processes = [
            # 水泥稳定碎石基层施工
            Process(
                name="水泥稳定碎石基层施工",
                process_type="基层施工",
                description="水泥稳定碎石基层的施工工艺流程",
                duration=14,
                steps=[
                    "施工放样",
                    "准备下承层",
                    "备料",
                    "拌和",
                    "运输",
                    "摊铺",
                    "整平",
                    "碾压",
                    "接缝处理",
                    "养生"
                ],
                conditions="气温高于5℃，避开雨季施工，基层施工前下承层应验收合格"
            ),
            Process(
                name="水泥稳定碎石拌和",
                process_type="拌和作业",
                description="水泥稳定碎石的集中厂拌法",
                duration=1,
                steps=[
                    "原材料检验",
                    "配合比设计",
                    "设备标定",
                    "上料",
                    "加水拌和",
                    "质量检验",
                    "出料"
                ],
                conditions="含水量应大于最佳含水量1-2%，拌和均匀，无离析"
            ),
            Process(
                name="水泥稳定碎石碾压",
                process_type="碾压作业",
                description="水泥稳定碎石的碾压工艺",
                duration=1,
                steps=[
                    "初压(静压1-2遍)",
                    "复压(振动压实3-4遍)",
                    "终压(光轮压实1-2遍)",
                    "压实度检测",
                    "缺陷修补"
                ],
                conditions="碾压应重叠1/2轮宽，压实度达到设计要求"
            ),
            # 沥青路面面层施工
            Process(
                name="沥青路面面层施工",
                process_type="面层施工",
                description="沥青路面面层的施工工艺流程",
                duration=21,
                steps=[
                    "施工准备",
                    "配合比设计",
                    "混合料拌和",
                    "混合料运输",
                    "摊铺",
                    "压实",
                    "接缝处理",
                    "开放交通"
                ],
                conditions="地表温度不低于10℃，雨季避开施工"
            ),
            Process(
                name="沥青混合料拌和",
                process_type="拌和作业",
                description="沥青混合料的间歇式拌和工艺",
                duration=1,
                steps=[
                    "原材料加热",
                    "配合比设定",
                    "干拌",
                    "湿拌",
                    "矿粉加入",
                    "沥青加入",
                    "出料"
                ],
                conditions="沥青加热温度150-170℃，矿料加热温度160-190℃，出料温度140-155℃"
            ),
            Process(
                name="沥青混合料摊铺",
                process_type="摊铺作业",
                description="沥青混合料的摊铺施工",
                duration=1,
                steps=[
                    "下承层准备",
                    "施工放样",
                    "摊铺机就位",
                    "熨平板加热",
                    "螺旋布料器布料",
                    "找平",
                    "摊铺速度控制"
                ],
                conditions="摊铺温度不低于135℃，摊铺速度2-4m/min，熨平板预热不低于100℃"
            ),
            Process(
                name="沥青路面压实",
                process_type="压实作业",
                description="沥青路面的压实工艺",
                duration=1,
                steps=[
                    "初压(钢轮静压1-2遍)",
                    "复压(振动压实3-5遍)",
                    "终压(钢轮静压1-2遍)",
                    "温度检测",
                    "压实度检测"
                ],
                conditions="初压温度不低于130℃，复压温度不低于110℃，终压温度不低于70℃"
            ),
            # 混凝土桥面铺装施工
            Process(
                name="混凝土桥面铺装施工",
                process_type="桥面施工",
                description="水泥混凝土桥面铺装的施工工艺",
                duration=21,
                steps=[
                    "桥面清理",
                    "防水层施工",
                    "测量放样",
                    "钢筋绑扎",
                    "模板安装",
                    "混凝土浇筑",
                    "振捣",
                    "收面",
                    "养护",
                    "切缝"
                ],
                conditions="桥面应干燥清洁，混凝土强度达到设计要求后方可开放交通"
            ),
            Process(
                name="桥面防水层施工",
                process_type="防水施工",
                description="桥面防水层的施工工艺",
                duration=3,
                steps=[
                    "基层处理",
                    "防水材料喷涂",
                    "第一遍防水层",
                    "第二遍防水层",
                    "质量检验"
                ],
                conditions="基层应平整、干燥、无油污，喷涂温度不低于5℃"
            ),
            Process(
                name="混凝土桥面铺装浇筑",
                process_type="浇筑作业",
                description="桥面混凝土的浇筑施工",
                duration=1,
                steps=[
                    "混凝土运输",
                    "卸料",
                    "摊铺",
                    "振捣",
                    "整平",
                    "收面"
                ],
                conditions="混凝土坍落度120-160mm，浇筑应连续进行"
            ),
        ]
        
        for proc in processes:
            self.store.create_entity(proc)
            self.entity_ids[proc.name] = proc.id
    
    def _create_quality_standards(self):
        """创建质量标准"""
        quality_standards = [
            # 压实度要求
            QualityStandard(
                name="水泥稳定碎石基层压实度",
                standard_code="JTG F80/1-2017",
                index_name="压实度",
                index_value="≥96%",
                test_method="灌砂法",
                tolerance="单点值≥92%"
            ),
            QualityStandard(
                name="沥青面层压实度(高速公路)",
                standard_code="JTG F80/1-2017",
                index_name="压实度",
                index_value="≥96%",
                test_method="核子密度仪法/钻芯法",
                tolerance="代表值-2%，极值-4%"
            ),
            QualityStandard(
                name="沥青面层压实度(一级公路)",
                standard_code="JTG F80/1-2017",
                index_name="压实度",
                index_value="≥95%",
                test_method="核子密度仪法/钻芯法",
                tolerance="代表值-2%，极值-4%"
            ),
            QualityStandard(
                name="沥青面层压实度(二级公路)",
                standard_code="JTG F80/1-2017",
                index_name="压实度",
                index_value="≥94%",
                test_method="核子密度仪法/钻芯法",
                tolerance="代表值-2%，极值-4%"
            ),
            # 平整度要求
            QualityStandard(
                name="沥青路面平整度(高速公路)",
                standard_code="JTG F80/1-2017",
                index_name="平整度(3m直尺)",
                index_value="≤3mm",
                test_method="3m直尺法",
                tolerance="单点值≤5mm"
            ),
            QualityStandard(
                name="沥青路面车辙深度",
                standard_code="JTG F80/1-2017",
                index_name="车辙深度",
                index_value="≤5mm",
                test_method="车辙仪法",
                tolerance="设计时速>100km/h时≤5mm"
            ),
            QualityStandard(
                name="水泥混凝土路面平整度",
                standard_code="JTG F80/1-2017",
                index_name="平整度(3m直尺)",
                index_value="≤3mm",
                test_method="3m直尺法",
                tolerance="单点值≤5mm"
            ),
            QualityStandard(
                name="桥面铺装平整度",
                standard_code="JTG F80/1-2017",
                index_name="平整度(3m直尺)",
                index_value="≤3mm",
                test_method="3m直尺法",
                tolerance="桥面应平整，无跳车现象"
            ),
            # 厚度允许偏差
            QualityStandard(
                name="沥青面层厚度允许偏差(代表值)",
                standard_code="JTG F80/1-2017",
                index_name="厚度代表值",
                index_value="-5%H",
                test_method="钻芯法",
                tolerance="设计厚度H的-5%"
            ),
            QualityStandard(
                name="沥青面层厚度允许偏差(极值)",
                standard_code="JTG F80/1-2017",
                index_name="厚度极值",
                index_value="-10%H",
                test_method="钻芯法",
                tolerance="设计厚度H的-10%"
            ),
            QualityStandard(
                name="水泥稳定碎石基层厚度",
                standard_code="JTG F80/1-2017",
                index_name="厚度",
                index_value="≥设计厚度",
                test_method="挖坑法",
                tolerance="代表值-10mm，极值-20mm"
            ),
            QualityStandard(
                name="桥面铺装层厚度",
                standard_code="JTG F80/1-2017",
                index_name="厚度",
                index_value="≥设计厚度",
                test_method="钻芯法",
                tolerance="设计厚度±5mm"
            ),
            # 其他质量标准
            QualityStandard(
                name="沥青路面弯沉值",
                standard_code="JTG F80/1-2017",
                index_name="弯沉值",
                index_value="≤设计值",
                test_method="贝克曼梁法",
                tolerance="代表值≤设计弯沉值"
            ),
            QualityStandard(
                name="沥青路面渗水系数",
                standard_code="JTG F80/1-2017",
                index_name="渗水系数",
                index_value="≤300ml/min",
                test_method="渗水仪法",
                tolerance="中面层≤300ml/min，上面层≤200ml/min"
            ),
            QualityStandard(
                name="水泥混凝土路面抗折强度",
                standard_code="JTG F80/1-2017",
                index_name="抗折强度",
                index_value="≥5.0MPa",
                test_method="三点梁法",
                tolerance="以15个试件平均值为准"
            ),
            QualityStandard(
                name="桥面铺装混凝土强度",
                standard_code="JTG F80/1-2017",
                index_name="抗压强度",
                index_value="≥40MPa",
                test_method="立方体试件法",
                tolerance="同条件养护试件"
            ),
        ]
        
        for qs in quality_standards:
            self.store.create_entity(qs)
            self.entity_ids[qs.name] = qs.id
    
    def _create_relationships(self):
        """创建关系"""
        # 获取规范ID
        jtg_d20 = self.entity_ids.get("JTG D20-2017")
        jtg_f40 = self.entity_ids.get("JTG F40-2004")
        jtg_f80 = self.entity_ids.get("JTG F80/1-2017")
        jtg_034 = self.entity_ids.get("JTG 034-2000")
        
        # 获取材料ID
        ah70 = self.entity_ids.get("道路石油沥青AH-70")
        ah90 = self.entity_ids.get("道路石油沥青AH-90")
        sbs = self.entity_ids.get("SBS改性沥青I-D")
        cement_425 = self.entity_ids.get("普通硅酸盐水泥42.5")
        coarse_agg = self.entity_ids.get("粗集料(碎石)")
        fine_agg = self.entity_ids.get("细集料(机制砂)")
        csm = self.entity_ids.get("水泥稳定碎石混合料")
        ac16 = self.entity_ids.get("AC-16沥青混合料")
        sma13 = self.entity_ids.get("SMA-13沥青混合料")
        c40 = self.entity_ids.get("C40混凝土(桥面铺装)")
        
        # 获取工艺ID
        csm_proc = self.entity_ids.get("水泥稳定碎石基层施工")
        csm_mix = self.entity_ids.get("水泥稳定碎石拌和")
        csm_roll = self.entity_ids.get("水泥稳定碎石碾压")
        asphalt_proc = self.entity_ids.get("沥青路面面层施工")
        asphalt_mix = self.entity_ids.get("沥青混合料拌和")
        asphalt_pave = self.entity_ids.get("沥青混合料摊铺")
        asphalt_roll = self.entity_ids.get("沥青路面压实")
        bridge_proc = self.entity_ids.get("混凝土桥面铺装施工")
        bridge_water = self.entity_ids.get("桥面防水层施工")
        bridge_cast = self.entity_ids.get("混凝土桥面铺装浇筑")
        
        # 获取质量标准ID
        csm_compaction = self.entity_ids.get("水泥稳定碎石基层压实度")
        asphalt_compaction_hv = self.entity_ids.get("沥青面层压实度(高速公路)")
        asphalt_compaction_1 = self.entity_ids.get("沥青面层压实度(一级公路)")
        asphalt_smooth = self.entity_ids.get("沥青路面平整度(高速公路)")
        asphalt_rut = self.entity_ids.get("沥青路面车辙深度")
        bridge_smooth = self.entity_ids.get("桥面铺装平整度")
        asphalt_thick = self.entity_ids.get("沥青面层厚度允许偏差(代表值)")
        csm_thick = self.entity_ids.get("水泥稳定碎石基层厚度")
        bridge_thick = self.entity_ids.get("桥面铺装层厚度")
        
        relationships = []
        
        # ========== 规范与质量标准的关系 ==========
        if jtg_f80 and csm_compaction:
            relationships.append(create_contains_relation(jtg_f80, csm_compaction))
        if jtg_f80 and asphalt_compaction_hv:
            relationships.append(create_contains_relation(jtg_f80, asphalt_compaction_hv))
        if jtg_f80 and asphalt_smooth:
            relationships.append(create_contains_relation(jtg_f80, asphalt_smooth))
        if jtg_f80 and asphalt_thick:
            relationships.append(create_contains_relation(jtg_f80, asphalt_thick))
        if jtg_f80 and bridge_smooth:
            relationships.append(create_contains_relation(jtg_f80, bridge_smooth))
        
        # ========== 规范与工艺的关系 ==========
        if jtg_f40 and asphalt_proc:
            relationships.append(create_references_relation(asphalt_proc, jtg_f40))
        if jtg_034 and csm_proc:
            relationships.append(create_references_relation(csm_proc, jtg_034))
        if jtg_f80 and bridge_proc:
            relationships.append(create_references_relation(bridge_proc, jtg_f80))
        
        # ========== 规范适用于道路类型 ==========
        if jtg_d20:
            relationships.append(create_applies_to_relation(jtg_d20, "高速公路"))
            relationships.append(create_applies_to_relation(jtg_d20, "一级公路"))
            relationships.append(create_applies_to_relation(jtg_d20, "二级公路"))
        if jtg_f40:
            relationships.append(create_applies_to_relation(jtg_f40, "高速公路"))
            relationships.append(create_applies_to_relation(jtg_f40, "一级公路"))
            relationships.append(create_applies_to_relation(jtg_f40, "二级公路"))
            relationships.append(create_applies_to_relation(jtg_f40, "城市道路"))
        
        # ========== 工艺与材料的关系 ==========
        # 水泥稳定碎石工艺使用材料
        if csm_proc and cement_425:
            relationships.append(create_uses_relation(csm_proc, cement_425))
        if csm_proc and coarse_agg:
            relationships.append(create_uses_relation(csm_proc, coarse_agg))
        if csm_proc and fine_agg:
            relationships.append(create_uses_relation(csm_proc, fine_agg))
        if csm_proc and csm:
            relationships.append(create_depends_on_relation(csm_proc, csm))
        
        # 沥青路面工艺使用材料
        if asphalt_proc and ac16:
            relationships.append(create_uses_relation(asphalt_proc, ac16))
        if asphalt_proc and sma13:
            relationships.append(create_uses_relation(asphalt_proc, sma13))
        if asphalt_proc and ah70:
            relationships.append(create_depends_on_relation(asphalt_proc, ah70))
        if asphalt_proc and ah90:
            relationships.append(create_depends_on_relation(asphalt_proc, ah90))
        if asphalt_proc and sbs:
            relationships.append(create_depends_on_relation(asphalt_proc, sbs))
        
        # 沥青混合料拌和使用材料
        if asphalt_mix and ah70:
            relationships.append(create_uses_relation(asphalt_mix, ah70))
        if asphalt_mix and ah90:
            relationships.append(create_uses_relation(asphalt_mix, ah90))
        if asphalt_mix and sbs:
            relationships.append(create_uses_relation(asphalt_mix, sbs))
        if asphalt_mix and coarse_agg:
            relationships.append(create_uses_relation(asphalt_mix, coarse_agg))
        if asphalt_mix and fine_agg:
            relationships.append(create_uses_relation(asphalt_mix, fine_agg))
        
        # 桥面铺装工艺使用材料
        if bridge_proc and c40:
            relationships.append(create_uses_relation(bridge_proc, c40))
        if bridge_proc and cement_425:
            relationships.append(create_uses_relation(bridge_proc, cement_425))
        
        # 防水层施工使用材料
        if bridge_water and coarse_agg:
            relationships.append(create_depends_on_relation(bridge_water, coarse_agg))
        
        # ========== 工艺与质量标准的关系 ==========
        if csm_proc and csm_compaction:
            relationships.append(create_has_standard_relation(csm_proc, csm_compaction))
        if csm_proc and csm_thick:
            relationships.append(create_has_standard_relation(csm_proc, csm_thick))
        if asphalt_proc and asphalt_compaction_hv:
            relationships.append(create_has_standard_relation(asphalt_proc, asphalt_compaction_hv))
        if asphalt_proc and asphalt_smooth:
            relationships.append(create_has_standard_relation(asphalt_proc, asphalt_smooth))
        if asphalt_proc and asphalt_rut:
            relationships.append(create_has_standard_relation(asphalt_proc, asphalt_rut))
        if asphalt_proc and asphalt_thick:
            relationships.append(create_has_standard_relation(asphalt_proc, asphalt_thick))
        if bridge_proc and bridge_smooth:
            relationships.append(create_has_standard_relation(bridge_proc, bridge_smooth))
        if bridge_proc and bridge_thick:
            relationships.append(create_has_standard_relation(bridge_proc, bridge_thick))
        
        # ========== 工艺之间的前置关系 ==========
        if asphalt_proc and csm_proc:
            relationships.append(create_requires_relation(asphalt_proc, csm_proc))
        if asphalt_mix and asphalt_proc:
            relationships.append(create_requires_relation(asphalt_mix, asphalt_proc))
        if asphalt_pave and asphalt_mix:
            relationships.append(create_requires_relation(asphalt_pave, asphalt_mix))
        if asphalt_roll and asphalt_pave:
            relationships.append(create_requires_relation(asphalt_roll, asphalt_pave))
        if bridge_water and bridge_proc:
            relationships.append(create_requires_relation(bridge_water, bridge_proc))
        if bridge_cast and bridge_water:
            relationships.append(create_requires_relation(bridge_cast, bridge_water))
        
        # 创建所有关系
        for rel in relationships:
            self.store.create_relationship(rel)


def create_has_standard_relation(process_id: str, standard_id: str, 
                                  weight: float = 1.0) -> Relationship:
    """创建拥有标准关系"""
    return create_relationship(
        source_id=process_id,
        target_id=standard_id,
        rel_type=RelationshipType.HAS_STANDARD,
        weight=weight,
    )


def seed_road_engineering(db_path: str = "knowledge_graph.db") -> Dict[str, int]:
    """填充道路工程领域知识数据
    
    Args:
        db_path: 数据库路径
    
    Returns:
        统计信息
    """
    store = KnowledgeGraphStore(db_path)
    
    # 检查是否已有数据
    stats = store.get_statistics()
    if stats["total_entities"] > 10:
        print(f"知识图谱已有数据，跳过初始化")
        return stats
    
    seeder = RoadEngineeringSeedData(store)
    result = seeder.seed_all()
    
    print(f"道路工程知识图谱初始化完成:")
    print(f"  - 实体数量: {result['entities']}")
    print(f"  - 关系数量: {result['relationships']}")
    
    return result


if __name__ == "__main__":
    seed_road_engineering()
