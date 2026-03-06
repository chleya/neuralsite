# -*- coding: utf-8 -*-
"""
GPS坐标提取工具

从照片EXIF中提取GPS坐标
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Optional, Tuple, Dict, Any
import math


class GeoExtractor:
    """GPS坐标提取器"""
    
    @staticmethod
    def extract_gps(image_path: str) -> Optional[Tuple[float, float]]:
        """
        从照片提取GPS坐标 (WGS84)
        
        Args:
            image_path: 照片文件路径
            
        Returns:
            (纬度, 经度) 或 None
        """
        try:
            image = Image.open(image_path)
            exif = image._getexif()
            
            if not exif:
                return None
            
            # 查找GPS信息
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'GPSInfo':
                    return GeoExtractor._parse_gps(value)
            
            return None
        except Exception as e:
            print(f"GPS extraction error: {e}")
            return None
    
    @staticmethod
    def _parse_gps(gps_info: dict) -> Optional[Tuple[float, float]]:
        """
        解析GPS原始数据
        
        Args:
            gps_info: GPS信息字典
            
        Returns:
            (纬度, 经度)
        """
        try:
            # GPS标签ID映射
            GPS_TAG = {
                'GPSLatitude': 1,
                'GPSLatitudeRef': 2,
                'GPSLongitude': 3,
                'GPSLongitudeRef': 4,
                'GPSAltitude': 6,
                'GPSAltitudeRef': 5,
            }
            
            # 提取经纬度
            lat = GeoExtractor._convert_to_degrees(gps_info.get(GPS_TAG['GPSLatitude']))
            lon = GeoExtractor._convert_to_degrees(gps_info.get(GPS_TAG['GPSLongitude']))
            
            if lat is None or lon is None:
                return None
            
            # 处理南纬/西经
            lat_ref = gps_info.get(GPS_TAG['GPSLatitudeRef'], 'N')
            lon_ref = gps_info.get(GPS_TAG['GPSLongitudeRef'], 'E')
            
            if lat_ref == 'S':
                lat = -lat
            if lon_ref == 'W':
                lon = -lon
            
            return (lat, lon)
        except Exception as e:
            print(f"GPS parse error: {e}")
            return None
    
    @staticmethod
    def _convert_to_degrees(value: Optional[tuple]) -> Optional[float]:
        """
        将GPS度分秒转换为十进制度
        
        Args:
            value: (度, 分, 秒) 元组
            
        Returns:
            十进制度
        """
        if not value:
            return None
        
        try:
            d, m, s = value
            return float(d) + float(m) / 60.0 + float(s) / 3600.0
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def extract_all_gps_data(image_path: str) -> Optional[Dict[str, Any]]:
        """
        提取完整的GPS数据
        
        Args:
            image_path: 照片文件路径
            
        Returns:
            包含所有GPS信息的字典
        """
        try:
            image = Image.open(image_path)
            exif = image._getexif()
            
            if not exif:
                return None
            
            # 查找GPS信息
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'GPSInfo':
                    return GeoExtractor._parse_all_gps(value)
            
            return None
        except Exception as e:
            print(f"GPS extraction error: {e}")
            return None
    
    @staticmethod
    def _parse_all_gps(gps_info: dict) -> Dict[str, Any]:
        """解析完整的GPS信息"""
        result = {}
        
        # GPS标签名称映射
        gps_tag_names = {
            1: 'GPSLatitude',
            2: 'GPSLatitudeRef', 
            3: 'GPSLongitude',
            4: 'GPSLongitudeRef',
            5: 'GPSAltitudeRef',
            6: 'GPSAltitude',
            7: 'GPSTimeStamp',
            8: 'GPSDateStamp',
            11: 'GPSImgDirection',
            12: 'GPSMapDatum',
        }
        
        for tag_id, value in gps_info.items():
            tag_name = gps_tag_names.get(tag_id, f'GPS_{tag_id}')
            
            # 转换经纬度
            if tag_name in ('GPSLatitude', 'GPSLongitude'):
                converted = GeoExtractor._convert_to_degrees(value)
                if converted:
                    result[tag_name] = converted
            else:
                result[tag_name] = str(value) if not isinstance(value, (int, float)) else value
        
        # 添加解析后的坐标
        if 'GPSLatitude' in result and 'GPSLongitude' in result:
            lat_ref = result.get('GPSLatitudeRef', 'N')
            lon_ref = result.get('GPSLongitudeRef', 'E')
            
            if lat_ref == 'S':
                result['GPSLatitude'] = -result['GPSLatitude']
            if lon_ref == 'W':
                result['GPSLongitude'] = -result['GPSLongitude']
            
            result['latitude'] = result['GPSLatitude']
            result['longitude'] = result['GPSLongitude']
        
        # 添加高程
        if 'GPSAltitude' in result:
            altitude_ref = result.get('GPSAltitudeRef', 0)
            if altitude_ref == 1:  #Below sea level
                result['GPSAltitude'] = -result['GPSAltitude']
            result['elevation'] = result['GPSAltitude']
        
        return result
    
    @staticmethod
    def wgs84_to_cgcs2000(lat: float, lon: float) -> Tuple[float, float]:
        """
        WGS84转CGCS2000 (简化转换)
        
        实际项目中应使用精确的七参数转换
        
        Args:
            lat: WGS84纬度
            lon: WGS84经度
            
        Returns:
            (CGCS2000 X, CGCS2000 Y)
        """
        # 简化转换: 对于中国中部区域，WGS84和CGCS2000差异较小
        # 精确转换需要七参数模型
        
        # 使用简单的平面投影近似
        # 这里假设项目在中部地区，使用3度带
        # 实际应使用pyproj进行精确转换
        
        # 返回原始WGS84坐标 (项目可能直接使用WGS84)
        return (lon, lat)
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        计算两点之间的距离 (米)
        
        使用Haversine公式
        
        Args:
            lat1, lon1: 第一点坐标
            lat2, lon2: 第二点坐标
            
        Returns:
            距离(米)
        """
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


# 测试
if __name__ == "__main__":
    # 创建测试图片的GPS信息测试
    extractor = GeoExtractor()
    
    # 测试距离计算
    dist = GeoExtractor.calculate_distance(
        31.2304, 121.4737,  # 上海
        31.2304, 121.4837  # 东方约1km
    )
    print(f"Distance: {dist:.2f} meters")
    
    # 测试WGS84到CGCS2000转换
    x, y = GeoExtractor.wgs84_to_cgcs2000(31.2304, 121.4737)
    print(f"CGCS2000: ({x}, {y})")
