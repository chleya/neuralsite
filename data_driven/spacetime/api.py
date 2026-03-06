# -*- coding: utf-8 -*-
"""
时空状态管理 - API接口
基于规格书V1.0
"""
from typing import Dict, List, Optional, Any
from uuid import UUID
import json

from .models import (
    SpacetimeDB, Project, SpatialControl, EngineeringEntity,
    EntityState, StateEvent, ProcessData,
    EntityType, VersionType, EventType
)


class SpacetimeAPI:
    """时空状态管理API"""
    
    def __init__(self, db: SpacetimeDB = None):
        self.db = db or SpacetimeDB()
    
    # ========== 项目管理 ==========
    
    def create_project(self, name: str, description: str = "") -> Dict:
        """创建项目"""
        project = self.db.create_project(name)
        return {
            "id": str(project.id),
            "name": project.name,
            "created_at": project.created_at.isoformat()
        }
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """获取项目"""
        try:
            proj = self.db.projects[UUID(project_id)]
            return {
                "id": str(proj.id),
                "name": proj.name,
                "created_at": proj.created_at.isoformat()
            }
        except:
            return None
    
    # ========== 空间控制点 ==========
    
    def add_spatial_control(self, project_id: str, station: float, 
                           lateral: float = 0, elevation: float = 0) -> Dict:
        """添加空间控制点"""
        sc = self.db.add_spatial_control(
            UUID(project_id), station, lateral, elevation
        )
        return {
            "id": str(sc.id),
            "station": sc.station,
            "lateral": sc.lateral,
            "elevation": sc.elevation
        }
    
    # ========== 工程实体 ==========
    
    def create_entity(self, project_id: str, entity_type: str,
                     code: str, station_start: float, station_end: float,
                     attributes: Dict = None) -> Dict:
        """创建工程实体"""
        et = EntityType(entity_type)
        entity = self.db.add_entity(
            UUID(project_id), et, code, station_start, station_end, attributes
        )
        return {
            "id": str(entity.id),
            "code": entity.code,
            "type": entity.type.value,
            "station_range": f"{station_start}-{station_end}"
        }
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """获取实体"""
        try:
            e = self.db.entities[UUID(entity_id)]
            return {
                "id": str(e.id),
                "code": e.code,
                "type": e.type.value,
                "station_start": e.station_start,
                "station_end": e.station_end,
                "attributes": e.attributes
            }
        except:
            return None
    
    # ========== 状态管理 ==========
    
    def add_state(self, entity_id: str, version_type: str, progress: float,
                  spatial: Dict = None, attributes: Dict = None,
                  created_by: str = "") -> Dict:
        """添加实体状态"""
        vt = VersionType(version_type)
        state = self.db.add_state(
            UUID(entity_id), vt, progress, spatial, attributes, created_by
        )
        return {
            "id": str(state.id),
            "version_type": state.version_type.value,
            "progress": state.progress,
            "hash": state.hash,
            "snapshot_time": state.snapshot_time.isoformat()
        }
    
    def get_latest_state(self, entity_id: str) -> Optional[Dict]:
        """获取最新状态"""
        state = self.db.get_latest_state(UUID(entity_id))
        if not state:
            return None
        
        return {
            "id": str(state.id),
            "version_type": state.version_type.value,
            "progress": state.progress,
            "spatial_snapshot": state.spatial_snapshot,
            "attribute_snapshot": state.attribute_snapshot,
            "hash": state.hash,
            "snapshot_time": state.snapshot_time.isoformat()
        }
    
    # ========== 实时查询（核心功能） ==========
    
    def realtime_query(self, station: float, lateral: float = 0) -> Dict:
        """
        实时查询指定位置的实体和状态
        对应规格书中的 realtime_query 函数
        """
        return self.db.realtime_query(station, lateral)
    
    def query_by_entity(self, entity_id: str) -> Dict:
        """按实体ID查询"""
        entity = self.db.entities.get(UUID(entity_id))
        if not entity:
            return {"status": "not_found"}
        
        latest_state = self.db.get_latest_state(entity.id)
        
        # 获取过程数据
        photos = []
        if entity.id in self.db.process_data:
            photos = [
                {"photo_url": pd.photo_url, "uploaded_at": pd.uploaded_at.isoformat()}
                for pd in self.db.process_data[entity.id][-5:]
            ]
        
        # 获取问题
        # TODO: 从issues表查询
        
        return {
            "status": "found",
            "entity": {
                "id": str(entity.id),
                "code": entity.code,
                "type": entity.type.value,
                "station_range": f"{entity.station_start}-{entity.station_end}",
                "attributes": entity.attributes
            },
            "current_state": {
                "version_type": latest_state.version_type.value if latest_state else None,
                "progress": latest_state.progress if latest_state else 0,
                "spatial_snapshot": latest_state.spatial_snapshot if latest_state else {},
                "attribute_snapshot": latest_state.attribute_snapshot if latest_state else {},
                "hash": latest_state.hash if latest_state else None
            } if latest_state else None,
            "recent_photos": photos
        }
    
    # ========== 状态模拟 ==========
    
    def simulate_future(self, entity_id: str, target_version_type: str = "designed") -> Dict:
        """
        模拟未来状态
        对应规格书中的 simulate_future 函数
        """
        entity = self.db.entities.get(UUID(entity_id))
        if not entity:
            return {"status": "not_found"}
        
        current = self.db.get_latest_state(entity.id)
        if not current:
            return {"status": "no_current_state"}
        
        # 目标进度
        target_progress = 100 if target_version_type == "designed" else 0
        
        # 生成30帧动画
        frames = []
        for i in range(31):
            ratio = i / 30
            progress = current.progress + (target_progress - current.progress) * ratio
            
            # 简单的空间插值
            spatial = {}
            if current.spatial_snapshot:
                for k, v in current.spatial_snapshot.items():
                    if isinstance(v, (int, float)):
                        target_v = v * (target_progress / current.progress) if current.progress > 0 else 0
                        spatial[k] = v + (target_v - v) * ratio
                    else:
                        spatial[k] = v
            
            frames.append({
                "frame": i,
                "progress": round(progress, 2),
                "spatial": spatial
            })
        
        return {
            "entity_id": entity_id,
            "current": {
                "progress": current.progress,
                "version_type": current.version_type.value
            },
            "target": {
                "version_type": target_version_type,
                "progress": target_progress
            },
            "animation_frames": frames
        }
    
    # ========== 事件管理 ==========
    
    def add_event(self, project_id: str, event_type: str,
                 station_start: float = None, station_end: float = None,
                 data: Dict = None) -> Dict:
        """添加事件"""
        et = EventType(event_type)
        event = self.db.add_event(
            UUID(project_id), et, station_start, station_end, data
        )
        return {
            "id": str(event.id),
            "event_type": event.event_type.value,
            "station_range": f"{station_start}-{station_end}" if station_start else None,
            "data": event.data,
            "start_time": event.start_time.isoformat() if event.start_time else None
        }
    
    # ========== 过程数据 ==========
    
    def add_photo(self, entity_id: str, photo_url: str,
                  station: float = None, ai_tags: Dict = None) -> Dict:
        """添加照片"""
        pd = self.db.add_process_data(
            UUID(entity_id), photo_url, station, ai_tags
        )
        return {
            "id": str(pd.id),
            "photo_url": pd.photo_url,
            "station": pd.station,
            "ai_tags": pd.ai_tags,
            "uploaded_at": pd.uploaded_at.isoformat()
        }
    
    # ========== 区块链存证 ==========
    
    def verify_hash(self, state_id: str) -> Dict:
        """验真哈希"""
        state = None
        for states in self.db.states.values():
            for s in states:
                if str(s.id) == state_id:
                    state = s
                    break
        
        if not state:
            return {"status": "not_found", "verified": False}
        
        # 重新计算哈希
        expected_hash = state.compute_hash()
        
        return {
            "status": "verified",
            "match": state.hash == expected_hash,
            "stored_hash": state.hash,
            "computed_hash": expected_hash
        }


# 测试
if __name__ == "__main__":
    api = SpacetimeAPI()
    
    # 创建项目
    project = api.create_project("测试项目")
    print(f"Project: {project}")
    
    # 添加实体
    entity = api.create_entity(
        project["id"], 
        "pavement",
        "PAV-K5000-K5500",
        5000, 5500,
        {"material": "C30", "thickness": 0.36}
    )
    print(f"Entity: {entity}")
    
    # 添加状态
    state = api.add_state(
        entity["id"],
        "actual",
        85,
        {"coverage": 0.85},
        {"layers": [{"name": "基层", "status": "completed"}]},
        "worker_zhang"
    )
    print(f"State: {state}")
    
    # 实时查询
    result = api.realtime_query(5200)
    print(f"\nRealtime Query K5+200:")
    print(f"  Status: {result['status']}")
    if result['status'] == 'found':
        print(f"  Entity: {result['entity']['code']}")
        print(f"  Progress: {result['current_state']['progress']}%")
    
    # 模拟
    sim = api.simulate_future(entity["id"])
    print(f"\nSimulation:")
    print(f"  Frames: {len(sim['animation_frames'])}")
    print(f"  Frame 15: {sim['animation_frames'][15]}")
