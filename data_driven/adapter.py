# -*- coding: utf-8 -*-
"""
数据接入适配器

连接新旧模块，处理照片、问题、空间等数据的接入
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from typing import Dict, Any, Optional
from datetime import datetime

# 导入数据驱动模块
from data_driven.standards import FileFormat
from data_driven.lineage import LineageRecord, LineageType, LineageStorage
from data_driven.validation import ValidationEngine

# 尝试导入核心引擎，如果失败则使用模拟实现
try:
    from packages.core.engine import NeuralSiteEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    # 创建模拟引擎类
    class NeuralSiteEngine:
        def __init__(self, route_id: str = ""):
            self.route_id = route_id
        
        def get_coordinate(self, station: float):
            """模拟坐标获取"""
            class MockCoord:
                def to_dict(self):
                    return {
                        'station': f"K{int(station)//1000}+{int(station)%1000:03d}",
                        'station_m': station,
                        'x': 500000 + station * 0.1,
                        'y': 3000000 + station * 0.1,
                        'z': 100 + station * 0.01,
                        'azimuth': 45
                    }
            return MockCoord()

# 尝试导入存储管理器
try:
    from packages.core.storage.manager import get_storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    # 创建模拟存储
    def get_storage():
        class MockStorage:
            pass
        return MockStorage()


class DataAdapter:
    """
    数据适配器 - 连接新旧模块
    
    负责：
    1. 验证数据格式
    2. 记录数据血缘
    3. 校验数据完整性
    4. 关联空间数据
    """
    
    def __init__(self, route_id: str = "default"):
        """初始化适配器
        
        Args:
            route_id: 路线ID
        """
        self.route_id = route_id
        self.engine = NeuralSiteEngine(route_id)
        self.storage = get_storage()
        self._validation_engine = None
    
    @property
    def validation_engine(self) -> ValidationEngine:
        """获取验证引擎（延迟加载）"""
        if self._validation_engine is None:
            self._validation_engine = ValidationEngine()
        return self._validation_engine
    
    # ========== 照片数据接入 ==========
    
    def import_photo(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        导入照片数据
        
        Args:
            photo_data: 照片数据字典，包含:
                - id: 照片ID
                - filename: 文件名
                - size: 文件大小
                - hash: 文件哈希
                - latitude: 纬度
                - longitude: 经度
                - station: 桩号 (可选)
                - captured_at: 拍摄时间 (可选)
                
        Returns:
            验证结果字典
        """
        # 1. 验证格式
        filename = photo_data.get('filename', '')
        size = photo_data.get('size', 0)
        
        format_valid = self._validate_file_format(filename, size)
        if not format_valid['valid']:
            return {
                'success': False,
                'error': format_valid['error'],
                'stage': 'format_validation'
            }
        
        # 2. 记录血缘
        lineage = self._record_lineage(
            data_id=photo_data.get('id', ''),
            data_type='photo',
            source_type=LineageType.IMPORT,
            metadata=photo_data
        )
        
        # 3. 校验数据
        validation_result = self._validate_photo_data(photo_data)
        
        return {
            'success': validation_result.get('valid', False),
            'lineage_id': lineage.get('id') if lineage else None,
            'validation': validation_result,
            'stage': 'validation'
        }
    
    def _validate_file_format(self, filename: str, size: int) -> Dict[str, Any]:
        """验证文件格式"""
        try:
            FileFormat.validate(filename, size)
            return {'valid': True}
        except ValueError as e:
            return {'valid': False, 'error': str(e)}
    
    def _record_lineage(self, data_id: str, data_type: str, 
                        source_type: LineageType, metadata: Dict) -> Optional[Dict]:
        """记录数据血缘"""
        try:
            lineage = LineageRecord(
                data_id=data_id,
                data_type=data_type,
                source_type=source_type,
                is_root=True
            )
            # 记录元数据到original_value
            import json
            lineage.original_value = json.dumps(metadata)
            
            # 保存血缘记录
            storage = LineageStorage()
            storage.save(lineage)
            
            return {'id': lineage.lineage_id, 'recorded': True}
        except Exception as e:
            print(f"记录血缘失败: {e}")
            return None
    
    def _validate_photo_data(self, photo_data: Dict) -> Dict[str, Any]:
        """校验照片数据"""
        result = self.validation_engine.validate(photo_data, 'photo')
        return {
            'valid': result.is_valid if hasattr(result, 'is_valid') else True,
            'errors': result.errors if hasattr(result, 'errors') else [],
            'warnings': result.warnings if hasattr(result, 'warnings') else []
        }
    
    # ========== 问题数据接入 ==========
    
    def import_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        导入问题数据
        
        Args:
            issue_data: 问题数据字典，包含:
                - id: 问题ID
                - type: 问题类型
                - severity: 严重程度
                - station: 桩号
                - description: 描述
                - photos: 相关照片ID列表
                
        Returns:
            验证结果字典
        """
        # 1. 验证必填字段
        required_fields = ['id', 'type', 'station']
        for field in required_fields:
            if field not in issue_data:
                return {
                    'success': False,
                    'error': f'缺少必填字段: {field}',
                    'stage': 'validation'
                }
        
        # 2. 记录血缘
        lineage = self._record_lineage(
            data_id=issue_data.get('id', ''),
            data_type='issue',
            source_type=LineageType.IMPORT,
            metadata=issue_data
        )
        
        # 3. 校验数据
        validation_result = self._validate_issue_data(issue_data)
        
        # 4. 关联空间数据
        spatial_info = self._resolve_spatial(issue_data.get('station'))
        
        return {
            'success': validation_result.get('valid', False),
            'lineage_id': lineage.get('id') if lineage else None,
            'spatial': spatial_info,
            'validation': validation_result,
            'stage': 'validation'
        }
    
    def _validate_issue_data(self, issue_data: Dict) -> Dict[str, Any]:
        """校验问题数据"""
        result = self.validation_engine.validate(issue_data, 'issue')
        return {
            'valid': result.is_valid if hasattr(result, 'is_valid') else True,
            'errors': result.errors if hasattr(result, 'errors') else [],
            'warnings': result.warnings if hasattr(result, 'warnings') else []
        }
    
    # ========== 空间数据接入 ==========
    
    def import_spatial(self, spatial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        导入空间数据
        
        Args:
            spatial_data: 空间数据字典，包含:
                - station: 桩号
                - type: 数据类型 (coordinate, cross_section等)
                - values: 坐标值
                
        Returns:
            处理结果
        """
        station = spatial_data.get('station', 0)
        
        # 调用几何引擎获取坐标
        coords = self._resolve_spatial(station)
        
        # 记录血缘
        lineage = self._record_lineage(
            data_id=f"spatial_{station}",
            data_type='spatial',
            source_type=LineageType.CALCULATION,
            metadata=spatial_data
        )
        
        return {
            'success': True,
            'coordinates': coords,
            'lineage_id': lineage.get('id') if lineage else None,
            'stage': 'spatial_resolved'
        }
    
    def _resolve_spatial(self, station: float) -> Dict[str, Any]:
        """
        解析空间数据 - 获取桩号对应的坐标
        
        Args:
            station: 桩号 (米)
            
        Returns:
            坐标字典
        """
        try:
            # 尝试解析桩号字符串
            if isinstance(station, str):
                station = self._parse_station(station)
            
            # 调用引擎获取坐标
            coord = self.engine.get_coordinate(station)
            return coord.to_dict()
        except Exception as e:
            return {
                'error': str(e),
                'station': station
            }
    
    def _parse_station(self, station_str: str) -> float:
        """解析桩号字符串"""
        import re
        m = re.search(r'K?(\d+)\+(\d{3})', str(station_str).upper())
        if m:
            return int(m.group(1)) * 1000 + int(m.group(2))
        return 0
    
    # ========== 批量接入 ==========
    
    def batch_import(self, data_list: list, data_type: str) -> Dict[str, Any]:
        """
        批量导入数据
        
        Args:
            data_list: 数据列表
            data_type: 数据类型 (photo, issue, spatial)
            
        Returns:
            批量导入结果
        """
        results = []
        success_count = 0
        failed_count = 0
        
        for data in data_list:
            if data_type == 'photo':
                result = self.import_photo(data)
            elif data_type == 'issue':
                result = self.import_issue(data)
            elif data_type == 'spatial':
                result = self.import_spatial(data)
            else:
                result = {'success': False, 'error': f'未知数据类型: {data_type}'}
            
            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1
            
            results.append(result)
        
        return {
            'total': len(data_list),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }


# ========== 工厂函数 ==========

def create_adapter(route_id: str = "default") -> DataAdapter:
    """创建数据适配器"""
    return DataAdapter(route_id)


# 测试
if __name__ == "__main__":
    # 测试照片导入
    adapter = DataAdapter("test_route")
    
    # 测试照片数据
    photo_data = {
        'id': 'photo_001',
        'filename': 'test.jpg',
        'size': 1024 * 1024,  # 1MB
        'latitude': 31.2304,
        'longitude': 121.4737
    }
    
    result = adapter.import_photo(photo_data)
    print("照片导入结果:", result)
    
    # 测试空间数据
    spatial_data = {
        'station': 1000,  # K1+000
        'type': 'coordinate'
    }
    
    result = adapter.import_spatial(spatial_data)
    print("空间数据结果:", result)
