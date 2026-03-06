# -*- coding: utf-8 -*-
"""
数据血缘模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class LineageType(Enum):
    """血缘类型"""
    IMPORT = "import"           # 导入
    CALCULATION = "calculation" # 计算
    MANUAL = "manual"           # 人工录入
    AI_PREDICT = "ai_predict"  # AI生成
    TRANSFORM = "transform"     # 转换


@dataclass
class LineageRecord:
    """数据血缘记录"""
    
    lineage_id: str = ""
    data_id: str = ""
    data_type: str = ""
    data_version: str = "1.0"
    project_id: str = ""
    
    # 来源信息
    source_type: LineageType = LineageType.MANUAL
    source_system: str = ""
    source_file: str = ""
    imported_at: Optional[datetime] = None
    imported_by: str = ""
    original_value: str = ""
    
    # 血缘链
    parent_lineage_id: str = ""
    generation: int = 0
    
    # 元数据
    is_root: bool = False
    is_leaf: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.lineage_id:
            self.lineage_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "lineage_id": self.lineage_id,
            "data_id": self.data_id,
            "data_type": self.data_type,
            "data_version": self.data_version,
            "project_id": self.project_id,
            "source_type": self.source_type.value,
            "source_system": self.source_system,
            "source_file": self.source_file,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            "imported_by": self.imported_by,
            "original_value": self.original_value,
            "parent_lineage_id": self.parent_lineage_id,
            "generation": self.generation,
            "is_root": self.is_root,
            "is_leaf": self.is_leaf,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LineageStorage:
    """血缘存储"""
    
    def __init__(self):
        self._storage = {}  # 临时存储
    
    def save(self, record: LineageRecord):
        """保存血缘记录"""
        self._storage[record.lineage_id] = record
    
    def get(self, lineage_id: str) -> Optional[LineageRecord]:
        """获取血缘记录"""
        return self._storage.get(lineage_id)
    
    def get_by_data_id(self, data_id: str) -> List[LineageRecord]:
        """根据数据ID查询"""
        return [r for r in self._storage.values() if r.data_id == data_id]
    
    def get_children(self, lineage_id: str) -> List[LineageRecord]:
        """获取子节点"""
        return [r for r in self._storage.values() 
                if r.parent_lineage_id == lineage_id]


class LineageTracer:
    """血缘追溯"""
    
    def __init__(self, storage: LineageStorage):
        self.storage = storage
    
    def trace_forward(self, lineage_id: str) -> List[LineageRecord]:
        """正向追溯：从原始数据到衍生数据"""
        result = []
        current = self.storage.get(lineage_id)
        
        while current:
            result.append(current)
            children = self.storage.get_children(current.lineage_id)
            if not children:
                break
            current = children[0]  # 取第一个子节点
            
        return result
    
    def trace_backward(self, lineage_id: str) -> List[LineageRecord]:
        """反向追溯：从衍生数据到原始数据"""
        result = []
        current = self.storage.get(lineage_id)
        
        while current:
            result.append(current)
            if not current.parent_lineage_id:
                break
            current = self.storage.get(current.parent_lineage_id)
            
        return list(reversed(result))
