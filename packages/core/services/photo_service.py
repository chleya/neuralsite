# NeuralSite 照片服务
# 照片CRUD + GPS信息提取 + 桩号关联

import hashlib
import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from PIL import Image
from PIL.ExifTags import TAGS
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from api.deps import CurrentUser, NotFoundError
from models.p0_models import (
    PhotoRecord, PhotoCreate, PhotoUpdate, PhotoResponse,
    SyncStatus, IssueStatus
)


# ==================== 照片存储配置 ====================

PHOTO_STORAGE_PATH = os.getenv("PHOTO_STORAGE_PATH", "./photos")
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB


# ==================== GPS信息提取 ====================

def extract_gps_from_exif(file_path: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    从EXIF中提取GPS信息
    
    Returns:
        (latitude, longitude, accuracy)
    """
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        
        if not exif_data:
            return None, None, None
        
        # 解析GPS信息
        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                gps_info = value
                break
        
        if not gps_info:
            return None, None, None
        
        # GPS标签ID
        GPSLatitude = 1
        GPSLatitudeRef = 2
        GPSLongitude = 3
        GPSLongitudeRef = 4
        GPSAltitudeRef = 6
        GPSAltitude = 5
        
        def convert_to_degrees(value):
            """将GPS坐标转换为度数"""
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        
        lat = None
        lon = None
        
        if GPSLatitude in gps_info and GPSLatitudeRef in gps_info:
            lat = convert_to_degrees(gps_info[GPSLatitude])
            if gps_info[GPSLatitudeRef] == 'S':
                lat = -lat
        
        if GPSLongitude in gps_info and GPSLongitudeRef in gps_info:
            lon = convert_to_degrees(gps_info[GPSLongitude])
            if gps_info[GPSLongitudeRef] == 'W':
                lon = -lon
        
        # 简化的精度估算（实际应考虑卫星数量等因素）
        accuracy = 10.0  # 默认精度10米
        
        return lat, lon, accuracy
        
    except Exception as e:
        print(f"EXIF提取失败: {e}")
        return None, None, None


def calculate_file_hash(file_path: str) -> str:
    """计算文件SHA256哈希"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ==================== 桩号关联 ====================

def calculate_station_from_gps(
    latitude: float,
    longitude: float,
    project_id: uuid.UUID,
    db: Session
) -> Optional[float]:
    """
    根据GPS坐标计算桩号
    
    这是一个占位实现，实际需要：
    1. 查询项目的路线几何数据
    2. 使用线性参考系统计算最近桩号
    
    Returns:
        桩号值（米）
    """
    # TODO: 实现基于Neo4j的路线几何匹配
    # TODO: 实现基于PostGIS的空间查询
    return None


# ==================== 照片服务类 ====================

class PhotoService:
    """照片服务"""
    
    def __init__(self, db: Session, current_user: Optional[CurrentUser] = None):
        self.db = db
        self.current_user = current_user
    
    # ==================== 创建 ====================
    
    def create_photo(self, photo_data: PhotoCreate) -> PhotoRecord:
        """创建照片记录"""
        photo = PhotoRecord(
            photo_id=uuid.uuid4(),
            project_id=photo_data.project_id,
            file_path=photo_data.file_path,
            file_hash=photo_data.file_hash,
            file_size=photo_data.file_size,
            mime_type=photo_data.mime_type,
            captured_at=photo_data.captured_at,
            captured_by=photo_data.captured_by,
            latitude=photo_data.latitude,
            longitude=photo_data.longitude,
            gps_accuracy=photo_data.gps_accuracy,
            station=photo_data.station,
            station_display=photo_data.station_display,
            description=photo_data.description,
            tags=photo_data.tags or [],
            entity_id=photo_data.entity_id,
            entity_type=photo_data.entity_type,
            local_id=photo_data.local_id,
            sync_status=SyncStatus.PENDING if photo_data.local_id else SyncStatus.SYNCED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        
        return photo
    
    def create_photo_from_upload(
        self,
        file_path: str,
        project_id: uuid.UUID,
        captured_at: datetime,
        captured_by: Optional[uuid.UUID] = None,
        local_id: Optional[str] = None,
        **kwargs
    ) -> PhotoRecord:
        """从上传文件创建照片记录"""
        # 计算文件hash
        file_hash = calculate_file_hash(file_path)
        
        # 获取文件大小和类型
        file_size = os.path.getsize(file_path)
        mime_type = f"image/{os.path.splitext(file_path)[1][1:]}"
        
        # 尝试从EXIF提取GPS
        latitude = kwargs.get("latitude")
        longitude = kwargs.get("longitude")
        gps_accuracy = kwargs.get("gps_accuracy")
        
        if not latitude and not longitude:
            exif_lat, exif_lon, exif_acc = extract_gps_from_exif(file_path)
            if exif_lat and exif_lon:
                latitude = exif_lat
                longitude = exif_lon
                gps_accuracy = exif_acc
        
        # 如果有GPS但没有桩号，尝试计算
        station = kwargs.get("station")
        if not station and latitude and longitude:
            station = calculate_station_from_gps(latitude, longitude, project_id, self.db)
        
        photo_data = PhotoCreate(
            project_id=project_id,
            file_path=file_path,
            captured_at=captured_at,
            captured_by=captured_by,
            latitude=latitude,
            longitude=longitude,
            gps_accuracy=gps_accuracy,
            station=station,
            station_display=kwargs.get("station_display"),
            description=kwargs.get("description"),
            tags=kwargs.get("tags"),
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type,
            entity_id=kwargs.get("entity_id"),
            entity_type=kwargs.get("entity_type"),
            local_id=local_id
        )
        
        return self.create_photo(photo_data)
    
    # ==================== 查询 ====================
    
    def get_photo(self, photo_id: uuid.UUID) -> PhotoRecord:
        """获取单个照片"""
        photo = self.db.query(PhotoRecord).filter(PhotoRecord.photo_id == photo_id).first()
        if not photo:
            raise NotFoundError("照片", str(photo_id))
        return photo
    
    def list_photos(
        self,
        project_id: Optional[uuid.UUID] = None,
        station_start: Optional[float] = None,
        station_end: Optional[float] = None,
        captured_by: Optional[uuid.UUID] = None,
        is_verified: Optional[bool] = None,
        sync_status: Optional[SyncStatus] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PhotoRecord]:
        """查询照片列表"""
        query = self.db.query(PhotoRecord)
        
        if project_id:
            query = query.filter(PhotoRecord.project_id == project_id)
        
        if station_start is not None and station_end is not None:
            query = query.filter(
                and_(
                    PhotoRecord.station >= station_start,
                    PhotoRecord.station <= station_end
                )
            )
        elif station_start is not None:
            query = query.filter(PhotoRecord.station >= station_start)
        elif station_end is not None:
            query = query.filter(PhotoRecord.station <= station_end)
        
        if captured_by:
            query = query.filter(PhotoRecord.captured_by == captured_by)
        
        if is_verified is not None:
            query = query.filter(PhotoRecord.is_verified == is_verified)
        
        if sync_status:
            query = query.filter(PhotoRecord.sync_status == sync_status)
        
        if entity_type:
            query = query.filter(PhotoRecord.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(PhotoRecord.entity_id == entity_id)
        
        return query.order_by(PhotoRecord.captured_at.desc()).offset(skip).limit(limit).all()
    
    def count_photos(
        self,
        project_id: Optional[uuid.UUID] = None,
        **filters
    ) -> int:
        """统计照片数量"""
        query = self.db.query(PhotoRecord)
        
        if project_id:
            query = query.filter(PhotoRecord.project_id == project_id)
        
        for key, value in filters.items():
            if hasattr(PhotoRecord, key) and value is not None:
                query = query.filter(getattr(PhotoRecord, key) == value)
        
        return query.count()
    
    # ==================== 更新 ====================
    
    def update_photo(
        self,
        photo_id: uuid.UUID,
        photo_update: PhotoUpdate
    ) -> PhotoRecord:
        """更新照片信息"""
        photo = self.get_photo(photo_id)
        
        if photo_update.station is not None:
            photo.station = photo_update.station
        if photo_update.station_display is not None:
            photo.station_display = photo_update.station_display
        if photo_update.description is not None:
            photo.description = photo_update.description
        if photo_update.tags is not None:
            photo.tags = photo_update.tags
        if photo_update.is_verified is not None:
            photo.is_verified = photo_update.is_verified
        if photo_update.verified_by is not None:
            photo.verified_by = photo_update.verified_by
        
        photo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(photo)
        
        return photo
    
    def verify_photo(
        self,
        photo_id: uuid.UUID,
        verified_by: uuid.UUID
    ) -> PhotoRecord:
        """人工确认照片"""
        photo = self.get_photo(photo_id)
        
        photo.is_verified = True
        photo.verified_by = verified_by
        photo.verified_at = datetime.utcnow()
        photo.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(photo)
        
        return photo
    
    # ==================== 删除 ====================
    
    def delete_photo(self, photo_id: uuid.UUID) -> None:
        """删除照片"""
        photo = self.get_photo(photo_id)
        
        # 删除物理文件
        if os.path.exists(photo.file_path):
            try:
                os.remove(photo.file_path)
            except OSError:
                pass  # 忽略文件删除错误
        
        # 删除数据库记录
        self.db.delete(photo)
        self.db.commit()
    
    # ==================== AI分类 ====================
    
    def classify_photo(self, photo_id: uuid.UUID) -> dict:
        """
        AI分类照片（占位实现）
        
        实际需要调用图像分类模型
        """
        photo = self.get_photo(photo_id)
        
        # TODO: 调用AI模型进行分类
        # 示例返回
        classification = {
            "type": "quality",
            "value": "crack",
            "confidence": 0.85,
            "needs_verification": True,
            "suggestion": "建议人工确认"
        }
        
        # 保存分类结果
        photo.ai_classification = classification
        photo.updated_at = datetime.utcnow()
        self.db.commit()
        
        return classification
    
    # ==================== 同步相关 ====================
    
    def get_pending_sync_photos(
        self,
        device_id: str,
        limit: int = 100
    ) -> List[PhotoRecord]:
        """获取待同步的照片"""
        return self.db.query(PhotoRecord).filter(
            and_(
                PhotoRecord.sync_status == SyncStatus.PENDING,
                PhotoRecord.local_id.isnot(None)
            )
        ).limit(limit).all()
    
    def mark_as_synced(self, photo_id: uuid.UUID) -> None:
        """标记为已同步"""
        photo = self.get_photo(photo_id)
        photo.sync_status = SyncStatus.SYNCED
        photo.local_id = None
        photo.updated_at = datetime.utcnow()
        self.db.commit()
