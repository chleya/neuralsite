# -*- coding: utf-8 -*-
"""
数据服务层

对外提供统一的数据服务接口
"""

import os
import uuid
import hashlib
import aiofiles
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# 导入适配器
from data_driven.adapter import DataAdapter, create_adapter

# 导入区块链模块
try:
    from data_driven.blockchain import hash as blockchain_hash
    from data_driven.blockchain.verify import verify_evidence
    BLOCKCHAIN_AVAILABLE = True
except ImportError:
    BLOCKCHAIN_AVAILABLE = False


class DataService:
    """
    数据服务 - 对外统一接口
    
    负责：
    1. 处理文件上传
    2. 提取GPS和关联桩号
    3. 记录数据血缘
    4. 校验数据
    5. 上链存证
    """
    
    def __init__(self, adapter: Optional[DataAdapter] = None, route_id: str = "default"):
        """初始化数据服务
        
        Args:
            adapter: 数据适配器实例
            route_id: 路线ID
        """
        self.adapter = adapter or create_adapter(route_id)
        self.route_id = route_id
        
        # 上传配置
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads/photos")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    # ========== 照片服务 ==========
    
    async def upload_photo(self, file, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传照片
        
        流程：
        1. 保存文件
        2. 计算文件哈希
        3. 提取GPS信息
        4. 关联桩号
        5. 记录血缘
        6. 校验数据
        7. 上链存证
        
        Args:
            file: FastAPI UploadFile对象
            location: 位置信息，包含:
                - latitude: 纬度
                - longitude: 经度
                - station: 桩号 (可选)
                
        Returns:
            上传结果
        """
        try:
            # 1. 保存文件
            file_id = str(uuid.uuid4())
            file_ext = os.path.splitext(file.filename)[1].lower()
            file_path = os.path.join(self.upload_dir, f"{file_id}{file_ext}")
            
            content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # 2. 计算文件哈希
            file_hash = self._calculate_hash(content)
            file_size = len(content)
            
            # 3. 提取GPS信息
            gps_info = self._extract_gps(content, file.filename)
            latitude = location.get('latitude') or gps_info.get('latitude')
            longitude = location.get('longitude') or gps_info.get('longitude')
            
            # 4. 关联桩号
            station = location.get('station')
            if not station and latitude and longitude:
                station = await self._estimate_station(latitude, longitude)
            
            # 5. 准备照片数据
            photo_data = {
                'id': file_id,
                'filename': file.filename,
                'size': file_size,
                'hash': file_hash,
                'latitude': latitude,
                'longitude': longitude,
                'station': station,
                'captured_at': gps_info.get('captured_at'),
                'file_path': file_path
            }
            
            # 6. 记录血缘
            lineage_result = self.adapter.import_photo(photo_data)
            
            # 7. 校验数据
            validation = lineage_result.get('validation', {})
            
            # 8. 上链存证
            chain_result = {}
            if BLOCKCHAIN_AVAILABLE:
                chain_result = await self._store_on_chain(photo_data)
            
            return {
                'success': True,
                'photo_id': file_id,
                'file_path': file_path,
                'file_hash': file_hash,
                'file_size': file_size,
                'latitude': latitude,
                'longitude': longitude,
                'station': station,
                'lineage_id': lineage_result.get('lineage_id'),
                'validation': validation,
                'chain': chain_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'upload'
            }
    
    def _calculate_hash(self, content: bytes) -> str:
        """计算文件哈希"""
        return hashlib.sha256(content).hexdigest()
    
    def _extract_gps(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        从文件提取GPS信息
        
        目前只处理文件名，后续可扩展EXIF读取
        """
        # 从文件名尝试提取位置信息（如果有）
        gps_info = {}
        
        # 这里可以添加EXIF读取逻辑
        # 使用: from PIL import Image
        #       from PIL.ExifTags import TAGS
        
        return gps_info
    
    async def _estimate_station(self, latitude: float, longitude: float) -> Optional[float]:
        """
        根据GPS估算桩号
        
        需要路线数据支持
        """
        # TODO: 实现基于位置的桩号估算
        # 可以使用最近点查找算法
        return None
    
    async def _store_on_chain(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """上链存证"""
        try:
            evidence = blockchain_hash.create_evidence(
                data_id=data['id'],
                data_hash=data['hash'],
                metadata=data
            )
            return {
                'stored': True,
                'evidence_id': evidence.get('id')
            }
        except Exception as e:
            return {
                'stored': False,
                'error': str(e)
            }
    
    # ========== 问题服务 ==========
    
    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建问题
        
        Args:
            issue_data: 问题数据，包含:
                - type: 问题类型
                - severity: 严重程度
                - station: 桩号
                - description: 描述
                - photos: 照片ID列表
                
        Returns:
            创建结果
        """
        try:
            # 添加ID
            if 'id' not in issue_data:
                issue_data['id'] = str(uuid.uuid4())
            
            # 调用适配器导入问题
            result = self.adapter.import_issue(issue_data)
            
            # 上链存证
            chain_result = {}
            if BLOCKCHAIN_AVAILABLE:
                chain_result = await self._store_on_chain(issue_data)
            
            return {
                'success': result.get('success', False),
                'issue_id': issue_data['id'],
                'lineage_id': result.get('lineage_id'),
                'spatial': result.get('spatial'),
                'validation': result.get('validation'),
                'chain': chain_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'create_issue'
            }
    
    async def update_issue(self, issue_id: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新问题"""
        # TODO: 实现问题更新逻辑
        return {
            'success': False,
            'error': 'Not implemented'
        }
    
    async def delete_issue(self, issue_id: str) -> Dict[str, Any]:
        """删除问题"""
        # TODO: 实现问题删除逻辑
        return {
            'success': False,
            'error': 'Not implemented'
        }
    
    # ========== 查询服务 ==========
    
    async def query_issues(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询问题
        
        Args:
            filters: 查询过滤器，支持:
                - station_start: 起始桩号
                - station_end: 结束桩号
                - type: 问题类型
                - severity: 严重程度
                - limit: 返回数量限制
                
        Returns:
            问题列表
        """
        try:
            # TODO: 实现数据库查询
            # 临时返回空列表
            issues = []
            
            return {
                'success': True,
                'total': len(issues),
                'issues': issues
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'query_issues'
            }
    
    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """获取单个问题"""
        try:
            # TODO: 实现单个问题查询
            return {
                'success': False,
                'error': 'Not implemented'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== 空间数据服务 ==========
    
    async def get_coordinates(self, station: float) -> Dict[str, Any]:
        """
        获取坐标
        
        Args:
            station: 桩号 (米)
            
        Returns:
            坐标信息
        """
        try:
            result = self.adapter.import_spatial({
                'station': station,
                'type': 'coordinate'
            })
            
            return {
                'success': result.get('success', False),
                'coordinates': result.get('coordinates'),
                'lineage_id': result.get('lineage_id')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_get_coordinates(self, stations: List[float]) -> Dict[str, Any]:
        """
        批量获取坐标
        
        Args:
            stations: 桩号列表
            
        Returns:
            坐标列表
        """
        results = []
        for station in stations:
            coord_result = await self.get_coordinates(station)
            results.append({
                'station': station,
                'coordinates': coord_result.get('coordinates')
            })
        
        return {
            'success': True,
            'total': len(results),
            'results': results
        }
    
    # ========== 数据统计 ==========
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计"""
        return {
            'success': True,
            'stats': {
                'photos': 0,
                'issues': 0,
                'spatial_points': 0
            }
        }


# ========== 工厂函数 ==========

def create_service(route_id: str = "default") -> DataService:
    """创建数据服务"""
    adapter = create_adapter(route_id)
    return DataService(adapter, route_id)


# 测试
if __name__ == "__main__":
    import asyncio
    
    async def test():
        service = DataService()
        
        # 测试创建问题
        issue_data = {
            'type': '路面破损',
            'severity': '中',
            'station': 1000,
            'description': '测试问题'
        }
        
        result = await service.create_issue(issue_data)
        print("创建问题结果:", result)
        
        # 测试查询
        query_result = await service.query_issues({'limit': 10})
        print("查询结果:", query_result)
    
    asyncio.run(test())
