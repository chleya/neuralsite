# -*- coding: utf-8 -*-
"""
语义归一映射

包含：材料名称、结构类型、工程部位等语义映射
"""

from typing import Dict, Optional, List


class SemanticMapper:
    """语义归一映射"""
    
    # ==================== 材料语义映射 ====================
    
    MATERIAL_MAPPINGS = {
        # 沥青类
        "沥青混凝土": {"code": "MAT-AC", "name": "沥青混凝土", "category": "路面"},
        "沥青砼": {"code": "MAT-AC", "name": "沥青混凝土", "category": "路面"},
        "AC": {"code": "MAT-AC", "name": "沥青混凝土", "category": "路面"},
        "SMA": {"code": "MAT-SMA", "name": "沥青玛蹄脂碎石", "category": "路面"},
        "沥青玛蹄脂碎石": {"code": "MAT-SMA", "name": "沥青玛蹄脂碎石", "category": "路面"},
        "OGFC": {"code": "MAT-OGFC", "name": "开级配排水式沥青磨耗层", "category": "路面"},
        
        # 水泥类
        "水泥稳定碎石": {"code": "MAT-CRB", "name": "水泥稳定碎石", "category": "基层"},
        "水稳": {"code": "MAT-CRB", "name": "水泥稳定碎石", "category": "基层"},
        "CRB": {"code": "MAT-CRB", "name": "水泥稳定碎石", "category": "基层"},
        "水泥稳定级配碎石": {"code": "MAT-CRB", "name": "水泥稳定碎石", "category": "基层"},
        "水泥稳定土": {"code": "MAT-CSG", "name": "水泥稳定土", "category": "基层"},
        "水稳土": {"code": "MAT-CSG", "name": "水泥稳定土", "category": "基层"},
        
        # 二灰类
        "二灰碎石": {"code": "MAT-LSG", "name": "石灰粉煤灰稳定碎石", "category": "基层"},
        "二灰土": {"code": "MAT-LSA", "name": "石灰粉煤灰稳定土", "category": "基层"},
        "石灰粉煤灰碎石": {"code": "MAT-LSG", "name": "石灰粉煤灰稳定碎石", "category": "基层"},
        "石灰粉煤灰土": {"code": "MAT-LSA", "name": "石灰粉煤灰稳定土", "category": "基层"},
        
        # 碎石类
        "级配碎石": {"code": "MAT-GP", "name": "级配碎石", "category": "底基层"},
        "未筛分碎石": {"code": "MAT-UP", "name": "未筛分碎石", "category": "底基层"},
        "天然砂砾": {"code": "MAT-NG", "name": "天然砂砾", "category": "底基层"},
        
        # 水泥混凝土类
        "水泥混凝土": {"code": "MAT-CC", "name": "水泥混凝土", "category": "路面"},
        "砼": {"code": "MAT-CC", "name": "水泥混凝土", "category": "路面"},
        "混凝土": {"code": "MAT-CC", "name": "水泥混凝土", "category": "路面"},
        "C30": {"code": "MAT-CC-C30", "name": "C30水泥混凝土", "category": "路面"},
        "C35": {"code": "MAT-CC-C35", "name": "C35水泥混凝土", "category": "路面"},
        "C40": {"code": "MAT-CC-C40", "name": "C40水泥混凝土", "category": "路面"},
        
        # 钢材
        "Q235": {"code": "MAT-STL-Q235", "name": "Q235钢", "category": "钢材"},
        "Q345": {"code": "MAT-STL-Q345", "name": "Q345钢", "category": "钢材"},
        "HRB400": {"code": "MAT-RB-HRB400", "name": "HRB400钢筋", "category": "钢筋"},
        
        # 木材
        "木材": {"code": "MAT-WD", "name": "木材", "category": "其他"},
        "原木": {"code": "MAT-WD", "name": "木材", "category": "其他"},
        
        # 土工材料
        "土工格栅": {"code": "MAT-GG", "name": "土工格栅", "category": "土工合成材料"},
        "土工布": {"code": "MAT-GT", "name": "土工布", "category": "土工合成材料"},
        "防水板": {"code": "MAT-WB", "name": "防水板", "category": "防水材料"},
    }
    
    # ==================== 结构类型映射 ====================
    
    STRUCTURE_MAPPINGS = {
        # 路面结构
        "路面": {"code": "STR-PAVEMENT", "name": "路面结构"},
        "面层": {"code": "STR-SURFACE", "name": "面层"},
        "上面层": {"code": "STR-SURFACE-UP", "name": "上面层"},
        "中面层": {"code": "STR-SURFACE-MID", "name": "中面层"},
        "下面层": {"code": "STR-SURFACE-LOW", "name": "下面层"},
        
        # 基层
        "基层": {"code": "STR-BASE", "name": "基层"},
        "上基层": {"code": "STR-BASE-UP", "name": "上基层"},
        "下基层": {"code": "STR-BASE-LOW", "name": "下基层"},
        
        # 底基层
        "底基层": {"code": "STR-SUBBASE", "name": "底基层"},
        "垫层": {"code": "STR-CUSHION", "name": "垫层"},
        
        # 桥梁结构
        "桥梁": {"code": "STR-BRIDGE", "name": "桥梁"},
        "桥面": {"code": "STR-BRIDGE-DECK", "name": "桥面"},
        "桥墩": {"code": "STR-BRIDGE-PIER", "name": "桥墩"},
        "桥台": {"code": "STR-BRIDGE-ABUTMENT", "name": "桥台"},
        "承台": {"code": "STR-BRIDGE-CAP", "name": "承台"},
        "桩基": {"code": "STR-BRIDGE-PILE", "name": "桩基"},
        "系梁": {"code": "STR-BRIDGE-TIE", "name": "系梁"},
        "盖梁": {"code": "STR-BRIDGE-COPING", "name": "盖梁"},
        
        # 隧道结构
        "隧道": {"code": "STR-TUNNEL", "name": "隧道"},
        "洞身": {"code": "STR-TUNNEL-BODY", "name": "洞身"},
        "洞门": {"code": "STR-TUNNEL-PORTAL", "name": "洞门"},
        "明洞": {"code": "STR-TUNNEL-CUTCOVER", "name": "明洞"},
        "衬砌": {"code": "STR-TUNNEL-LINING", "name": "衬砌"},
        
        # 涵洞结构
        "涵洞": {"code": "STR-CULVERT", "name": "涵洞"},
        "涵身": {"code": "STR-CULVERT-BODY", "name": "涵身"},
        "洞口": {"code": "STR-CULVERT-PORTAL", "name": "洞口"},
        "基础": {"code": "STR-FOUNDATION", "name": "基础"},
        
        # 防护结构
        "边坡": {"code": "STR-SLOPE", "name": "边坡"},
        "挡土墙": {"code": "STR-RETAINING", "name": "挡土墙"},
        "抗滑桩": {"code": "STR-ANTI-SLIDE", "name": "抗滑桩"},
        "锚杆": {"code": "STR-ANCHOR", "name": "锚杆"},
        "锚索": {"code": "STR-CABLE", "name": "锚索"},
        
        # 排水结构
        "排水沟": {"code": "STR-DRAINAGE", "name": "排水沟"},
        "截水沟": {"code": "STR-CATCHWATER", "name": "截水沟"},
        "急流槽": {"code": "STR-CHUTE", "name": "急流槽"},
        "渗沟": {"code": "STR-SUBDRAIN", "name": "渗沟"},
        "盲沟": {"code": "STR-BLINDDRAIN", "name": "盲沟"},
    }
    
    # ==================== 工程部位映射 ====================
    
    LOCATION_MAPPINGS = {
        # 路线部位
        "路基": {"code": "LOC-SUBGRADE", "name": "路基"},
        "路堤": {"code": "LOC-EMBANKMENT", "name": "路堤"},
        "路堑": {"code": "LOC-CUT", "name": "路堑"},
        "半填半挖": {"code": "LOC-HALFCUT", "name": "半填半挖"},
        "高填方": {"code": "LOC-HIGHFILL", "name": "高填方"},
        "深挖方": {"code": "LOC-DEEPCUT", "name": "深挖方"},
        
        # 桥梁部位
        "基础": {"code": "LOC-FOUNDATION", "name": "基础"},
        "下部": {"code": "LOC-SUBSTRUCTURE", "name": "下部结构"},
        "上部": {"code": "LOC-SUPERSTRUCTURE", "name": "上部结构"},
        "桥跨": {"code": "LOC-SPAN", "name": "桥跨"},
        
        # 隧道部位
        "入口": {"code": "LOC-ENTRY", "name": "入口"},
        "出口": {"code": "LOC-EXIT", "name": "出口"},
        "洞身段": {"code": "LOC-TUNNEL-SECTION", "name": "洞身段"},
        
        # 方向
        "左侧": {"code": "LOC-LEFT", "name": "左侧"},
        "右侧": {"code": "LOC-RIGHT", "name": "右侧"},
        "中央": {"code": "LOC-CENTER", "name": "中央"},
    }
    
    # ==================== 地基类型映射 ====================
    
    FOUNDATION_MAPPINGS = {
        "天然地基": {"code": "FND-NATURAL", "name": "天然地基"},
        "人工地基": {"code": "FND-ARTIFICIAL", "name": "人工地基"},
        "换填": {"code": "FND-REPLACE", "name": "换填地基"},
        "桩基": {"code": "FND-PILE", "name": "桩基础"},
        "筏板": {"code": "FND-RAFT", "name": "筏板基础"},
    }
    
    # ==================== 映射方法 ====================
    
    @classmethod
    def map_material(cls, text: str) -> dict:
        """
        映射材料名称
        
        Args:
            text: 材料名称
            
        Returns:
            {"code": "MAT-XXX", "name": "标准名称", "category": "分类"}
        """
        # 精确匹配
        if text in cls.MATERIAL_MAPPINGS:
            return cls.MATERIAL_MAPPINGS[text].copy()
        
        # 模糊匹配 - 遍历查找包含关系
        for key, value in cls.MATERIAL_MAPPINGS.items():
            if key in text or text in key:
                result = value.copy()
                result["original"] = text
                return result
        
        # 未找到匹配
        return {"code": "UNKNOWN", "name": text, "category": "未知"}
    
    @classmethod
    def map_structure(cls, text: str) -> dict:
        """
        映射结构类型
        
        Args:
            text: 结构类型
            
        Returns:
            {"code": "STR-XXX", "name": "标准名称"}
        """
        # 精确匹配
        if text in cls.STRUCTURE_MAPPINGS:
            return cls.STRUCTURE_MAPPINGS[text].copy()
        
        # 模糊匹配
        for key, value in cls.STRUCTURE_MAPPINGS.items():
            if key in text or text in key:
                result = value.copy()
                result["original"] = text
                return result
        
        return {"code": "UNKNOWN", "name": text}
    
    @classmethod
    def map_location(cls, text: str) -> dict:
        """
        映射工程部位
        
        Args:
            text: 部位名称
            
        Returns:
            {"code": "LOC-XXX", "name": "标准名称"}
        """
        if text in cls.LOCATION_MAPPINGS:
            return cls.LOCATION_MAPPINGS[text].copy()
        
        for key, value in cls.LOCATION_MAPPINGS.items():
            if key in text or text in key:
                result = value.copy()
                result["original"] = text
                return result
        
        return {"code": "UNKNOWN", "name": text}
    
    @classmethod
    def map_foundation(cls, text: str) -> dict:
        """
        映射地基类型
        
        Args:
            text: 地基类型
            
        Returns:
            {"code": "FND-XXX", "name": "标准名称"}
        """
        if text in cls.FOUNDATION_MAPPINGS:
            return cls.FOUNDATION_MAPPINGS[text].copy()
        
        for key, value in cls.FOUNDATION_MAPPINGS.items():
            if key in text or text in key:
                result = value.copy()
                result["original"] = text
                return result
        
        return {"code": "UNKNOWN", "name": text}
    
    @classmethod
    def map_all(cls, material: Optional[str] = None, 
                structure: Optional[str] = None,
                location: Optional[str] = None,
                foundation: Optional[str] = None) -> Dict[str, dict]:
        """
        综合映射多个字段
        
        Args:
            material: 材料名称
            structure: 结构类型
            location: 工程部位
            foundation: 地基类型
            
        Returns:
            {"material": {...}, "structure": {...}, ...}
        """
        result = {}
        
        if material:
            result["material"] = cls.map_material(material)
        if structure:
            result["structure"] = cls.map_structure(structure)
        if location:
            result["location"] = cls.map_location(location)
        if foundation:
            result["foundation"] = cls.map_foundation(foundation)
        
        return result
    
    @classmethod
    def get_category_materials(cls, category: str) -> List[dict]:
        """
        获取指定分类的所有材料
        
        Args:
            category: 分类名称
            
        Returns:
            [{"code": "...", "name": "..."}, ...]
        """
        return [
            {"code": v["code"], "name": v["name"]}
            for v in cls.MATERIAL_MAPPINGS.values()
            if v.get("category") == category
        ]
    
    @classmethod
    def search(cls, keyword: str) -> List[dict]:
        """
        搜索所有映射
        
        Args:
            keyword: 关键词
            
        Returns:
            [{"type": "material/structure/location/foundation", ...}, ...]
        """
        results = []
        
        # 搜索材料
        for key, value in cls.MATERIAL_MAPPINGS.items():
            if keyword in key or keyword in value["name"]:
                results.append({**value, "type": "material", "original": key})
        
        # 搜索结构
        for key, value in cls.STRUCTURE_MAPPINGS.items():
            if keyword in key or keyword in value["name"]:
                results.append({**value, "type": "structure", "original": key})
        
        # 搜索部位
        for key, value in cls.LOCATION_MAPPINGS.items():
            if keyword in key or keyword in value["name"]:
                results.append({**value, "type": "location", "original": key})
        
        return results
