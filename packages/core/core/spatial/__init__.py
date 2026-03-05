# -*- coding: utf-8 -*-
"""
Spatial Module
空间数据模块

包含:
- database: 空间数据库
- rtree_index: R-Tree 空间索引
- chainage_transform: 桩号坐标转换
- lod: 多级细节层次
"""

from .database import SpatialDatabase, SpatialPoint, get_spatial_db

# R-Tree 索引
from .rtree_index import (
    Box, RTree, SpatialItem, ChainageRTree
)

# 导出兼容别名
RTreeNode = None  # 保留兼容性

# 坐标转换
from .chainage_transform import (
    ChainagePoint, OffsetPoint, 
    ChainageTransformer, CombinedCurveCalculator
)

# LOD
from .lod import (
    LODLevel, LODConfig, Viewport,
    ChainageLODGenerator, ViewportLODSelector,
    LODManager, LOD_CONFIGS
)


__all__ = [
    # 数据库
    'SpatialDatabase', 'SpatialPoint', 'get_spatial_db',
    
    # R-Tree 索引
    'Box', 'RTree', 'RTreeNode', 'ChainageRTree',
    
    # 坐标转换
    'ChainagePoint', 'OffsetPoint', 
    'ChainageTransformer', 'CombinedCurveCalculator',
    
    # LOD
    'LODLevel', 'LODConfig', 'Viewport',
    'ChainageLODGenerator', 'ViewportLODSelector',
    'LODManager', 'LOD_CONFIGS',
]
