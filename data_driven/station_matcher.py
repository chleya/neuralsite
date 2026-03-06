# -*- coding: utf-8 -*-
"""
桩号自动匹配模块

根据GPS坐标匹配最近桩号
"""

from typing import Optional, List, Dict, Any, Tuple
import math
import sys
import os

# 添加core路径以便导入spatial模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'core'))

try:
    from core.spatial.database import SpatialDatabase, SpatialPoint, get_spatial_db
except ImportError:
    # Fallback: 使用本地的简单实现
    SpatialDatabase = None
    SpatialPoint = None
    get_spatial_db = None


class StationMatcher:
    """桩号匹配器"""
    
    def __init__(self, engine=None, connection_string: str = None):
        """
        初始化匹配器
        
        Args:
            engine: 空间数据库引擎实例 (可选)
            connection_string: 数据库连接字符串 (可选)
        """
        self.engine = engine
        self.connection_string = connection_string
        self._db = None
        
        # 如果传入了engine，直接使用
        if engine is not None:
            self._db = engine
        elif get_spatial_db is not None:
            # 尝试获取默认的空间数据库
            try:
                self._db = get_spatial_db(connection_string)
            except Exception as e:
                print(f"Failed to initialize spatial db: {e}")
        
        # 内存中的桩号缓存 (备选)
        self._station_cache: List[SpatialPoint] = []
    
    @property
    def db(self) -> Optional[SpatialDatabase]:
        """获取数据库实例"""
        return self._db
    
    def add_station(self, station: str, x: float, y: float, 
                   elevation: float = 0, azimuth: float = 0,
                   point_type: str = "centerline",
                   project_id: int = 1) -> int:
        """
        添加桩号到数据库
        
        Args:
            station: 桩号字符串 (如 "K0+000")
            x: X坐标 (经度或东坐标)
            y: Y坐标 (纬度或北坐标)
            elevation: 高程
            azimuth: 方位角
            point_type: 点类型
            project_id: 项目ID
            
        Returns:
            添加的点的ID
        """
        if self._db is not None:
            point = SpatialPoint(
                id=None,
                project_id=project_id,
                chainage=station,
                point_type=point_type,
                x=x,
                y=y,
                z=elevation,
                azimuth=azimuth
            )
            return self._db.add_point(point)
        else:
            # 内存缓存
            point = SpatialPoint(
                id=len(self._station_cache) + 1,
                project_id=project_id,
                chainage=station,
                point_type=point_type,
                x=x,
                y=y,
                z=elevation,
                azimuth=azimuth
            )
            self._station_cache.append(point)
            return point.id
    
    def add_stations_batch(self, stations: List[Dict[str, Any]], 
                          project_id: int = 1) -> int:
        """
        批量添加桩号
        
        Args:
            stations: 桩号列表，每项包含 station, x, y, elevation, azimuth, point_type
            project_id: 项目ID
            
        Returns:
            添加的数量
        """
        count = 0
        for s in stations:
            self.add_station(
                station=s.get('station', ''),
                x=s.get('x', 0),
                y=s.get('y', 0),
                elevation=s.get('elevation', 0),
                azimuth=s.get('azimuth', 0),
                point_type=s.get('point_type', 'centerline'),
                project_id=project_id
            )
            count += 1
        return count
    
    def match_station(self, lat: float, lon: float, 
                     max_distance: float = 100,
                     project_id: int = None) -> Optional[Dict[str, Any]]:
        """
        根据GPS坐标匹配最近桩号
        
        Args:
            lat: 纬度 (WGS84)
            lon: 经度 (WGS84)
            max_distance: 最大搜索距离(米)
            project_id: 项目ID过滤
            
        Returns:
            匹配的桩号信息 {
                "station": "K0+000",
                "distance": 5.2,  # 米
                "x": 500000,
                "y": 3000000,
                "elevation": 100,
                "azimuth": 45
            } 或 None
        """
        # 如果有数据库，使用数据库查询
        if self._db is not None:
            result = self._db.nearest_station(lat, lon, project_id)
            if result:
                point, distance = result
                if distance <= max_distance:
                    return {
                        "station": point.chainage,
                        "distance": round(distance, 2),
                        "x": point.x,
                        "y": point.y,
                        "elevation": point.z,
                        "azimuth": point.azimuth,
                        "point_type": point.point_type,
                        "project_id": point.project_id
                    }
            return None
        
        # 使用内存缓存
        return self._match_from_cache(lat, lon, max_distance, project_id)
    
    def _match_from_cache(self, lat: float, lon: float,
                         max_distance: float,
                         project_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """从内存缓存中匹配"""
        if not self._station_cache:
            return None
        
        min_dist = float('inf')
        nearest = None
        
        for point in self._station_cache:
            if project_id and point.project_id != project_id:
                continue
            
            # 计算距离 (简化版)
            dx = point.x - lon
            dy = point.y - lat
            dist = math.sqrt(dx * dx + dy * dy)
            
            # 简化: 假设1度约等于111km
            dist_meters = dist * 111000
            
            if dist_meters < min_dist:
                min_dist = dist_meters
                nearest = point
        
        if nearest and min_dist <= max_distance:
            return {
                "station": nearest.chainage,
                "distance": round(min_dist, 2),
                "x": nearest.x,
                "y": nearest.y,
                "elevation": nearest.z,
                "azimuth": nearest.azimuth,
                "point_type": nearest.point_type,
                "project_id": nearest.project_id
            }
        
        return None
    
    def query_nearby(self, lat: float, lon: float,
                    radius: float = 100,
                    project_id: int = None) -> List[Dict[str, Any]]:
        """
        查询指定范围内的所有桩号
        
        Args:
            lat: 纬度
            lon: 经度
            radius: 搜索半径(米)
            project_id: 项目ID过滤
            
        Returns:
            附近的桩号列表
        """
        if self._db is not None:
            # 简化: 将WGS84转为项目坐标后再查询
            # 实际应使用坐标转换
            points = self._db.query_nearby(lon, lat, radius, project_id)
            return [
                {
                    "station": p.chainage,
                    "distance": self._calculate_distance(lat, lon, p.y, p.x),
                    "x": p.x,
                    "y": p.y,
                    "elevation": p.z,
                    "azimuth": p.azimuth,
                    "point_type": p.point_type
                }
                for p in points
            ]
        
        # 内存缓存查询
        return self._query_nearby_cache(lat, lon, radius, project_id)
    
    def _query_nearby_cache(self, lat: float, lon: float,
                           radius: float,
                           project_id: Optional[int]) -> List[Dict[str, Any]]:
        """从内存缓存中查询附近"""
        results = []
        
        for point in self._station_cache:
            if project_id and point.project_id != project_id:
                continue
            
            dist = self._calculate_distance(lat, lon, point.y, point.x)
            
            if dist <= radius:
                results.append({
                    "station": point.chainage,
                    "distance": round(dist, 2),
                    "x": point.x,
                    "y": point.y,
                    "elevation": point.z,
                    "azimuth": point.azimuth,
                    "point_type": point.point_type
                })
        
        # 按距离排序
        results.sort(key=lambda x: x['distance'])
        return results
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
        """计算两点之间的距离(米) - Haversine公式"""
        R = 6371000  # 地球半径(米)
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * 
             math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_all_stations(self, project_id: int = None) -> List[str]:
        """
        获取所有桩号
        
        Args:
            project_id: 项目ID过滤
            
        Returns:
            桩号字符串列表
        """
        if self._db is not None:
            # 简化实现
            if project_id:
                points = self._db.query_by_chainage("K0+000", "K999+999", project_id)
            else:
                points = self._db.query_by_chainage("K0+000", "K999+999", None)
            return [p.chainage for p in points]
        
        # 内存缓存
        if project_id:
            return [p.chainage for p in self._station_cache if p.project_id == project_id]
        return [p.chainage for p in self._station_cache]
    
    def clear_cache(self):
        """清空内存缓存"""
        self._station_cache = []


# 测试
if __name__ == "__main__":
    # 创建匹配器
    matcher = StationMatcher()
    
    # 添加测试桩号 (示例坐标)
    test_stations = [
        {"station": "K0+000", "x": 121.4737, "y": 31.2304, "elevation": 10},
        {"station": "K0+100", "x": 121.4747, "y": 31.2314, "elevation": 12},
        {"station": "K0+200", "x": 121.4757, "y": 31.2324, "elevation": 15},
        {"station": "K0+300", "x": 121.4767, "y": 31.2334, "elevation": 18},
        {"station": "K0+400", "x": 121.4777, "y": 31.2344, "elevation": 20},
    ]
    
    for s in test_stations:
        matcher.add_station(**s)
    
    print(f"Added {len(test_stations)} test stations")
    
    # 测试匹配
    # 在K0+200附近
    test_lat, test_lon = 31.2324, 121.4757
    
    result = matcher.match_station(test_lat, test_lon, max_distance=50)
    if result:
        print(f"Matched station: {result['station']}, distance: {result['distance']}m")
    else:
        print("No matching station found")
    
    # 测试查询附近
    nearby = matcher.query_nearby(test_lat, test_lon, radius=100)
    print(f"Found {len(nearby)} nearby stations")
    for n in nearby:
        print(f"  {n['station']}: {n['distance']}m")
