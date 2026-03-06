# -*- coding: utf-8 -*-
"""
图数据模块 - 道路/桥梁空间数据管理
基于桩号的图结构，用于存储和管理空间数据
"""
from typing import Dict, List, Optional, Tuple
import openpyxl


class StationNode:
    """桩号节点"""
    def __init__(self, station_id: int, station_name: str, elevation: float = 0.0, 
                 x: float = 0.0, y: float = 0.0, data: dict = None):
        self.station_id = station_id  # 桩号ID (如 4300)
        self.station_name = station_name  # 桩号名称 (如 "K4+300")
        self.elevation = elevation  # 高程 (m)
        self.x = x  # X坐标 (东向)
        self.y = y  # Y坐标 (北向)
        self.data = data or {}  # 附加数据
    
    def __repr__(self):
        return f"StationNode({self.station_name}, H={self.elevation}m)"
    
    def to_dict(self):
        return {
            'station_id': self.station_id,
            'station_name': self.station_name,
            'elevation': self.elevation,
            'x': self.x,
            'y': self.y,
            'data': self.data
        }


class RoadSegment:
    """道路段"""
    def __init__(self, start_station: StationNode, end_station: StationNode, 
                 length: float = 0.0, data: dict = None):
        self.start = start_station
        self.end = end_station
        self.length = length  # 长度 (m)
        self.data = data or {}
    
    def __repr__(self):
        return f"RoadSegment({self.start.station_name} -> {self.end.station_name}, {self.length}m)"
    
    @property
    def slope(self):
        """坡度 (%)"""
        if self.length > 0:
            return (self.end.elevation - self.start.elevation) / self.length * 100
        return 0
    
    def to_dict(self):
        return {
            'start': self.start.station_name,
            'end': self.end.station_name,
            'length': self.length,
            'slope': self.slope,
            'data': self.data
        }


class RoadGraph:
    """道路图数据"""
    
    def __init__(self, name: str = "未命名道路"):
        self.name = name
        self.nodes: Dict[int, StationNode] = {}  # station_id -> StationNode
        self.segments: List[RoadSegment] = []  # 道路段列表
        self.photos: Dict[int, List[str]] = {}  # station_id -> [photo_paths]
        self.issues: Dict[int, List[dict]] = {}  # station_id -> [issues]
    
    def add_station(self, station_id: int, station_name: str, elevation: float = 0.0,
                    x: float = 0.0, y: float = 0.0, data: dict = None):
        """添加桩号节点"""
        node = StationNode(station_id, station_name, elevation, x, y, data)
        self.nodes[station_id] = node
        return node
    
    def build_segments(self):
        """根据节点自动构建道路段"""
        self.segments = []
        sorted_ids = sorted(self.nodes.keys())
        
        for i in range(len(sorted_ids) - 1):
            start_id = sorted_ids[i]
            end_id = sorted_ids[i + 1]
            
            start_node = self.nodes[start_id]
            end_node = self.nodes[end_id]
            
            # 计算距离 (简化为桩号差)
            length = end_id - start_id
            
            segment = RoadSegment(start_node, end_node, length)
            self.segments.append(segment)
        
        return self.segments
    
    def get_station_by_name(self, name: str) -> Optional[StationNode]:
        """按桩号名称查找节点"""
        for node in self.nodes.values():
            if node.station_name == name:
                return node
        return None
    
    def get_nearby_stations(self, station_id: int, range_meters: int = 100) -> List[StationNode]:
        """查找附近的桩号"""
        nearby = []
        for id, node in self.nodes.items():
            if abs(id - station_id) <= range_meters:
                nearby.append(node)
        return sorted(nearby, key=lambda n: abs(n.station_id - station_id))
    
    def add_photo(self, station_id: int, photo_path: str):
        """关联照片到桩号"""
        if station_id not in self.photos:
            self.photos[station_id] = []
        self.photos[station_id].append(photo_path)
    
    def add_issue(self, station_id: int, issue: dict):
        """添加问题到桩号"""
        if station_id not in self.issues:
            self.issues[station_id] = []
        self.issues[station_id].append(issue)
    
    def get_station_info(self, station_id: int) -> dict:
        """获取桩号完整信息"""
        node = self.nodes.get(station_id)
        if not node:
            return {'error': '桩号不存在'}
        
        return {
            'station': node.to_dict(),
            'photos': self.photos.get(station_id, []),
            'issues': self.issues.get(station_id, [])
        }
    
    def get_elevation_profile(self) -> List[Tuple[str, float]]:
        """获取高程纵断面数据"""
        return [(node.station_name, node.elevation) 
                for node in sorted(self.nodes.values(), key=lambda n: n.station_id)]
    
    def summary(self) -> str:
        """图数据摘要"""
        return f"{self.name}: {len(self.nodes)}个桩号, {len(self.segments)}个道路段"


def load_from_excel(file_path: str, sheet_name: str = '右幅') -> RoadGraph:
    """从Excel加载道路数据"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb[sheet_name]
    
    graph = RoadGraph("从Excel导入")
    
    # 读取桩号和高程数据 (列1=桩号, 列6=路面高程)
    # 根据实际Excel结构，路面高程在F列(第6列)
    for row in ws.iter_rows(min_row=11, max_row=100, min_col=1, max_col=6, values_only=True):
        if row[0] and isinstance(row[0], (int, float)):
            station_id = int(row[0])
            # 尝试从不同列获取高程
            elevation = row[5] if row[5] and isinstance(row[5], (int, float)) else 0
            
            # 如果第一列也是数字，可能是坡率不是高程
            if elevation == 0 and len(row) > 10 and row[10]:
                elevation = row[10] if isinstance(row[10], (int, float)) else 0
            
            # 转换为桩号名称
            km = station_id // 1000
            offset = station_id % 1000
            station_name = f"K{km}+{offset:03d}"
            
            graph.add_station(station_id, station_name, elevation)
    
    # 构建道路段
    graph.build_segments()
    
    return graph


# 测试
if __name__ == "__main__":
    # 创建测试图数据
    graph = RoadGraph("测试道路")
    
    # 添加桩号节点
    graph.add_station(4300, "K4+300", 278.74)
    graph.add_station(4400, "K4+400", 275.50)
    graph.add_station(4500, "K4+500", 272.30)
    graph.add_station(4600, "K4+600", 269.10)
    graph.add_station(4700, "K4+700", 265.90)
    graph.add_station(4800, "K4+800", 262.70)
    graph.add_station(4900, "K4+900", 259.50)
    graph.add_station(5000, "K5+000", 256.30)
    
    # 构建道路段
    graph.build_segments()
    
    # 测试查询
    print(graph.summary())
    print()
    
    # 高程纵断面
    print("高程纵断面:")
    for name, elev in graph.get_elevation_profile():
        print(f"  {name}: {elev}m")
    
    print()
    
    # 查找附近桩号
    print("K4+500附近桩号:")
    nearby = graph.get_nearby_stations(4500, 200)
    for node in nearby:
        print(f"  {node.station_name}: {node.elevation}m")
    
    print()
    
    # 添加照片和问题
    graph.add_photo(4500, "photo_001.jpg")
    graph.add_photo(4500, "photo_002.jpg")
    graph.add_issue(4500, {'type': '裂缝', 'severity': '中度'})
    
    # 获取完整信息
    info = graph.get_station_info(4500)
    print(f"K4+500 完整信息:")
    print(f"  高程: {info['station']['elevation']}m")
    print(f"  照片: {info['photos']}")
    print(f"  问题: {info['issues']}")
