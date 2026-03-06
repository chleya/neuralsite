# -*- coding: utf-8 -*-
"""
照片采集完整流程模块

整合GPS提取、桩号匹配、格式校验、血缘记录、区块链存证
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from .geo_utils import GeoExtractor
from .station_matcher import StationMatcher
from .standards.formats import FileFormat
from .blockchain.hash import HashComputer


class PhotoCaptureFlow:
    """照片采集完整流程"""
    
    def __init__(self, service=None, connection_string: str = None):
        """
        初始化照片采集流程
        
        Args:
            service: 数据服务实例 (可选)
            connection_string: 数据库连接字符串 (可选)
        """
        self.service = service
        self.geo = GeoExtractor()
        self.matcher = StationMatcher(connection_string=connection_string)
        
        # 血缘记录器 (延迟初始化)
        self._lineage_tracer = None
        
        # 区块链存证器 (延迟初始化)
        self._chain_verifier = None
        
        # 照片存储
        self._photos: Dict[str, Dict[str, Any]] = {}
    
    @property
    def lineage_tracer(self):
        """获取血缘追踪器"""
        if self._lineage_tracer is None:
            try:
                from .lineage.trace import LineageTracerSQL
                from .lineage.storage import LineageStorageSQL
                
                storage = LineageStorageSQL()
                self._lineage_tracer = LineageTracerSQL(storage)
            except ImportError as e:
                print(f"Lineage module not available: {e}")
                self._lineage_tracer = None
        
        return self._lineage_tracer
    
    @property
    def chain_verifier(self):
        """获取区块链验真器"""
        if self._chain_verifier is None:
            try:
                from .blockchain.verify import ChainVerifier, MockChainStorage
                
                storage = MockChainStorage()
                self._chain_verifier = ChainVerifier(storage)
            except ImportError as e:
                print(f"Blockchain module not available: {e}")
                self._chain_verifier = None
        
        return self._chain_verifier
    
    async def capture(self, image_path: str, 
                     manual_location: Optional[Dict[str, float]] = None,
                     entity_id: Optional[str] = None,
                     project_id: int = 1,
                     operator: str = "system") -> Dict[str, Any]:
        """
        完整采集流程
        
        Step 1: 提取/获取GPS
        Step 2: 匹配桩号
        Step 3: 格式校验
        Step 4: 血缘记录
        Step 5: 存证上链
        Step 6: 保存到数据库
        
        Args:
            image_path: 照片文件路径
            manual_location: 手动指定的GPS坐标 {"lat": float, "lon": float}
            entity_id: 关联的实体ID
            project_id: 项目ID
            operator: 操作人
            
        Returns:
            采集结果 {
                "photo_id": "xxx",
                "station": "K0+000",
                "location": {"lat": float, "lon": float},
                "status": "saved",
                "lineage_id": "xxx",
                "chain_id": "xxx"
            }
            
        Raises:
            ValueError: GPS提取失败或格式校验失败
        """
        # ==================== Step 1: 获取位置 ====================
        if manual_location:
            lat = manual_location.get('lat')
            lon = manual_location.get('lon')
            if lat is None or lon is None:
                raise ValueError("Invalid manual location: missing lat or lon")
        else:
            gps = self.geo.extract_gps(image_path)
            if not gps:
                raise ValueError("无法从照片提取GPS信息，请手动提供位置")
            lat, lon = gps
        
        # ==================== Step 2: 匹配桩号 ====================
        station_info = self.matcher.match_station(
            lat, lon, 
            max_distance=100,  # 最多100米
            project_id=project_id
        )
        
        station = station_info['station'] if station_info else None
        match_distance = station_info.get('distance') if station_info else None
        
        # ==================== Step 3: 格式校验 ====================
        if not os.path.exists(image_path):
            raise ValueError(f"File not found: {image_path}")
        
        file_size = os.path.getsize(image_path)
        is_valid, error_msg = FileFormat.validate(os.path.basename(image_path), file_size)
        
        if not is_valid:
            raise ValueError(f"File validation failed: {error_msg}")
        
        # ==================== Step 4: 计算文件哈希 ====================
        file_hash = HashComputer.compute_file_hash(image_path)
        
        # ==================== Step 5: 生成照片ID ====================
        photo_id = str(uuid.uuid4())
        
        # ==================== Step 6: 记录血缘 ====================
        lineage_id = None
        if self.lineage_tracer and entity_id:
            lineage_id = await self._record_lineage(
                photo_id=photo_id,
                entity_id=entity_id,
                project_id=project_id,
                file_hash=file_hash,
                station=station,
                operator=operator
            )
        
        # ==================== Step 7: 存证上链 ====================
        chain_id = None
        if self.chain_verifier:
            chain_id = await self._record_to_chain(
                photo_id=photo_id,
                data_hash=file_hash,
                data={
                    "photo_id": photo_id,
                    "file_path": image_path,
                    "station": station,
                    "location": {"lat": lat, "lon": lon},
                    "entity_id": entity_id,
                    "project_id": project_id,
                    "operator": operator
                },
                operator=operator
            )
        
        # ==================== Step 8: 保存到内存 (实际应存数据库) ====================
        photo_record = {
            "photo_id": photo_id,
            "entity_id": entity_id,
            "project_id": project_id,
            "station": station,
            "filename": os.path.basename(image_path),
            "file_path": image_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "location": {
                "lat": lat,
                "lon": lon
            },
            "match_distance": match_distance,
            "lineage_id": lineage_id,
            "chain_id": chain_id,
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
            "operator": operator,
            "status": "saved"
        }
        
        self._photos[photo_id] = photo_record
        
        # 如果有service，保存到数据库
        if self.service:
            await self._save_to_database(photo_record)
        
        return {
            "photo_id": photo_id,
            "station": station,
            "location": {"lat": lat, "lon": lon},
            "match_distance": match_distance,
            "lineage_id": lineage_id,
            "chain_id": chain_id,
            "status": "saved"
        }
    
    async def _record_lineage(self, photo_id: str, entity_id: str,
                              project_id: int, file_hash: str,
                              station: Optional[str],
                              operator: str) -> Optional[str]:
        """记录血缘"""
        try:
            from .lineage.models import LineageRecord
            from .lineage.storage import LineageStorageSQL
            
            # 创建血缘记录
            lineage_id = str(uuid.uuid4())
            record = LineageRecord(
                lineage_id=lineage_id,
                data_id=photo_id,
                data_type="photo",
                parent_lineage_id=None,  # 根节点
                project_id=project_id,
                generation=0,
                operator=operator,
                metadata_json=json.dumps({
                    "entity_id": entity_id,
                    "station": station,
                    "file_hash": file_hash
                })
            )
            
            # 保存 (需要storage实例)
            storage = LineageStorageSQL()
            storage.save(record)
            
            return lineage_id
        except Exception as e:
            print(f"Lineage recording failed: {e}")
            return None
    
    async def _record_to_chain(self, photo_id: str, data_hash: str,
                              data: Dict[str, Any], 
                              operator: str) -> Optional[str]:
        """记录到区块链"""
        try:
            # 计算验真哈希
            verification_hash = HashComputer.compute_verification_hash(
                photo_id, data_hash, operator
            )
            
            # 创建存证记录
            chain_record = {
                "data_id": photo_id,
                "data_type": "photo",
                "data_hash": data_hash,
                "verification_hash": verification_hash,
                "record_data": data,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "operator": operator
            }
            
            # 保存到模拟链
            if hasattr(self.chain_verifier.storage, 'save'):
                self.chain_verifier.storage.save(chain_record)
            
            return chain_record.get("chain_id")
        except Exception as e:
            print(f"Chain recording failed: {e}")
            return None
    
    async def _save_to_database(self, photo_record: Dict[str, Any]):
        """保存到数据库 (需要service实现)"""
        # 实际实现应根据service接口保存到数据库
        # 这里仅作为接口定义
        pass
    
    def get_photo(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """获取照片记录"""
        return self._photos.get(photo_id)
    
    def list_photos(self, project_id: int = None,
                   station: str = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """列出照片记录"""
        results = list(self._photos.values())
        
        if project_id:
            results = [p for p in results if p.get('project_id') == project_id]
        
        if station:
            results = [p for p in results if p.get('station') == station]
        
        return results[:limit]
    
    async def verify_photo(self, photo_id: str) -> Dict[str, Any]:
        """
        验真照片
        
        检查照片是否与链上记录一致
        
        Args:
            photo_id: 照片ID
            
        Returns:
            验真结果
        """
        photo = self.get_photo(photo_id)
        if not photo:
            return {"verified": False, "message": "Photo not found"}
        
        # 重新计算当前文件哈希
        try:
            current_hash = HashComputer.compute_file_hash(photo['file_path'])
        except Exception as e:
            return {"verified": False, "message": f"Cannot read file: {e}"}
        
        # 验真
        if self.chain_verifier:
            result = self.chain_verifier.verify(photo_id, current_hash)
            return {
                "verified": result.is_verified,
                "message": result.message,
                "chain_record": result.chain_record
            }
        
        return {
            "verified": True,
            "message": "No chain verifier available, assuming valid",
            "current_hash": current_hash,
            "stored_hash": photo.get('file_hash')
        }


class PhotoCaptureService:
    """照片采集服务 (提供更高级的接口)"""
    
    def __init__(self, connection_string: str = None):
        self.flow = PhotoCaptureFlow(connection_string=connection_string)
    
    async def upload_photo(self, image_path: str, 
                          entity_id: str = None,
                          project_id: int = 1,
                          operator: str = "system",
                          auto_location: bool = True) -> Dict[str, Any]:
        """
        上传照片的便捷方法
        
        Args:
            image_path: 照片路径
            entity_id: 关联实体
            project_id: 项目ID
            operator: 操作人
            auto_location: 是否自动提取GPS
            
        Returns:
            上传结果
        """
        if auto_location:
            return await self.flow.capture(
                image_path=image_path,
                entity_id=entity_id,
                project_id=project_id,
                operator=operator
            )
        else:
            # 需要手动提供位置
            raise ValueError("Manual location not yet implemented")
    
    def add_test_stations(self):
        """添加测试桩号数据"""
        test_stations = [
            {"station": "K0+000", "x": 121.4737, "y": 31.2304, "elevation": 10},
            {"station": "K0+100", "x": 121.4747, "y": 31.2314, "elevation": 12},
            {"station": "K0+200", "x": 121.4757, "y": 31.2324, "elevation": 15},
            {"station": "K0+300", "x": 121.4767, "y": 31.2334, "elevation": 18},
            {"station": "K0+400", "x": 121.4777, "y": 31.2344, "elevation": 20},
        ]
        
        for s in test_stations:
            self.flow.matcher.add_station(**s)


# 测试
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # 创建服务
        service = PhotoCaptureService()
        
        # 添加测试桩号
        service.add_test_stations()
        print("Added test stations")
        
        # 模拟照片采集 (需要实际的照片文件)
        # result = await service.upload_photo(
        #     image_path="test.jpg",
        #     entity_id="entity_001",
        #     project_id=1,
        #     operator="test_user"
        # )
        
        print("Photo capture service ready")
        
        # 测试桩号匹配
        result = service.flow.matcher.match_station(31.2324, 121.4757, max_distance=50)
        print(f"Match result: {result}")
    
    asyncio.run(test())
