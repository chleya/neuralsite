# -*- coding: utf-8 -*-
"""
Spatial Module Unit Tests
空间模块单元测试
"""

import unittest
import math
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core'))

from spatial.rtree_index import (
    Box, RTree, SpatialItem, ChainageRTree
)
from spatial.lod import (
    LODLevel, LODConfig, Viewport, 
    ChainageLODGenerator, ViewportLODSelector,
    LODManager, LOD_CONFIGS
)


class TestBox(unittest.TestCase):
    """Box 测试"""
    
    def test_create(self):
        box = Box(0, 0, 10, 10)
        self.assertEqual(box.min_x, 0)
        self.assertEqual(box.max_x, 10)
        self.assertEqual(box.area(), 100)
    
    def test_contains_point(self):
        box = Box(0, 0, 10, 10)
        self.assertTrue(box.contains_point(5, 5))
        self.assertFalse(box.contains_point(15, 5))
    
    def test_intersects(self):
        box1 = Box(0, 0, 10, 10)
        box2 = Box(5, 5, 15, 15)
        box3 = Box(20, 20, 30, 30)
        
        self.assertTrue(box1.intersects(box2))
        self.assertFalse(box1.intersects(box3))
    
    def test_expand(self):
        box1 = Box(0, 0, 10, 10)
        box2 = Box(5, 5, 15, 15)
        
        expanded = box1.expand(box2)
        
        self.assertEqual(expanded.min_x, 0)
        self.assertEqual(expanded.min_y, 0)
        self.assertEqual(expanded.max_x, 15)
        self.assertEqual(expanded.max_y, 15)
    
    def test_distance_to_point(self):
        box = Box(0, 0, 10, 10)
        
        # 点在 Box 内
        self.assertEqual(box.distance_to_point(5, 5), 0)
        
        # 点在 Box 外
        self.assertAlmostEqual(box.distance_to_point(15, 5), 5)
        self.assertAlmostEqual(box.distance_to_point(5, 15), 5)
        self.assertAlmostEqual(box.distance_to_point(15, 15), math.sqrt(50))


class TestRTree(unittest.TestCase):
    """R-Tree 测试"""
    
    def setUp(self):
        self.tree = RTree(max_items=4)
        
        # 插入测试点
        self.test_points = [
            (500000, 3000000, "K0+000"),
            (500100, 3000100, "K0+100"),
            (500200, 3000200, "K0+200"),
            (500300, 3000300, "K0+300"),
            (500400, 3000400, "K0+400"),
        ]
        
        for x, y, name in self.test_points:
            self.tree.insert(x, y, name)
    
    def test_insert(self):
        self.assertEqual(self.tree.size, 5)
    
    def test_range_query(self):
        # 查询矩形范围
        results = self.tree.query_range(500100, 3000100, 500300, 3000300)
        
        self.assertGreaterEqual(len(results), 1)
    
    def test_nearest_query(self):
        nearest = self.tree.query_nearest(500150, 3000150, 2)
        
        self.assertEqual(len(nearest), 2)
        self.assertLessEqual(nearest[0][1], nearest[1][1])  # 距离递增
    
    def test_clear(self):
        self.tree.clear()
        self.assertEqual(self.tree.size, 0)


class TestChainageRTree(unittest.TestCase):
    """ChainageRTree 测试"""
    
    def setUp(self):
        self.tree = ChainageRTree()
        
        # 插入带桩号的数据
        self.test_data = [
            (500000, 3000000, 0, "K0+000"),
            (500100, 3000100, 100, "K0+100"),
            (500200, 3000200, 200, "K0+200"),
            (500300, 3000300, 300, "K0+300"),
            (500400, 3000400, 400, "K0+400"),
        ]
        
        for x, y, ch, name in self.test_data:
            self.tree.insert_with_chainage(x, y, ch, name)
    
    def test_chainage_query(self):
        results = self.tree.query_by_chainage(100, 300)
        
        self.assertGreaterEqual(len(results), 2)
    
    def test_find_nearest_by_chainage(self):
        data, dist = self.tree.find_nearest_by_chainage(150)
        
        self.assertIsNotNone(data)
        self.assertLessEqual(dist, 50)


class TestLOD(unittest.TestCase):
    """LOD 测试"""
    
    def test_lod_configs(self):
        """测试 LOD 配置"""
        self.assertEqual(len(LOD_CONFIGS), 5)
        
        for level in LODLevel:
            config = LOD_CONFIGS.get(level)
            self.assertIsNotNone(config)
            self.assertEqual(config.level, level)
    
    def test_viewport_contains(self):
        vp = Viewport(500, 500, 100, 100)
        
        self.assertTrue(vp.contains_point(500, 500))
        self.assertTrue(vp.contains_point(450, 550))
        self.assertFalse(vp.contains_point(600, 600))
    
    def test_viewport_distance(self):
        vp = Viewport(500, 500, 100, 100)
        
        self.assertEqual(vp.distance_to(500, 500), 0)
        self.assertAlmostEqual(vp.distance_to(600, 500), 100)
    
    def test_lod_selector(self):
        selector = ViewportLODSelector()
        
        # 不同视口大小应选择不同 LOD
        small_vp = Viewport(0, 0, 50, 50)
        large_vp = Viewport(0, 0, 5000, 5000)
        
        small_level = selector.select(small_vp)
        large_level = selector.select(large_vp)
        
        # 视口越大，选择的 LOD 级别应该越高
        self.assertLessEqual(small_level.value, large_level.value)
    
    def test_lod_manager(self):
        manager = LODManager()
        
        viewport = Viewport(500, 500, 200, 200)
        level, points = manager.get_points(viewport, 0, 1000)
        
        self.assertIsNotNone(level)
        self.assertIsInstance(points, list)
    
    def test_multilevel_points(self):
        manager = LODManager()
        
        viewport = Viewport(500, 500, 200, 200)
        multi = manager.get_multilevel_points(viewport, 0, 1000)
        
        self.assertEqual(len(multi), 5)  # 5 个 LOD 级别


class TestLODGenerator(unittest.TestCase):
    """LOD 生成器测试"""
    
    def test_chainage_generator(self):
        generator = ChainageLODGenerator()
        
        # 测试线性生成
        points = generator.generate(LODLevel.LOD1, {
            'start': 0,
            'end': 100
        })
        
        self.assertGreater(len(points), 0)
        
        # 验证点间距
        for i in range(len(points) - 1):
            diff = points[i+1]['chainage'] - points[i]['chainage']
            self.assertLessEqual(diff, 10)  # LOD2 间距 10m


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBox))
    suite.addTests(loader.loadTestsFromTestCase(TestRTree))
    suite.addTests(loader.loadTestsFromTestCase(TestChainageRTree))
    suite.addTests(loader.loadTestsFromTestCase(TestLOD))
    suite.addTests(loader.loadTestsFromTestCase(TestLODGenerator))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
