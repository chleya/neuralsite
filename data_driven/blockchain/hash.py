# -*- coding: utf-8 -*-
"""
哈希计算模块
"""

import hashlib
import json
from typing import Dict, Any, Optional


class HashComputer:
    """数据哈希计算器"""
    
    @staticmethod
    def compute_data_hash(data: Dict[str, Any], data_type: str) -> str:
        """
        计算结构化数据的哈希值
        
        Args:
            data: 数据字典
            data_type: 数据类型
        """
        # 根据数据类型提取关键字段
        key_fields = HashComputer._extract_key_fields(data, data_type)
        
        # 标准化排序后计算哈希
        normalized = json.dumps(key_fields, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        计算文件的哈希值
        
        Args:
            file_path: 文件路径
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def compute_file_hash_from_bytes(data: bytes) -> str:
        """从字节数据计算哈希"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def compute_verification_hash(data_id: str, data_hash: str, 
                                  operator: str) -> str:
        """
        计算验真记录的哈希值
        """
        content = f"{data_id}:{data_hash}:{operator}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _extract_key_fields(data: Dict, data_type: str) -> Dict:
        """提取关键字段"""
        
        if data_type == "design_change":
            return {
                "change_id": data.get("change_id"),
                "station_start": str(data.get("station_start", "")),
                "station_end": str(data.get("station_end", "")),
                "change_type": data.get("change_type"),
                "old_value": str(data.get("old_value", "")),
                "new_value": str(data.get("new_value", "")),
                "created_at": str(data.get("created_at", ""))
            }
        elif data_type == "quality_issue":
            return {
                "issue_id": data.get("issue_id"),
                "station": data.get("station"),
                "issue_type": data.get("issue_type"),
                "severity": data.get("severity"),
                "description": data.get("description"),
                "reported_at": str(data.get("reported_at", ""))
            }
        elif data_type == "quality_confirmation":
            return {
                "confirmation_id": data.get("confirmation_id"),
                "issue_id": data.get("issue_id"),
                "confirmed_by": data.get("confirmed_by"),
                "result": data.get("result"),
                "confirmed_at": str(data.get("confirmed_at", ""))
            }
        else:
            # 通用：使用所有非元数据字段
            return {k: v for k, v in data.items() 
                    if not k.startswith('_') and not k.endswith('_at')}
    
    @staticmethod
    def verify(data: Dict[str, Any], data_type: str, 
               expected_hash: str) -> bool:
        """
        验真：比对数据哈希
        """
        actual_hash = HashComputer.compute_data_hash(data, data_type)
        return actual_hash == expected_hash
