# -*- coding: utf-8 -*-
"""测试区块链存证模块"""
import sys
sys.path.insert(0, '.')

# 测试1: 导入模块
print('=== Test 1: Import Modules ===')
from blockchain import (
    HashComputer, ChainRecord, ChainContract,
    DictStorageAdapter, ChainVerifier, Web3Client
)
print('All modules imported successfully!')

# 测试2: 创建存证记录
print('\n=== Test 2: Create ChainRecord ===')
record = ChainRecord(
    data_id='test_data_001',
    data_hash='abc123def456',
    data_type='design_change',
    operator='chenleiyang',
    operator_role='engineer',
    project_id='project_001',
    data_summary='Test record'
)
print(f'chain_id: {record.chain_id}')
print(f'timestamp: {record.timestamp}')
print(f'data_id: {record.data_id}')
print(f'data_hash: {record.data_hash}')

# 测试3: 存证合约 - 提交和查询
print('\n=== Test 3: ChainContract Submit & Query ===')
storage = DictStorageAdapter()
contract = ChainContract(storage)

# 提交存证
new_record = contract.submit(
    data_id='design_change_001',
    data_hash='sha256_hash_abc123',
    data_type='design_change',
    operator='chenleiyang',
    operator_role='engineer',
    project_id='railway_project_001',
    data_summary='Design change record for station A'
)
print(f'Submitted: chain_id={new_record.chain_id[:16]}...')

# 查询存证
retrieved = contract.get_record('design_change_001')
print(f'Retrieved: data_id={retrieved.data_id}, hash={retrieved.data_hash[:16]}...')

# 测试4: 验真功能
print('\n=== Test 4: Verification ===')
verifier = ChainVerifier(storage)

# 正确的哈希
result = verifier.verify('design_change_001', 'sha256_hash_abc123')
print(f'Verify correct hash: {result.is_verified} - {result.message}')

# 错误的哈希
result2 = verifier.verify('design_change_001', 'wrong_hash_xyz')
print(f'Verify wrong hash: {result2.is_verified} - {result2.message}')

# 不存在的记录
result3 = verifier.verify('nonexistent_001', 'any_hash')
print(f'Verify nonexistent: {result3.is_verified} - {result3.message}')

# 测试5: Web3客户端（模拟模式）
print('\n=== Test 5: Web3Client (Mock Mode) ===')
web3 = Web3Client()  # 不传入provider_url，使用模拟模式
tx_hash = web3.submit_hash('test_hash', {'data_id': 'test_001', 'operator': 'tester'})
print(f'Submitted tx: {tx_hash}')

verified = web3.verify_hash('test_hash')
print(f'Verified: {verified}')

# 测试6: 完整流程 - 存证+验真
print('\n=== Test 6: Full Flow ===')
# 计算数据哈希
data = {
    'change_id': 'C001',
    'station_start': 'K001',
    'station_end': 'K002',
    'change_type': 'speed_limit',
    'old_value': '80',
    'new_value': '120',
    'created_at': '2026-03-06T10:00:00'
}
data_hash = HashComputer.compute_data_hash(data, 'design_change')
print(f'Computed data hash: {data_hash}')

# 提交存证
record = contract.submit(
    data_id='C001',
    data_hash=data_hash,
    data_type='design_change',
    operator='chenleiyang',
    operator_role='engineer',
    project_id='railway_001',
    data_summary='Speed limit change from 80 to 120 km/h'
)
print(f'Submitted to chain: {record.chain_id[:16]}...')

# 验真（正确数据）
result = verifier.verify('C001', data_hash)
print(f'Verification (correct): {result.is_verified}')

# 验真（篡改后数据）
data['new_value'] = '200'  # 篡改数据
tampered_hash = HashComputer.compute_data_hash(data, 'design_change')
result_tampered = verifier.verify('C001', tampered_hash)
print(f'Verification (tampered): {result_tampered.is_verified} - {result_tampered.message}')

print('\n=== All Tests Passed! ===')
