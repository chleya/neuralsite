# -*- coding: utf-8 -*-
"""
格式标准定义

包含：桩号、坐标、时间、文件格式标准
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class StationFormat:
    """桩号格式标准"""
    
    # 标准格式: K5+800.000 或 K5+0800
    STATION_PATTERN = re.compile(r'^(K|ZK|YK)?(\d+)\+(\d{1,3})$')
    
    @classmethod
    def parse(cls, station_str: str) -> float:
        """
        解析桩号字符串为数值
        
        Args:
            station_str: 桩号字符串，如 "K5+800" 或 "K5+800.000"
            
        Returns:
            桩号数值，如 5800.0
        """
        station_str = station_str.strip().upper()
        
        # 匹配格式
        match = cls.STATION_PATTERN.match(station_str)
        if not match:
            raise ValueError(f"Invalid station format: {station_str}")
        
        prefix = match.group(1) or "K"  # 前缀
        km = int(match.group(2))  # 公里数
        offset = int(match.group(3))  # 米数
        
        return float(km * 1000 + offset)
    
    @classmethod
    def format(cls, station_num: float, prefix: str = "K") -> str:
        """
        将数值格式化为桩号字符串
        
        Args:
            station_num: 桩号数值
            prefix: 前缀
            
        Returns:
            桩号字符串，如 "K5+800"
        """
        km = int(station_num // 1000)
        offset = int(station_num % 1000)
        return f"{prefix}{km}+{offset:03d}"
    
    @classmethod
    def validate(cls, station_str: str) -> bool:
        """验证桩号格式是否合法"""
        try:
            cls.parse(station_str)
            return True
        except ValueError:
            return False


@dataclass
class CoordinateFormat:
    """坐标格式标准"""
    
    # 支持的坐标系
    COORDINATE_SYSTEMS = {
        "WGS84": "EPSG:4326",
        "CGCS2000": "EPSG:4490",
        "XIAN80": "EPSG:4618",
        "WGS84_UTM": "EPSG:32650",
    }
    
    @classmethod
    def validate(cls, easting: float, northing: float, 
                 elevation: Optional[float], 
                 system: str = "CGCS2000") -> bool:
        """
        验证坐标是否在合理范围内
        
        Args:
            easting: 东坐标
            northing: 北坐标  
            elevation: 高程
            system: 坐标系
        """
        # 中国区域大致范围检查
        if system == "CGCS2000":
            return (7000000 <= easting <= 8000000 and 
                    1500000 <= northing <= 5500000)
        elif system == "WGS84":
            return (73 <= easting <= 136 and 
                    18 <= northing <= 54)
        return True


@dataclass
class TimeFormat:
    """时间格式标准"""
    
    # ISO 8601格式
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    
    @classmethod
    def to_iso(cls, dt) -> str:
        """转换为ISO 8601格式"""
        return dt.strftime(cls.ISO_FORMAT)
    
    @classmethod
    def from_iso(cls, iso_str: str):
        """从ISO 8601格式解析"""
        from datetime import datetime
        return datetime.strptime(iso_str, cls.ISO_FORMAT)


@dataclass  
class FileFormat:
    """文件格式标准"""
    
    # 支持的文件类型
    SUPPORTED_IMAGE = ["jpg", "jpeg", "png"]
    SUPPORTED_VIDEO = ["mp4"]
    SUPPORTED_DRAWING = ["dwg", "dxf", "pdf"]
    
    # 文件大小限制 (MB)
    MAX_IMAGE_SIZE = 50
    MAX_VIDEO_SIZE = 500
    MAX_DRAWING_SIZE = 100
    
    @classmethod
    def get_file_type(cls, filename: str) -> str:
        """获取文件类型"""
        ext = filename.lower().split('.')[-1]
        
        if ext in cls.SUPPORTED_IMAGE:
            return "image"
        elif ext in cls.SUPPORTED_VIDEO:
            return "video"
        elif ext in cls.SUPPORTED_DRAWING:
            return "drawing"
        else:
            return "unknown"
    
    @classmethod
    def validate(cls, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        验证文件格式和大小
        
        Returns:
            (是否合法, 错误信息)
        """
        file_type = cls.get_file_type(filename)
        
        if file_type == "unknown":
            return False, f"Unsupported file type: {filename}"
        
        # 大小检查
        size_mb = file_size / (1024 * 1024)
        if file_type == "image" and size_mb > cls.MAX_IMAGE_SIZE:
            return False, f"Image too large: {size_mb:.1f}MB > {cls.MAX_IMAGE_SIZE}MB"
        elif file_type == "video" and size_mb > cls.MAX_VIDEO_SIZE:
            return False, f"Video too large: {size_mb:.1f}MB > {cls.MAX_VIDEO_SIZE}MB"
            
        return True, ""
