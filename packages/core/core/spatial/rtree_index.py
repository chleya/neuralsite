# -*- coding: utf-8 -*-
"""
R-Tree Spatial Index Module
R-Tree 空间索引 - 高效的空间查询
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class Box:
    """Axis-Aligned Bounding Box (AABB)"""
    
    def __init__(self, min_x: float, min_y: float, max_x: float, max_y: float):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
    
    def __repr__(self):
        return f"Box({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y})"
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
    
    def area(self) -> float:
        """面积"""
        return (self.max_x - self.min_x) * (self.max_y - self.min_y)
    
    def perimeter(self) -> float:
        """周长"""
        return 2 * (self.max_x - self.min_x + self.max_y - self.min_y)
    
    def expand(self, other: 'Box') -> 'Box':
        """合并两个Box"""
        return Box(
            min(self.min_x, other.min_x),
            min(self.min_y, other.min_y),
            max(self.max_x, other.max_x),
            max(self.max_y, other.max_y)
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """判断是否包含点"""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y
    
    def contains_box(self, other: 'Box') -> bool:
        """判断是否包含另一个Box"""
        return (self.min_x <= other.min_x and self.min_y <= other.min_y and
                self.max_x >= other.max_x and self.max_y >= other.max_y)
    
    def intersects(self, other: 'Box') -> bool:
        """判断是否相交"""
        return not (self.max_x < other.min_x or self.min_x > other.max_x or
                    self.max_y < other.min_y or self.min_y > other.max_y)
    
    def distance_to_point(self, x: float, y: float) -> float:
        """到点的最小距离"""
        if self.contains_point(x, y):
            return 0
        
        dx = max(self.min_x - x, 0, x - self.max_x)
        dy = max(self.min_y - y, 0, y - self.max_y)
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class SpatialItem:
    """空间数据项"""
    x: float
    y: float
    data: Any
    
    @property
    def box(self) -> Box:
        return Box(self.x, self.y, self.x, self.y)


class RTree:
    """R-Tree 空间索引 (简化版)
    
    基于递归空间分区实现
    支持：
    - 点查询
    - 范围查询
    - 最近邻查询
    """
    
    MAX_ITEMS = 8  # 每个节点最大条目数
    
    def __init__(self, max_items: int = None):
        self.max_items = max_items or self.MAX_ITEMS
        self._items: List[SpatialItem] = []
        self._subtrees: List['RTree'] = []
        self._parent: Optional['RTree'] = None
        self._bounding_box = None
        self._is_leaf = True
    
    @property
    def size(self) -> int:
        return len(self._items) + sum(s.size for s in self._subtrees)
    
    def _update_bbox(self):
        """更新包围盒"""
        all_boxes = [item.box for item in self._items]
        all_boxes.extend(s._bounding_box for s in self._subtrees if s._bounding_box)
        
        if all_boxes:
            self._bounding_box = Box(
                min(b.min_x for b in all_boxes),
                min(b.min_y for b in all_boxes),
                max(b.max_x for b in all_boxes),
                max(b.max_y for b in all_boxes)
            )
        else:
            self._bounding_box = None
    
    def insert(self, x: float, y: float, data: Any) -> None:
        """插入空间数据
        
        Args:
            x: X坐标
            y: Y坐标
            data: 关联数据
        """
        item = SpatialItem(x, y, data)
        
        if self._is_leaf:
            self._items.append(item)
            self._update_bbox()
            
            if len(self._items) > self.max_items:
                self._split()
        else:
            # 插入到合适的子树
            self._insert_to_subtree(item)
    
    def _insert_to_subtree(self, item: SpatialItem) -> None:
        """插入到子树"""
        if not self._subtrees:
            self._convert_to_internal()
        
        # 找到最佳子树
        best_subtree = None
        best_enlargement = float('inf')
        
        for subtree in self._subtrees:
            if subtree._bounding_box:
                enlarged = subtree._bounding_box.expand(item.box).area()
                enlargement = enlarged - subtree._bounding_box.area()
                
                if enlargement < best_enlargement:
                    best_enlargement = enlargement
                    best_subtree = subtree
        
        if best_subtree is None:
            best_subtree = self._subtrees[0]
        
        best_subtree.insert(item.x, item.y, item.data)
        self._update_bbox()
    
    def _convert_to_internal(self):
        """转换为内部节点"""
        self._is_leaf = False
        
        # 将现有项目分配到子树
        if self._items:
            # 创建两个子树
            subtree1 = RTree(self.max_items)
            subtree2 = RTree(self.max_items)
            
            # 按 x 坐标排序
            sorted_items = sorted(self._items, key=lambda i: i.x)
            mid = len(sorted_items) // 2
            
            for item in sorted_items[:mid]:
                subtree1.insert(item.x, item.y, item.data)
            for item in sorted_items[mid:]:
                subtree2.insert(item.x, item.y, item.data)
            
            subtree1._parent = self
            subtree2._parent = self
            
            self._subtrees = [subtree1, subtree2]
            self._items = []
            
            self._update_bbox()
    
    def _split(self) -> None:
        """节点分裂"""
        self._convert_to_internal()
    
    def query_range(self, min_x: float, min_y: float, 
                    max_x: float, max_y: float) -> List[Any]:
        """范围查询
        
        Args:
            min_x, min_y: 最小坐标
            max_x, max_y: 最大坐标
            
        Returns:
            匹配的数据列表
        """
        query_box = Box(min_x, min_y, max_x, max_y)
        results = []
        self._query_range(query_box, results)
        return results
    
    def _query_range(self, query_box: Box, results: List) -> None:
        """递归范围查询"""
        # 快速排除
        if self._bounding_box and not self._bounding_box.intersects(query_box):
            return
        
        # 叶子节点
        if self._is_leaf:
            for item in self._items:
                if query_box.contains_point(item.x, item.y):
                    results.append(item.data)
        else:
            # 递归子节点
            for subtree in self._subtrees:
                subtree._query_range(query_box, results)
    
    def query_nearest(self, x: float, y: float, count: int = 1) -> List[Tuple[Any, float]]:
        """最近邻查询
        
        Args:
            x: X坐标
            y: Y坐标
            count: 返回数量
            
        Returns:
            [(data, distance), ...] 按距离排序
        """
        # 收集所有候选
        candidates = []
        self._query_nearest(x, y, candidates)
        
        # 按距离排序
        candidates.sort(key=lambda item: item[1])
        
        return candidates[:count]
    
    def _query_nearest(self, x: float, y: float, 
                       candidates: List[Tuple[Any, float]]) -> None:
        """递归最近邻查询"""
        if self._is_leaf:
            for item in self._items:
                dist = math.sqrt((item.x - x)**2 + (item.y - y)**2)
                candidates.append((item.data, dist))
        else:
            # 按距离排序子节点
            subtree_dists = []
            for subtree in self._subtrees:
                if subtree._bounding_box:
                    dist = subtree._bounding_box.distance_to_point(x, y)
                    subtree_dists.append((subtree, dist))
            
            subtree_dists.sort(key=lambda item: item[1])
            
            for subtree, _ in subtree_dists:
                subtree._query_nearest(x, y, candidates)
    
    def query_circle(self, cx: float, cy: float, radius: float) -> List[Any]:
        """圆形范围查询
        
        Args:
            cx, cy: 圆心坐标
            radius: 半径
            
        Returns:
            匹配的数据列表
        """
        # 先用方形查询
        results = self.query_range(
            cx - radius, cy - radius,
            cx + radius, cy + radius
        )
        
        # 精确过滤
        final_results = []
        for item_data in results:
            if isinstance(item_data, tuple) and len(item_data) >= 2:
                # 尝试解析为坐标
                ix, iy = item_data[0], item_data[1]
                if isinstance(ix, (int, float)) and isinstance(iy, (int, float)):
                    dist = math.sqrt((ix - cx)**2 + (iy - cy)**2)
                    if dist <= radius:
                        final_results.append(item_data)
            elif hasattr(item_data, 'x') and hasattr(item_data, 'y'):
                # 如果是对象
                dist = math.sqrt((item_data.x - cx)**2 + (item_data.y - cy)**2)
                if dist <= radius:
                    final_results.append(item_data)
        
        return final_results
    
    def clear(self) -> None:
        """清空索引"""
        self._items = []
        self._subtrees = []
        self._bounding_box = None
        self._is_leaf = True


class ChainageRTree(RTree):
    """专门用于桩号索引的 R-Tree
    
    优化：同时索引空间位置和桩号
    """
    
    def __init__(self, max_items: int = None):
        super().__init__(max_items)
        self._chainage_index: Dict[float, List[Any]] = {}  # 桩号 -> 数据
    
    def insert_with_chainage(self, x: float, y: float, chainage: float, data: Any) -> None:
        """带桩号插入
        
        Args:
            x: X坐标
            y: Y坐标  
            chainage: 桩号(m)
            data: 关联数据
        """
        # 插入空间索引
        self.insert(x, y, data)
        
        # 插入桩号索引
        if chainage not in self._chainage_index:
            self._chainage_index[chainage] = []
        self._chainage_index[chainage].append(data)
    
    def query_by_chainage(self, start: float, end: float) -> List[Any]:
        """按桩号范围查询
        
        Args:
            start: 起始桩号(m)
            end: 结束桩号(m)
            
        Returns:
            匹配的数据列表
        """
        results = []
        
        for ch, data_list in self._chainage_index.items():
            if start <= ch <= end:
                results.extend(data_list)
        
        return results
    
    def find_nearest_by_chainage(self, target_chainage: float) -> Tuple[Any, float]:
        """查找最近桩号
        
        Args:
            target_chainage: 目标桩号
            
        Returns:
            (data, distance)
        """
        if not self._chainage_index:
            return None, float('inf')
        
        sorted_chainages = sorted(self._chainage_index.keys())
        
        # 二分查找
        left = 0
        right = len(sorted_chainages) - 1
        
        while left < right:
            mid = (left + right) // 2
            if sorted_chainages[mid] < target_chainage:
                left = mid + 1
            else:
                right = mid
        
        # 检查最近的两个
        candidates = []
        if left > 0:
            ch = sorted_chainages[left - 1]
            dist = abs(ch - target_chainage)
            for data in self._chainage_index[ch]:
                candidates.append((data, dist))
        
        if left < len(sorted_chainages):
            ch = sorted_chainages[left]
            dist = abs(ch - target_chainage)
            for data in self._chainage_index[ch]:
                candidates.append((data, dist))
        
        if not candidates:
            return None, float('inf')
        
        # 返回最近的
        candidates.sort(key=lambda x: x[1])
        return candidates[0]


# 测试
if __name__ == "__main__":
    # 测试 R-Tree
    tree = RTree()
    
    # 插入测试点
    test_points = [
        (500000, 3000000, "K0+000"),
        (500100, 3000100, "K0+100"),
        (500200, 3000200, "K0+200"),
        (500300, 3000300, "K0+300"),
        (500400, 3000400, "K0+400"),
    ]
    
    for x, y, name in test_points:
        tree.insert(x, y, name)
    
    print(f"Inserted {tree.size} points")
    
    # 范围查询
    results = tree.query_range(500100, 3000100, 500300, 3000300)
    print(f"\nRange query (500100-500300, 3000100-3000300):")
    for r in results:
        print(f"  {r}")
    
    # 最近邻查询
    nearest = tree.query_nearest(500150, 3000150, 2)
    print(f"\nNearest to (500150, 3000150):")
    for data, dist in nearest:
        print(f"  {data}: {dist:.2f}m")
