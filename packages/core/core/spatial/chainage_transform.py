# -*- coding: utf-8 -*-
"""
Chainage Coordinate Transform Module
桩号 ↔ 坐标 双向转换模块

支持平/竖/横曲线联合计算
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

# 尝试导入 geometry 模块
try:
    from geometry import (
        HorizontalAlignment, LineElement, CircularCurveElement, SpiralCurveElement,
        VerticalAlignment, VerticalCurveElement,
        CrossSectionCalculator, CrossSectionTemplate
    )
    GEOMETRY_AVAILABLE = True
except ImportError:
    GEOMETRY_AVAILABLE = False
    # 定义简单的类型别名以避免运行时错误
    HorizontalAlignment = None
    VerticalAlignment = None
    CrossSectionCalculator = None
    CrossSectionTemplate = None


@dataclass
class ChainagePoint:
    """桩号点"""
    chainage: float          # 桩号(m)
    x: float                  # X坐标
    y: float                  # Y坐标
    z: float = 0.0            # 高程
    azimuth: float = 0        # 方位角(度)
    radius: float = 0         # 曲率半径(无限大为直线)
    
    def to_dict(self) -> Dict:
        return {
            "chainage": self.chainage,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "azimuth": self.azimuth,
            "radius": self.radius
        }


@dataclass
class OffsetPoint:
    """偏移点 (中桩到边桩的转换)"""
    chainage: float           # 桩号
    offset: float             # 横向偏移(左负右正)
    x: float                  # X坐标
    y: float                  # Y坐标
    z: float                  # 高程


class ChainageTransformer:
    """桩号坐标转换器
    
    支持：
    - 桩号 → 坐标 (平面 + 高程)
    - 坐标 → 桩号 (反算)
    - 边桩计算
    - 精度验证 (毫米级)
    """
    
    TOLERANCE_MM = 0.001  # 毫米级精度
    
    def __init__(self):
        self.horizontal: Optional[HorizontalAlignment] = None
        self.vertical: Optional[VerticalAlignment] = None
        self.cross_section: Optional[CrossSectionCalculator] = None
        
        # 缓存
        self._point_cache: Dict[float, ChainagePoint] = {}
        self._inverse_cache: Dict[Tuple[int, int, int], float] = {}  # (x,y,z) -> chainage
    
    def set_horizontal(self, alignment: HorizontalAlignment) -> None:
        """设置平曲线"""
        self.horizontal = alignment
        self._clear_cache()
    
    def set_vertical(self, alignment: VerticalAlignment) -> None:
        """设置竖曲线"""
        self.vertical = alignment
        self._clear_cache()
    
    def set_cross_section(self, calculator: CrossSectionCalculator) -> None:
        """设置横断面计算器"""
        self.cross_section = calculator
    
    def _clear_cache(self) -> None:
        """清空缓存"""
        self._point_cache.clear()
        self._inverse_cache.clear()
    
    def chainage_to_coordinate(self, chainage: float) -> ChainagePoint:
        """桩号转坐标 (平面)
        
        Args:
            chainage: 桩号(m)
            
        Returns:
            ChainagePoint
        """
        # 尝试从缓存获取
        if chainage in self._point_cache:
            return self._point_cache[chainage]
        
        if self.horizontal is None:
            # 无平曲线，返回默认值
            point = ChainagePoint(
                chainage=chainage,
                x=chainage,
                y=0,
                azimuth=0
            )
            self._point_cache[chainage] = point
            return point
        
        # 获取平面坐标
        x, y, azimuth = self.horizontal.get_coordinate(chainage)
        
        # 计算曲率半径
        radius = self._calculate_radius(chainage)
        
        point = ChainagePoint(
            chainage=chainage,
            x=x,
            y=y,
            z=0,  # 高程单独处理
            azimuth=azimuth,
            radius=radius
        )
        
        self._point_cache[chainage] = point
        return point
    
    def get_full_coordinate(self, chainage: float) -> Tuple[float, float, float]:
        """获取完整坐标 (平面 + 高程)
        
        Args:
            chainage: 桩号(m)
            
        Returns:
            (x, y, z)
        """
        point = self.chainage_to_coordinate(chainage)
        
        # 获取高程
        z = 0
        if self.vertical is not None:
            z = self.vertical.get_elevation(chainage)
        
        return point.x, point.y, z
    
    def _calculate_radius(self, chainage: float) -> float:
        """计算指定桩号的曲率半径"""
        if self.horizontal is None:
            return float('inf')
        
        # 查找所在线元
        for elem in self.horizontal.elements:
            if elem.start_station <= chainage <= elem.end_station:
                if isinstance(elem, CircularCurveElement):
                    return elem.radius
                elif isinstance(elem, SpiralCurveElement):
                    # 缓和曲线半径渐变
                    l = chainage - elem.start_station
                    if elem.A > 0 and elem.radius:
                        r = elem.radius * elem.length / (l + elem.radius * elem.length / elem.A) if elem.A else float('inf')
                        return r if r > 0 else float('inf')
                # 直线段
                return float('inf')
        
        return float('inf')
    
    def coordinate_to_chainage(self, x: float, y: float, 
                               tolerance: float = None) -> Optional[float]:
        """坐标转桩号 (反算)
        
        使用二分搜索 + 距离最小化
        精度: 毫米级
        
        Args:
            x: X坐标
            y: Y坐标
            tolerance: 收敛 tolerance (m), 默认 0.001m (1mm)
            
        Returns:
            桩号(m) 或 None
        """
        tolerance = tolerance or self.TOLERANCE_MM
        
        if self.horizontal is None:
            return x  # 简化：返回 x 作为桩号
        
        # 检查缓存
        cache_key = (int(x * 1000), int(y * 1000), int(tolerance * 1000))
        if cache_key in self._inverse_cache:
            return self._inverse_cache[cache_key]
        
        # 确定搜索范围
        start = self.horizontal.start_station
        end = self.horizontal.end_station
        
        # 二分搜索
        chainage = self._binary_search_chainage(x, y, start, end, tolerance)
        
        if chainage is not None:
            self._inverse_cache[cache_key] = chainage
        
        return chainage
    
    def _binary_search_chainage(self, x: float, y: float, 
                                start: float, end: float,
                                tolerance: float) -> Optional[float]:
        """二分搜索求解桩号"""
        left = start
        right = end
        best_chainage = None
        best_distance = float('inf')
        
        # 迭代直到收敛
        for _ in range(100):  # 最多100次迭代
            if right - left < tolerance:
                break
            
            # 采样点
            mid = (left + right) / 2
            point = self.chainage_to_coordinate(mid)
            
            # 计算距离
            dx = point.x - x
            dy = point.y - y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < best_distance:
                best_distance = distance
                best_chainage = mid
            
            # 确定搜索方向
            # 通过比较前后点的距离来决定方向
            step = (right - left) / 10
            if step < tolerance:
                break
                
            left_point = self.chainage_to_coordinate(mid - step)
            right_point = self.chainage_to_coordinate(mid + step)
            
            left_dist = math.sqrt((left_point.x - x)**2 + (left_point.y - y)**2)
            right_dist = math.sqrt((right_point.x - x)**2 + (right_point.y - y)**2)
            
            if left_dist < right_dist:
                right = mid
            else:
                left = mid
        
        return best_chainage
    
    def get_offset_point(self, chainage: float, offset: float) -> OffsetPoint:
        """计算边桩坐标
        
        Args:
            chainage: 桩号(m)
            offset: 横向偏移(左负右正)
            
        Returns:
            OffsetPoint
        """
        # 获取中桩信息
        center = self.chainage_to_coordinate(chainage)
        
        # 获取高程
        z = center.z
        if self.vertical is not None:
            z = self.vertical.get_elevation(chainage)
        
        # 横断面计算
        if self.cross_section is not None:
            z = self.cross_section.calculate(
                chainage, offset
            ).get('center_z', z)
        
        # 计算边桩坐标
        azimuth_rad = math.radians(center.azimuth)
        
        # 左偏移: azimuth + 90度, 右偏移: azimuth - 90度
        if offset < 0:
            angle = azimuth_rad + math.pi / 2
        else:
            angle = azimuth_rad - math.pi / 2
        
        x = center.x + abs(offset) * math.cos(angle)
        y = center.y + abs(offset) * math.sin(angle)
        
        return OffsetPoint(
            chainage=chainage,
            offset=offset,
            x=x,
            y=y,
            z=z
        )
    
    def validate_accuracy(self, test_cases: List[Tuple[float, float, float]]) -> Dict:
        """精度验证
        
        Args:
            test_cases: [(chainage, expected_x, expected_y), ...]
            
        Returns:
            验证结果
        """
        errors = []
        
        for chainage, expected_x, expected_y in test_cases:
            point = self.chainage_to_coordinate(chainage)
            
            dx = point.x - expected_x
            dy = point.y - expected_y
            error = math.sqrt(dx * dx + dy * dy)
            
            errors.append({
                "chainage": chainage,
                "expected": (expected_x, expected_y),
                "actual": (point.x, point.y),
                "error_mm": error * 1000  # 转换为毫米
            })
        
        max_error = max(e["error_mm"] for e in errors)
        avg_error = sum(e["error_mm"] for e in errors) / len(errors)
        
        return {
            "test_cases": errors,
            "max_error_mm": max_error,
            "avg_error_mm": avg_error,
            "passed": max_error < 1.0  # 小于1mm为通过
        }


class CombinedCurveCalculator:
    """平竖横曲线联合计算器"""
    
    def __init__(self):
        self.transformer = ChainageTransformer()
        self._templates: Dict[str, CrossSectionTemplate] = {}
    
    def set_horizontal(self, elements: List) -> 'CombinedCurveCalculator':
        """设置平曲线"""
        alignment = HorizontalAlignment()
        for elem in elements:
            alignment.add_element(elem)
        self.transformer.set_horizontal(alignment)
        return self
    
    def set_vertical(self, elements: List) -> 'CombinedCurveCalculator':
        """设置竖曲线"""
        alignment = VerticalAlignment()
        for elem in elements:
            alignment.add_element(elem)
        self.transformer.set_vertical(alignment)
        return self
    
    def set_cross_section_template(self, name: str, 
                                    template: CrossSectionTemplate) -> 'CombinedCurveCalculator':
        """设置横断面模板"""
        self._templates[name] = template
        return self
    
    def use_cross_section(self, template_name: str = "default") -> 'CombinedCurveCalculator':
        """启用横断面计算"""
        template = self._templates.get(template_name, CrossSectionTemplate())
        calc = CrossSectionCalculator(template)
        self.transformer.set_cross_section(calc)
        return self
    
    def get_centerline_point(self, chainage: float) -> Dict:
        """获取中桩点"""
        x, y, z = self.transformer.get_full_coordinate(chainage)
        point = self.transformer.chainage_to_coordinate(chainage)
        
        return {
            "chainage": chainage,
            "x": x,
            "y": y,
            "z": z,
            "azimuth": point.azimuth,
            "radius": point.radius
        }
    
    def get_stake_point(self, chainage: float, offset: float) -> Dict:
        """获取边桩点
        
        Args:
            chainage: 桩号
            offset: 横向偏移
        """
        point = self.transformer.get_offset_point(chainage, offset)
        
        return {
            "chainage": point.chainage,
            "offset": point.offset,
            "x": point.x,
            "y": point.y,
            "z": point.z
        }
    
    def get_section_points(self, chainage: float, 
                           offsets: List[float] = None) -> List[Dict]:
        """获取断面多点
        
        Args:
            chainage: 桩号
            offsets: 偏移列表, 默认 [-10, -5, 0, 5, 10]
        """
        if offsets is None:
            offsets = [-10, -5, 0, 5, 10]
        
        return [
            self.get_stake_point(chainage, offset)
            for offset in offsets
        ]


# 测试
if __name__ == "__main__":
    from geometry import (
        HorizontalAlignment, LineElement, CircularCurveElement, SpiralCurveElement,
        VerticalAlignment, VerticalCurveElement
    )
    
    # 创建平曲线
    h = HorizontalAlignment()
    h.add_element(LineElement(0, 500, 45, 500000, 3000000))
    h.add_element(SpiralCurveElement(500, 600, 45, 500353.553, 3000353.553, 300, 800, "右"))
    h.add_element(CircularCurveElement(600, 1200, 800, 45, 500424.264, 3000424.264,
                                        500424.264, 3000224.264, "右"))
    h.add_element(LineElement(1200, 2000, 90, 500707.106, 3000707.106))
    
    # 创建竖曲线
    v = VerticalAlignment()
    v.add_element(VerticalCurveElement(0, 100.0, grade_out=20))
    v.add_element(VerticalCurveElement(500, 110.0, grade_in=20, grade_out=-15, length=200))
    v.add_element(VerticalCurveElement(1200, 99.5, grade_in=-15, grade_out=10, length=150))
    v.add_element(VerticalCurveElement(2000, 108.0, grade_in=10))
    
    # 创建联合计算器
    calculator = CombinedCurveCalculator()
    calculator.set_horizontal(h.elements)
    calculator.set_vertical(v.elements)
    
    print("=== Chainage Transform Test ===")
    
    # 测试桩号 -> 坐标
    print("\n1. Chainage -> Coordinate:")
    for chainage in [0, 250, 500, 600, 800, 1000, 1200, 1500, 2000]:
        point = calculator.get_centerline_point(chainage)
        print(f"K{chainage//1000}+{chainage%1000:03d}: "
              f"X={point['x']:.3f} Y={point['y']:.3f} Z={point['z']:.3f} "
              f"Az={point['azimuth']:.2f}°")
    
    # 测试边桩
    print("\n2. Stake Points at K0+500:")
    for offset in [-10, -5, 0, 5, 10]:
        stake = calculator.get_stake_point(500, offset)
        print(f"  Offset {offset:+}m: X={stake['x']:.3f} Y={stake['y']:.3f} Z={stake['z']:.3f}")
    
    # 测试反算
    print("\n3. Coordinate -> Chainage (Inverse):")
    test_points = [
        (500000, 3000000),
        (500424.264, 3000424.264),
        (500707.106, 3000707.106),
    ]
    
    for x, y in test_points:
        chainage = calculator.transformer.coordinate_to_chainage(x, y)
        if chainage:
            print(f"  ({x}, {y}) -> K{chainage//1000}+{chainage%1000:.3f}")
