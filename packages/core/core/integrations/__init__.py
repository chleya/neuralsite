# -*- coding: utf-8 -*-
"""
NeuralSite 集成模块

## 子模块

### ERP 集成
与广联达、鲁班等主流施工ERP系统对接，实现数据互通

主要功能：
- 数据模型转换 (ERP ↔ NeuralSite)
- API 对接层 (适配器模式)
- 同步机制 (定时/增量/冲突处理)

### BIM 集成
BIM 数据导入模块，支持 IFC2x3/IFC4 格式

主要功能：
- IFC 解析 (IFC2x3/IFC4)
- 数据转换 (IFC → NeuralSite 实体)
- 导入 API (文件上传、进度追踪、错误报告)
- 3D 可视化 (Three.js 集成)
"""

from .erp_adapter import (
    # 枚举类型
    ERPType,
    SyncDirection,
    SyncStatus,
    ConflictResolution,
    # 数据模型
    ERPBillItem,
    ERPContract,
    ERPMeasurement,
    SyncRecord,
    SyncConfig,
    # 适配器
    ERPAdapter,
    GlodonAdapter,
    LubanAdapter,
    # 工具类
    ERPDataConverter,
    SyncEngine,
    ERPAdapterFactory,
    ERPFeatureFlags
)

# BIM 集成
from .bim import (
    IFCParser,
    IFCVersion,
    BIMConverter,
    BIMProject,
    BIMBuilding,
    BIMStorey,
    BIMElement,
    BIMProperty,
    BIMGeometry,
    ImportProgress,
    ImportError,
    ElementType
)

__version__ = "1.0.0"

__all__ = [
    # ERP 集成
    "ERPType",
    "SyncDirection",
    "SyncStatus",
    "ConflictResolution",
    "ERPBillItem",
    "ERPContract",
    "ERPMeasurement",
    "SyncRecord",
    "SyncConfig",
    "ERPAdapter",
    "GlodonAdapter",
    "LubanAdapter",
    "ERPDataConverter",
    "SyncEngine",
    "ERPAdapterFactory",
    "ERPFeatureFlags",
    
    # BIM 集成
    "IFCParser",
    "IFCVersion",
    "BIMConverter",
    "BIMProject",
    "BIMBuilding",
    "BIMStorey",
    "BIMElement",
    "BIMProperty",
    "BIMGeometry",
    "ImportProgress",
    "ImportError",
    "ElementType"
]
