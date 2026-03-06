# -*- coding: utf-8 -*-
"""
存证合约模块

定义区块链存证记录结构和存证合约逻辑
"""

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ChainRecord:
    """区块链存证记录"""
    
    chain_id: str = ""
    data_type: str = ""
    data_hash: str = ""
    data_summary: str = ""
    project_id: str = ""
    data_id: str = ""
    data_version: str = "1.0"
    operation: str = "create"
    operator: str = ""
    operator_role: str = ""
    timestamp: datetime = None
    block_number: int = 0
    tx_hash: str = ""
    previous_chain_id: str = ""
    
    def __post_init__(self):
        if not self.chain_id:
            self.chain_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 序列化datetime
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChainRecord':
        """从字典创建"""
        # 反序列化datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ChainContract:
    """存证合约
    
    提供存证提交、查询等核心功能
    """
    
    def __init__(self, storage):
        """
        初始化存证合约
        
        Args:
            storage: 存储后端（需实现save/get_by_data_id方法）
        """
        self.storage = storage
    
    def submit(self, data_id: str, data_hash: str, 
               data_type: str, operator: str, 
               operator_role: str, project_id: str,
               data_summary: str = "",
               data_version: str = "1.0",
               previous_chain_id: str = "") -> ChainRecord:
        """
        提交存证
        
        Args:
            data_id: 数据ID
            data_hash: 数据哈希
            data_type: 数据类型
            operator: 操作人
            operator_role: 操作人角色
            project_id: 项目ID
            data_summary: 数据摘要
            data_version: 数据版本
            previous_chain_id: 上一条链ID（用于版本追溯）
            
        Returns:
            存证记录
        """
        record = ChainRecord(
            data_id=data_id,
            data_hash=data_hash,
            data_type=data_type,
            operator=operator,
            operator_role=operator_role,
            project_id=project_id,
            data_summary=data_summary,
            data_version=data_version,
            operation="create",
            previous_chain_id=previous_chain_id
        )
        
        # 保存到存储
        self.storage.save(record)
        
        return record
    
    def update(self, data_id: str, data_hash: str,
               operator: str, operator_role: str,
               data_version: str = "1.0") -> ChainRecord:
        """
        更新存证
        
        Args:
            data_id: 数据ID
            data_hash: 新数据哈希
            operator: 操作人
            operator_role: 操作人角色
            data_version: 新版本号
            
        Returns:
            新的存证记录
        """
        # 获取上一条记录
        old_record = self.storage.get_by_data_id(data_id)
        
        record = ChainRecord(
            data_id=data_id,
            data_hash=data_hash,
            data_type=old_record.data_type if old_record else "",
            operator=operator,
            operator_role=operator_role,
            project_id=old_record.project_id if old_record else "",
            data_version=data_version,
            operation="update",
            previous_chain_id=old_record.chain_id if old_record else ""
        )
        
        self.storage.save(record)
        return record
    
    def get_record(self, data_id: str) -> Optional[ChainRecord]:
        """
        获取存证记录
        
        Args:
            data_id: 数据ID
            
        Returns:
            存证记录，不存在返回None
        """
        return self.storage.get_by_data_id(data_id)
    
    def get_history(self, data_id: str) -> list:
        """
        获取存证历史
        
        Args:
            data_id: 数据ID
            
        Returns:
            存证历史列表
        """
        return self.storage.get_history(data_id)


class DictStorageAdapter:
    """字典存储适配器
    
    将ChainRecord dataclass适配为verify.py中的MockChainStorage接口
    """
    
    def __init__(self):
        self._records = {}
    
    def save(self, record: ChainRecord):
        """保存存证记录"""
        chain_id = record.chain_id
        self._records[chain_id] = record.to_dict()
    
    def get_by_data_id(self, data_id: str) -> Optional[ChainRecord]:
        """根据数据ID获取存证记录"""
        for record in self._records.values():
            if record.get("data_id") == data_id:
                return ChainRecord.from_dict(record)
        return None
    
    def get_history(self, data_id: str) -> list:
        """获取历史记录"""
        return [ChainRecord.from_dict(r) for r in self._records.values() 
                if r.get("data_id") == data_id]
