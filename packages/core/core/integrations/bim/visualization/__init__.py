# -*- coding: utf-8 -*-
"""
BIM 可视化模块

提供 Three.js 集成的适配器
"""

from .threejs_adapter import ThreeJSAdapter, MeshData, SceneConfig
from .viewer import BIMViewer, ViewerComponent

__all__ = [
    "ThreeJSAdapter",
    "MeshData",
    "SceneConfig",
    "BIMViewer",
    "ViewerComponent"
]
