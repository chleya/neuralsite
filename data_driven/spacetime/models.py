# -*- coding: utf-8 -*-
"""
时空状态管理系统 - 数据库模型
基于规格书V1.0
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import json
import hashlib


class EntityType(Enum):
    """工程实体类型"""
    SUBGRADE = "subgrade"      # 路基
    PAVEMENT = "pavement"      # 路面
    BRIDGE = "bridge"           # 桥梁
    CULVERT = "culvert"         # 涵洞
    TUNNEL = "tunnel"           # 隧道


class VersionType(Enum):
    """状态版本类型"""
    INITIAL = "initial"         # 初始
    DESIGNED = "designed"       # 设计
    ACTUAL = "actual"           # 实际
    AS_BUILT = "as_built"      # 竣工
    SIMULATED = "simulated"    # 模拟


class EventType(Enum):
    """事件类型"""
    WEATHER = "weather"         # 天气
    BLOCKAGE = "blockage"       # 阻工
    DISASTER = "disaster"       # 地质灾害
    CHANGE_ORDER = "change_order"  # 变更


@dataclass
class Project:
    """项目"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SpatialControl:
    """空间控制点"""
    id: UUID = field(default_factory=uuid4)
    project_id: UUID = None
    station: float = 0          # 桩号 (如 5800.123)
    lateral: float = 0          # 横距
    elevation: float = 0        # 高程
    geom: Optional[str] = None  # PostGIS几何


@dataclass
class EngineeringEntity:
    """工程实体"""
    id: UUID = field(default_factory=uuid4)
    project_id: UUID = None
    type: EntityType = EntityType.SUBGRADE
    code: str = ""              # 如 PAV-K5600-K6200
    station_start: float = 0
    station_end: float = 0
    lateral_min: float = 0
    lateral_max: float = 0
    elev_min: float = 0
    elev_max: float = 0
    attributes: Dict = field(default_factory=dict)  # JSONB
    lod_level: int = 1


@dataclass
class EntityState:
    """实体状态快照"""
    id: UUID = field(default_factory=uuid4)
    entity_id: UUID = None
    snapshot_time: datetime = field(default_factory=datetime.now)
    version_type: VersionType = VersionType.DESIGNED
    progress: float = 0         # 0-100
    spatial_snapshot: Dict = field(default_factory=dict)
    attribute_snapshot: Dict = field(default_factory=dict)
    delta: Dict = field(default_factory=dict)
    photos: List[UUID] = field(default_factory=list)
    issues: List[UUID] = field(default_factory=list)
    hash: str = ""
    created_by: str = ""
    
    def compute_hash(self):
        """计算哈希用于区块链存证"""
        data = {
            'entity_id': str(self.entity_id),
            'snapshot_time': self.snapshot_time.isoformat(),
            'version_type': self.version_type.value,
            'progress': self.progress,
            'spatial_snapshot': self.spatial_snapshot,
            'attribute_snapshot': self.attribute_snapshot
        }
        json_str = json.dumps(data, sort_keys=True)
        self.hash = hashlib.sha256(json_str.encode()).hexdigest()
        return self.hash


@dataclass
class StateEvent:
    """状态事件"""
    id: UUID = field(default_factory=uuid4)
    project_id: UUID = None
    event_type: EventType = EventType.WEATHER
    station_start: Optional[float] = None
    station_end: Optional[float] = None
    data: Dict = field(default_factory=dict)  # 如 {"rainfall_mm": 120}
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    affected_entities: List[UUID] = field(default_factory=list)
    resolved: bool = False


@dataclass
class ProcessData:
    """过程数据（照片/日志）"""
    id: UUID = field(default_factory=uuid4)
    entity_id: UUID = None
    photo_url: str = ""
    station: Optional[float] = None
    spatial_ref: UUID = None
    ai_tags: Dict = field(default_factory=dict)
    offline_synced: bool = False
    uploaded_at: datetime = field(default_factory=datetime.now)


class SpacetimeDB:
    """时空数据库（内存实现，可对接PostgreSQL）"""
    
    def __init__(self):
        self.projects: Dict[UUID, Project] = {}
        self.spatial_controls: Dict[UUID, SpatialControl] = {}
        self.entities: Dict[UUID, EngineeringEntity] = {}
        self.states: Dict[UUID, List[EntityState]] = {}  # entity_id -> states
        self.events: List[StateEvent] = []
        self.process_data: Dict[UUID, List[ProcessData]] = {}
    
    def create_project(self, name: str) -> Project:
        """创建项目"""
        project = Project(name=name)
        self.projects[project.id] = project
        return project
    
    def add_spatial_control(self, project_id: UUID, station: float, 
                           lateral: float = 0, elevation: float = 0) -> SpatialControl:
        """添加空间控制点"""
        sc = SpatialControl(
            project_id=project_id,
            station=station,
            lateral=lateral,
            elevation=elevation
        )
        self.spatial_controls[sc.id] = sc
        return sc
    
    def add_entity(self, project_id: UUID, entity_type: EntityType, 
                  code: str, station_start: float, station_end: float,
                  attributes: Dict = None) -> EngineeringEntity:
        """添加工程实体"""
        entity = EngineeringEntity(
            project_id=project_id,
            type=entity_type,
            code=code,
            station_start=station_start,
            station_end=station_end,
            attributes=attributes or {}
        )
        self.entities[entity.id] = entity
        self.states[entity.id] = []
        return entity
    
    def add_state(self, entity_id: UUID, version_type: VersionType,
                 progress: float, spatial: Dict = None,
                 attributes: Dict = None, created_by: str = "") -> EntityState:
        """添加实体状态"""
        state = EntityState(
            entity_id=entity_id,
            version_type=version_type,
            progress=progress,
            spatial_snapshot=spatial or {},
            attribute_snapshot=attributes or {},
            created_by=created_by
        )
        state.compute_hash()
        
        if entity_id in self.states:
            self.states[entity_id].append(state)
        else:
            self.states[entity_id] = [state]
        
        return state
    
    def get_latest_state(self, entity_id: UUID) -> Optional[EntityState]:
        """获取最新状态"""
        if entity_id in self.states and self.states[entity_id]:
            return self.states[entity_id][-1]
        return None
    
    def find_entity_at(self, station: float, lateral: float = 0, elevation: float = 0) -> Optional[EngineeringEntity]:
        """查找指定位置的实体"""
        for entity in self.entities.values():
            if (entity.station_start <= station <= entity.station_end and
                entity.lateral_min <= lateral <= entity.lateral_max):
                return entity
        return None
    
    def add_event(self, project_id: UUID, event_type: EventType,
                 station_start: float = None, station_end: float = None,
                 data: Dict = None) -> StateEvent:
        """添加事件"""
        event = StateEvent(
            project_id=project_id,
            event_type=event_type,
            station_start=station_start,
            station_end=station_end,
            data=data or {},
            start_time=datetime.now()
        )
        self.events.append(event)
        return event
    
    def add_process_data(self, entity_id: UUID, photo_url: str,
                        station: float = None, ai_tags: Dict = None) -> ProcessData:
        """添加过程数据"""
        pd = ProcessData(
            entity_id=entity_id,
            photo_url=photo_url,
            station=station,
            ai_tags=ai_tags or {}
        )
        
        if entity_id in self.process_data:
            self.process_data[entity_id].append(pd)
        else:
            self.process_data[entity_id] = [pd]
        
        return pd
    
    def realtime_query(self, station: float, lateral: float = 0) -> Dict:
        """实时查询"""
        entity = self.find_entity_at(station, lateral)
        if not entity:
            return {"status": "empty", "station": station}
        
        latest_state = self.get_latest_state(entity.id)
        
        # 获取该实体的过程数据
        photos = []
        if entity.id in self.process_data:
            photos = [pd.photo_url for pd in self.process_data[entity.id][-5:]]
        
        return {
            "status": "found",
            "location": {
                "station": station,
                "lateral": lateral
            },
            "entity": {
                "id": str(entity.id),
                "code": entity.code,
                "type": entity.type.value,
                "station_range": f"{entity.station_start}-{entity.station_end}"
            },
            "current_state": {
                "version_type": latest_state.version_type.value if latest_state else None,
                "progress": latest_state.progress if latest_state else 0,
                "hash": latest_state.hash if latest_state else None
            } if latest_state else None,
            "recent_photos": photos
        }


# 测试
if __name__ == "__main__":
    db = SpacetimeDB()
    
    # 创建项目
    project = db.create_project("京沪高速拓宽工程")
    print(f"Project: {project.name}")
    
    # 添加空间控制点
    for i in range(5):
        db.add_spatial_control(project.id, 5000 + i * 100, elevation=100 + i * 5)
    
    # 添加实体
    pavement = db.add_entity(
        project.id, 
        EntityType.PAVEMENT,
        "PAV-K5000-K5500",
        5000, 5500,
        {"material": "C30", "design_thickness": 0.36}
    )
    print(f"Entity: {pavement.code}")
    
    # 添加设计状态
    db.add_state(
        pavement.id,
        VersionType.DESIGNED,
        100,
        {"coverage": 1.0},
        [{"name": "基层", "status": "completed", "thickness": 0.36}]
    )
    
    # 添加实际状态
    db.add_state(
        pavement.id,
        VersionType.ACTUAL,
        85,
        {"coverage": 0.85},
        [{"name": "基层", "status": "completed", "thickness": 0.36}],
        "worker_zhang"
    )
    
    # 查询
    result = db.realtime_query(5200)
    print(f"\nRealtime Query (K5+200):")
    print(f"  Status: {result['status']}")
    print(f"  Entity: {result.get('entity', {}).get('code')}")
    print(f"  Progress: {result.get('current_state', {}).get('progress')}%")
    print(f"  Hash: {result.get('current_state', {}).get('hash', '')[:16]}...")
