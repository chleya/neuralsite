# -*- coding: utf-8 -*-
"""
Level of Detail (LOD) Module
多级细节层次模块

根据视口范围自动选择细节级别
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod


class LODLevel(Enum):
    """LOD 级别"""
    LOD0 = 0  # 最详细 (原始精度)
    LOD1 = 1  # 高精度
    LOD2 = 2  # 中精度
    LOD3 = 3  # 低精度
    LOD4 = 4  # 最低精度 (仅显示关键点)


@dataclass
class LODConfig:
    """LOD 配置"""
    level: LODLevel
    max_error: float          # 最大误差(m)
    min_distance: float       # 最小视距(m)
    point_spacing: float     # 点间距(m)
    show_markers: bool = True      # 显示标记点
    show_labels: bool = True       # 显示标签
    curve_segments: int = 32      # 曲线分段数


# 默认 LOD 配置
LOD_CONFIGS = {
    LODLevel.LOD0: LODConfig(
        level=LODLevel.LOD0,
        max_error=0.0001,    # 0.1mm
        min_distance=0,
        point_spacing=1,     # 1m
        show_markers=True,
        show_labels=True,
        curve_segments=128
    ),
    LODLevel.LOD1: LODConfig(
        level=LODLevel.LOD1,
        max_error=0.001,     # 1mm
        min_distance=100,
        point_spacing=5,     # 5m
        show_markers=True,
        show_labels=True,
        curve_segments=64
    ),
    LODLevel.LOD2: LODConfig(
        level=LODLevel.LOD2,
        max_error=0.01,     # 1cm
        min_distance=500,
        point_spacing=10,    # 10m
        show_markers=False,
        show_labels=True,
        curve_segments=32
    ),
    LODLevel.LOD3: LODConfig(
        level=LODLevel.LOD3,
        max_error=0.1,      # 10cm
        min_distance=2000,
        point_spacing=50,    # 50m
        show_markers=False,
        show_labels=False,
        curve_segments=16
    ),
    LODLevel.LOD4: LODConfig(
        level=LODLevel.LOD4,
        max_error=1.0,      # 1m
        min_distance=5000,
        point_spacing=100,   # 100m
        show_markers=False,
        show_labels=False,
        curve_segments=8
    ),
}


@dataclass
class Viewport:
    """视口"""
    center_x: float
    center_y: float
    width: float      # 宽度(m)
    height: float     # 高度(m)
    rotation: float = 0  # 旋转角度(度)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.center_x, self.center_y)
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def contains_point(self, x: float, y: float) -> bool:
        """判断视口是否包含点"""
        half_w = self.width / 2
        half_h = self.height / 2
        
        dx = abs(x - self.center_x)
        dy = abs(y - self.center_y)
        
        return dx <= half_w and dy <= half_h
    
    def distance_to(self, x: float, y: float) -> float:
        """到视口中心的距离"""
        return math.sqrt((x - self.center_x)**2 + (y - self.center_y)**2)


class LODGenerator(ABC):
    """LOD 生成器基类"""
    
    @abstractmethod
    def generate(self, level: LODLevel, params: Dict) -> Any:
        """生成指定级别的数据"""
        pass


class ChainageLODGenerator(LODGenerator):
    """桩号线 LOD 生成器
    
    根据视口生成不同精度的桩号线数据
    """
    
    def __init__(self, transformer = None):
        self.transformer = transformer
    
    def generate(self, level: LODLevel, params: Dict) -> List[Dict]:
        """生成桩号线点数据
        
        Args:
            level: LOD 级别
            params: {
                start: 起始桩号,
                end: 结束桩号,
                transformer: 坐标转换器
            }
        """
        config = LOD_CONFIGS.get(level, LOD_CONFIGS[LODLevel.LOD2])
        
        start = params.get('start', 0)
        end = params.get('end', 1000)
        transformer = params.get('transformer', self.transformer)
        
        if transformer is None:
            return self._generate_linear(start, end, config.point_spacing)
        
        return self._generate_with_transform(start, end, config, transformer)
    
    def _generate_linear(self, start: float, end: float, 
                         spacing: float) -> List[Dict]:
        """线性生成 (无坐标转换)"""
        points = []
        chainage = start
        
        while chainage <= end:
            points.append({
                "chainage": chainage,
                "x": chainage,
                "y": 0,
                "z": 0
            })
            chainage += spacing
        
        # 确保终点
        if points[-1]["chainage"] != end:
            points.append({
                "chainage": end,
                "x": end,
                "y": 0,
                "z": 0
            })
        
        return points
    
    def _generate_with_transform(self, start: float, end: float,
                                  config: LODConfig,
                                  transformer) -> List[Dict]:
        """使用坐标转换器生成"""
        points = []
        chainage = start
        
        while chainage <= end:
            try:
                x, y, z = transformer.get_full_coordinate(chainage)
                points.append({
                    "chainage": chainage,
                    "x": x,
                    "y": y,
                    "z": z
                })
            except:
                # 降级到线性
                points.append({
                    "chainage": chainage,
                    "x": chainage,
                    "y": 0,
                    "z": 0
                })
            
            chainage += config.point_spacing
        
        # 确保终点
        try:
            x, y, z = transformer.get_full_coordinate(end)
            if points[-1]["chainage"] != end:
                points.append({
                    "chainage": end,
                    "x": x,
                    "y": y,
                    "z": z
                })
        except:
            pass
        
        return points


class CurveLODGenerator(LODGenerator):
    """曲线 LOD 生成器
    
    根据曲线类型和精度要求生成点数据
    """
    
    def __init__(self, curve_elements: List = None):
        self.curve_elements = curve_elements or []
    
    def generate(self, level: LODLevel, params: Dict) -> List[Dict]:
        """生成曲线点数据
        
        Args:
            level: LOD 级别
            params: {
                elements: 曲线元素列表,
                segments: 分段数 (可选)
            }
        """
        config = LOD_CONFIGS.get(level, LOD_CONFIGS[LODLevel.LOD2])
        elements = params.get('elements', self.curve_elements)
        
        if not elements:
            return []
        
        # 根据曲线分段数计算步长
        total_length = 0
        for elem in elements:
            total_length += elem.length if hasattr(elem, 'length') else 0
        
        points_per_element = config.curve_segments
        points = []
        
        for elem in elements:
            elem_points = self._generate_element_points(elem, points_per_element)
            points.extend(elem_points)
        
        return points
    
    def _generate_element_points(self, element, num_points: int) -> List[Dict]:
        """生成单个曲线元素的点"""
        points = []
        
        start = element.start_station if hasattr(element, 'start_station') else 0
        end = element.end_station if hasattr(element, 'end_station') else start + 1
        
        step = (end - start) / num_points
        
        for i in range(num_points + 1):
            chainage = start + i * step
            
            try:
                if hasattr(element, 'get_coordinate'):
                    result = element.get_coordinate(chainage)
                    if isinstance(result, tuple):
                        x, y = result[0], result[1]
                        azimuth = result[2] if len(result) > 2 else 0
                    else:
                        x, y, azimuth = chainage, 0, 0
                else:
                    x, y = chainage, 0
                    azimuth = 0
                
                points.append({
                    "chainage": chainage,
                    "x": x,
                    "y": y,
                    "azimuth": azimuth
                })
            except:
                points.append({
                    "chainage": chainage,
                    "x": chainage,
                    "y": 0,
                    "azimuth": 0
                })
        
        return points


class ViewportLODSelector:
    """视口 LOD 选择器
    
    根据视口参数自动选择最佳 LOD 级别
    """
    
    def __init__(self, configs: Dict[LODLevel, LODConfig] = None):
        self.configs = configs or LOD_CONFIGS
    
    def select(self, viewport: Viewport) -> LODLevel:
        """根据视口选择 LOD 级别
        
        Args:
            viewport: 视口
            
        Returns:
            最佳的 LOD 级别
        """
        # 计算视口对角线长度 (近似视距)
        viewport_diagonal = math.sqrt(viewport.width**2 + viewport.height**2)
        
        # 根据视距选择 LOD
        for level in sorted(LODLevel, key=lambda x: x.value, reverse=True):
            config = self.configs.get(level)
            if config and viewport_diagonal >= config.min_distance:
                return level
        
        return LODLevel.LOD0
    
    def get_config(self, level: LODLevel) -> LODConfig:
        """获取 LOD 配置"""
        return self.configs.get(level, LOD_CONFIGS[LODLevel.LOD2])


class LODManager:
    """LOD 管理器
    
    统一管理多级细节层次
    """
    
    def __init__(self):
        self.selector = ViewportLODSelector()
        self.chainage_generator = ChainageLODGenerator()
        self.curve_generator = CurveLODGenerator()
        
        # 缓存
        self._cache: Dict[Tuple[LODLevel, str], Any] = {}
        self._cache_enabled = True
    
    def set_transformer(self, transformer):
        """设置坐标转换器"""
        self.chainage_generator = ChainageLODGenerator(transformer)
    
    def set_curve_elements(self, elements: List):
        """设置曲线元素"""
        self.curve_generator = CurveLODGenerator(elements)
    
    def get_points(self, viewport: Viewport, 
                   start: float, end: float) -> Tuple[LODLevel, List[Dict]]:
        """获取视口范围内的点数据
        
        Args:
            viewport: 视口
            start: 起始桩号
            end: 结束桩号
            
        Returns:
            (选择的LOD级别, 点数据列表)
        """
        # 选择 LOD 级别
        level = self.selector.select(viewport)
        config = self.selector.get_config(level)
        
        # 检查缓存
        cache_key = (level, f"{start}_{end}")
        if self._cache_enabled and cache_key in self._cache:
            return level, self._cache[cache_key]
        
        # 生成点数据
        params = {
            'start': start,
            'end': end,
            'transformer': self.chainage_generator.transformer
        }
        
        points = self.chainage_generator.generate(level, params)
        
        # 过滤视口外的点
        visible_points = [
            p for p in points
            if viewport.contains_point(p['x'], p['y'])
        ]
        
        # 缓存
        if self._cache_enabled:
            self._cache[cache_key] = visible_points
        
        return level, visible_points
    
    def get_multilevel_points(self, viewport: Viewport,
                              start: float, end: float,
                              levels: List[LODLevel] = None) -> Dict[LODLevel, List[Dict]]:
        """获取多级点数据 (用于平滑过渡)
        
        Args:
            viewport: 视口
            start: 起始桩号
            end: 结束桩号
            levels: 需要生成的级别列表
            
        Returns:
            {LODLevel: 点数据}
        """
        if levels is None:
            levels = list(LODLevel)
        
        result = {}
        
        for level in levels:
            config = self.selector.get_config(level)
            params = {
                'start': start,
                'end': end,
                'transformer': self.chainage_generator.transformer
            }
            points = self.chainage_generator.generate(level, params)
            
            # 过滤视口内
            visible = [p for p in points if viewport.contains_point(p['x'], p['y'])]
            result[level] = visible
        
        return result
    
    def invalidate_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def enable_cache(self, enabled: bool) -> None:
        """启用/禁用缓存"""
        self._cache_enabled = enabled


class LODVisualizationHelper:
    """LOD 可视化辅助工具"""
    
    @staticmethod
    def get_display_info(level: LODLevel) -> Dict:
        """获取 LOD 显示信息"""
        config = LOD_CONFIGS.get(level)
        
        return {
            "level": level.name,
            "level_value": level.value,
            "point_spacing": config.point_spacing if config else 0,
            "max_error": config.max_error if config else 0,
            "segments": config.curve_segments if config else 0,
            "show_labels": config.show_labels if config else False
        }
    
    @staticmethod
    def format_point_count(points: List[Dict], level: LODLevel) -> str:
        """格式化点数量信息"""
        count = len(points)
        config = LOD_CONFIGS.get(level)
        
        if config:
            spacing = config.point_spacing
            return f"{count} points (spacing: {spacing}m)"
        return f"{count} points"


# 测试
if __name__ == "__main__":
    # 测试 LOD 选择器
    print("=== LOD Selection Test ===\n")
    
    selector = ViewportLODSelector()
    
    # 模拟不同视口
    test_viewports = [
        Viewport(500000, 3000000, 100, 100),       # 很小视口
        Viewport(500000, 3000000, 500, 500),       # 中等视口
        Viewport(500000, 3000000, 2000, 2000),     # 大视口
        Viewport(500000, 3000000, 10000, 10000),   # 很大视口
    ]
    
    for vp in test_viewports:
        level = selector.select(vp)
        config = selector.get_config(level)
        print(f"Viewport: {vp.width}m x {vp.height}m -> LOD: {level.name}")
        print(f"  Point spacing: {config.point_spacing}m, Segments: {config.curve_segments}")
    
    # 测试 LOD 管理器
    print("\n=== LOD Manager Test ===\n")
    
    manager = LODManager()
    
    viewport = Viewport(500250, 3000250, 500, 500)
    level, points = manager.get_points(viewport, 0, 2000)
    
    print(f"Selected LOD: {level.name}")
    print(f"Visible points: {len(points)}")
    
    if points:
        print(f"First point: {points[0]}")
        print(f"Last point: {points[-1]}")
    
    # 多级测试
    print("\n=== Multi-Level Test ===")
    
    multi = manager.get_multilevel_points(viewport, 0, 2000)
    for lvl, pts in multi.items():
        info = LODVisualizationHelper.get_display_info(lvl)
        print(f"{lvl.name}: {len(pts)} points")
