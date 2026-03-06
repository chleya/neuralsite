# -*- coding: utf-8 -*-
"""
区块链存证模块
对应规格书第3周任务
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ChainRecord:
    """链上记录"""
    id: UUID = field(default_factory=uuid4)
    data_type: str = ""           # entity_state/issue/process_data
    data_id: str = ""             # 对应数据ID
    data_hash: str = ""          # 数据的SHA-256哈希
    timestamp: datetime = field(default_factory=datetime.now)
    tx_hash: str = ""            # 交易哈希
    verified: bool = False


class BlockchainRecorder:
    """区块链存证器（内存实现，可对接真实区块链）"""
    
    def __init__(self):
        self.records: Dict[str, ChainRecord] = {}  # data_id -> record
    
    def compute_hash(self, data: dict) -> str:
        """计算数据哈希"""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def record_state(self, state_data: dict) -> ChainRecord:
        """
        记录实体状态到区块链
        对应规格书: entity_states.hash上链
        """
        # 计算哈希
        data_hash = self.compute_hash({
            'entity_id': state_data.get('entity_id'),
            'snapshot_time': state_data.get('snapshot_time'),
            'version_type': state_data.get('version_type'),
            'progress': state_data.get('progress'),
            'spatial_snapshot': state_data.get('spatial_snapshot', {}),
            'attribute_snapshot': state_data.get('attribute_snapshot', {})
        })
        
        # 创建记录
        record = ChainRecord(
            data_type='entity_state',
            data_id=state_data.get('id', str(uuid4())),
            data_hash=data_hash,
            timestamp=datetime.now(),
            tx_hash=self._generate_tx_hash()
        )
        
        self.records[record.data_id] = record
        return record
    
    def record_issue(self, issue_data: dict) -> ChainRecord:
        """记录问题到区块链"""
        data_hash = self.compute_hash({
            'issue_type': issue_data.get('issue_type'),
            'severity': issue_data.get('severity'),
            'description': issue_data.get('description'),
            'created_at': issue_data.get('created_at')
        })
        
        record = ChainRecord(
            data_type='issue',
            data_id=issue_data.get('id', str(uuid4())),
            data_hash=data_hash,
            timestamp=datetime.now(),
            tx_hash=self._generate_tx_hash()
        )
        
        self.records[record.data_id] = record
        return record
    
    def _generate_tx_hash(self) -> str:
        """生成模拟交易哈希"""
        import random
        return '0x' + ''.join([random.choice('0123456789abcdef') for _ in range(64)])
    
    def verify(self, data_id: str, current_data: dict) -> Dict:
        """
        验证数据真实性
        对应规格书: POST /api/v1/chain/verify
        """
        record = self.records.get(data_id)
        if not record:
            return {
                'verified': False,
                'message': '未找到存证记录'
            }
        
        # 重新计算当前数据哈希
        computed_hash = self.compute_hash(current_data)
        
        # 比对
        match = computed_hash == record.data_hash
        
        return {
            'verified': match,
            'stored_hash': record.data_hash,
            'computed_hash': computed_hash,
            'timestamp': record.timestamp.isoformat(),
            'tx_hash': record.tx_hash
        }
    
    def get_history(self, data_type: str = None) -> List[Dict]:
        """获取存证历史"""
        records = self.records.values()
        if data_type:
            records = [r for r in records if r.data_type == data_type]
        
        return [
            {
                'id': str(r.id),
                'data_type': r.data_type,
                'data_id': r.data_id,
                'data_hash': r.data_hash[:16] + '...',
                'timestamp': r.timestamp.isoformat(),
                'tx_hash': r.tx_hash[:10] + '...',
                'verified': r.verified
            }
            for r in sorted(records, key=lambda x: x.timestamp, reverse=True)
        ]


# 测试
if __name__ == "__main__":
    recorder = BlockchainRecorder()
    
    # 记录实体状态
    state_data = {
        'id': 'state-001',
        'entity_id': 'entity-001',
        'snapshot_time': '2026-03-06T10:00:00',
        'version_type': 'actual',
        'progress': 85,
        'spatial_snapshot': {'coverage': 0.85},
        'attribute_snapshot': {'layers': [{'name': '基层', 'status': 'completed'}]}
    }
    
    record = recorder.record_state(state_data)
    print(f"Recorded state: {record.tx_hash[:20]}...")
    
    # 验证
    result = recorder.verify('state-001', state_data)
    print(f"\nVerification:")
    print(f"  Verified: {result['verified']}")
    print(f"  Timestamp: {result['timestamp']}")
    print(f"  TX Hash: {result['tx_hash'][:20]}...")
    
    # 获取历史
    history = recorder.get_history('entity_state')
    print(f"\nHistory: {len(history)} records")
    for h in history[:3]:
        print(f"  {h['data_type']}: {h['data_hash']} @ {h['timestamp']}")
