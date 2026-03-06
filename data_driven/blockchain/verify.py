# -*- coding: utf-8 -*-
"""
验真模块
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class VerifyResult:
    """验真结果"""
    is_verified: bool
    chain_record: Optional[Dict[str, Any]] = None
    message: str = ""


class ChainVerifier:
    """验真器"""
    
    def __init__(self, storage):
        """
        初始化验真器
        
        Args:
            storage: 存证存储
        """
        self.storage = storage
    
    def verify(self, data_id: str, current_hash: str) -> VerifyResult:
        """
        验真：比对当前数据哈希与链上哈希
        
        Args:
            data_id: 数据ID
            current_hash: 当前数据的哈希值
            
        Returns:
            验真结果
        """
        # 从存储中获取链上记录
        chain_record = self.storage.get_by_data_id(data_id)
        
        if not chain_record:
            return VerifyResult(
                is_verified=False,
                message="No chain record found for this data"
            )
        
        # 兼容ChainRecord和dict
        if hasattr(chain_record, 'data_hash'):
            stored_hash = chain_record.data_hash
            chain_record_dict = chain_record.to_dict() if hasattr(chain_record, 'to_dict') else chain_record
        else:
            stored_hash = chain_record.get("data_hash")
            chain_record_dict = chain_record
        
        # 比对哈希
        if stored_hash == current_hash:
            return VerifyResult(
                is_verified=True,
                chain_record=chain_record_dict,
                message="Data is authentic, no tampering detected"
            )
        else:
            return VerifyResult(
                is_verified=False,
                chain_record=chain_record_dict,
                message=f"Hash mismatch: stored={stored_hash[:16]}..., current={current_hash[:16]}..."
            )
    
    def get_history(self, data_id: str) -> Dict[str, Any]:
        """
        获取数据变更历史
        
        Args:
            data_id: 数据ID
            
        Returns:
            变更历史
        """
        records = self.storage.get_history(data_id)
        return {
            "data_id": data_id,
            "record_count": len(records),
            "records": records
        }


class MockChainStorage:
    """模拟链上存储（用于测试）"""
    
    def __init__(self):
        self._records = {}
    
    def save(self, record: Dict[str, Any]):
        """保存存证记录"""
        chain_id = record.get("chain_id") or str(uuid.uuid4())
        record["chain_id"] = chain_id
        self._records[chain_id] = record
    
    def get_by_data_id(self, data_id: str) -> Optional[Dict]:
        """根据数据ID获取存证记录"""
        for record in self._records.values():
            if record.get("data_id") == data_id:
                return record
        return None
    
    def get_history(self, data_id: str):
        """获取历史记录"""
        return [r for r in self._records.values() 
                if r.get("data_id") == data_id]
