# -*- coding: utf-8 -*-
"""
REST API 实现
基于FastAPI的数据接口服务
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# 导入数据模型
from .models import (
    Project, ProjectCreate, ProjectResponse,
    SpatialStation, SpatialStationResponse,
    ChainRecord, ChainRecordCreate, ChainRecordResponse,
    Entity, EntityResponse,
    Photo, PhotoCreate, PhotoResponse,
    Issue, IssueCreate, IssueResponse
)

# 导入区块链模块
try:
    from data_driven.blockchain import (
        HashComputer, ChainVerifier, MockChainStorage
    )
except ImportError:
    # 尝试neuralsite前缀
    try:
        from neuralsite.data_driven.blockchain import (
            HashComputer, ChainVerifier, MockChainStorage
        )
    except ImportError:
        # 使用本地模拟
        import uuid
        from datetime import datetime
        
        class HashComputer:
            @staticmethod
            def compute_data_hash(data, data_type):
                import hashlib
                import json
                normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
                return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        
        class MockChainStorage:
            def __init__(self):
                self._records = {}
            def save(self, record):
                record["chain_id"] = record.get("chain_id") or str(uuid.uuid4())
                self._records[record["chain_id"]] = record
            def get_by_data_id(self, data_id):
                for r in self._records.values():
                    if r.get("data_id") == data_id:
                        return r
                return None
            def get_history(self, data_id):
                return [r for r in self._records.values() if r.get("data_id") == data_id]
        
        class ChainVerifier:
            def __init__(self, storage):
                self.storage = storage
            def verify(self, data_id, current_hash):
                record = self.storage.get_by_data_id(data_id)
                if not record:
                    return type('obj', (object,), {"is_verified": False, "message": "No record"})()
                is_verified = record.get("data_hash") == current_hash
                return type('obj', (object,), {
                    "is_verified": is_verified,
                    "chain_record": record,
                    "message": "Verified" if is_verified else "Mismatch"
                })()
            def get_history(self, data_id):
                return self.storage.get_history(data_id)
        
        MockChainStorage = MockChainStorage

# 导入几何引擎
try:
    from packages.core.core.geometry import HorizontalAlignment
    GEOMETRY_AVAILABLE = True
except ImportError:
    try:
        from neuralsite.packages.core.core.geometry import HorizontalAlignment
        GEOMETRY_AVAILABLE = True
    except ImportError:
        GEOMETRY_AVAILABLE = False

# 创建路由器
router = APIRouter(prefix="/api/v1/data", tags=["数据接口"])

# 模拟数据存储（实际应使用数据库）
_projects_db: Dict[str, Dict] = {}
_entities_db: Dict[str, Dict] = {}
_photos_db: Dict[str, Dict] = {}
_issues_db: Dict[str, Dict] = {}
_chain_records_db = MockChainStorage()

# 模拟空间数据（实际应从数据库加载）
_STATION_COORDS = {
    "K0+000": {"easting": 500000.0, "northing": 3500000.0, "elevation": 100.0},
    "K0+100": {"easting": 500100.0, "northing": 3500100.0, "elevation": 101.0},
    "K0+200": {"easting": 500200.0, "northing": 3500200.0, "elevation": 102.0},
    "K0+300": {"easting": 500300.0, "northing": 3500300.0, "elevation": 103.0},
    "K0+400": {"easting": 500400.0, "northing": 3500400.0, "elevation": 104.0},
    "K0+500": {"easting": 500500.0, "northing": 3500500.0, "elevation": 105.0},
}


# ==================== 项目接口 ====================

@router.get("/projects", response_model=Dict)
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="项目名称筛选")
) -> Dict[str, Any]:
    """
    获取项目列表
    
    支持分页和名称筛选
    """
    # 筛选项目
    projects = list(_projects_db.values())
    if name:
        projects = [p for p in projects if name.lower() in p.get("name", "").lower()]
    
    # 分页
    total = len(projects)
    start = (page - 1) * page_size
    end = start + page_size
    items = projects[start:end]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.post("/projects", response_model=Dict)
async def create_project(project: ProjectCreate) -> Dict[str, Any]:
    """
    创建新项目
    """
    project_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    project_data = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "status": project.status or "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    _projects_db[project_id] = project_data
    
    return {
        "id": project_id,
        "created_at": now.isoformat()
    }


@router.get("/projects/{project_id}", response_model=Dict)
async def get_project(project_id: str) -> Dict[str, Any]:
    """获取项目详情"""
    project = _projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}", response_model=Dict)
async def update_project(project_id: str, project: ProjectCreate) -> Dict[str, Any]:
    """更新项目"""
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    now = datetime.utcnow()
    _projects_db[project_id].update({
        "name": project.name,
        "description": project.description,
        "status": project.status or "active",
        "updated_at": now.isoformat()
    })
    
    return _projects_db[project_id]


# ==================== 空间数据接口 ====================

@router.get("/spatial/stations", response_model=Dict)
async def list_stations(
    project_id: Optional[str] = Query(None, description="项目ID"),
    start: Optional[str] = Query(None, description="起始桩号"),
    end: Optional[str] = Query(None, description="结束桩号")
) -> Dict[str, Any]:
    """
    获取桩号列表
    """
    stations = []
    for station, coords in _STATION_COORDS.items():
        # 简单过滤（实际应解析桩号进行比较）
        if start and station < start:
            continue
        if end and station > end:
            continue
        
        stations.append({
            "station": station,
            **coords
        })
    
    return {
        "items": stations,
        "total": len(stations)
    }


@router.get("/spatial/stations/{station}/coordinates", response_model=Dict)
async def get_station_coordinates(station: str) -> Dict[str, Any]:
    """
    获取桩号对应坐标
    
    调用几何引擎计算精确坐标
    """
    # 先检查预定义数据
    if station in _STATION_COORDS:
        return {
            "station": station,
            **_STATION_COORDS[station]
        }
    
    # 如果几何引擎可用，尝试计算
    if GEOMETRY_AVAILABLE:
        # TODO: 使用HorizontalAlignment计算
        raise HTTPException(status_code=501, detail="Geometry calculation not implemented")
    
    raise HTTPException(status_code=404, detail=f"Station {station} not found")


@router.get("/spatial/coordinates/nearest", response_model=Dict)
async def get_nearest_station(
    easting: float = Query(..., description="东坐标"),
    northing: float = Query(..., description="北坐标"),
    max_distance: float = Query(100, ge=0, description="最大搜索距离(米)")
) -> Dict[str, Any]:
    """
    根据坐标获取最近桩号
    
    使用欧氏距离计算最近桩号
    """
    import math
    
    min_distance = float('inf')
    nearest_station = None
    nearest_coords = None
    
    for station, coords in _STATION_COORDS.items():
        dx = coords["easting"] - easting
        dy = coords["northing"] - northing
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
            nearest_coords = coords
    
    if nearest_station is None or min_distance > max_distance:
        raise HTTPException(
            status_code=404, 
            detail=f"No station found within {max_distance}m"
        )
    
    return {
        "station": nearest_station,
        "distance": round(min_distance, 2),
        **nearest_coords
    }


# ==================== 工程实体接口 ====================

@router.get("/entities", response_model=Dict)
async def list_entities(
    project_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """获取实体列表"""
    entities = list(_entities_db.values())
    if project_id:
        entities = [e for e in entities if e.get("project_id") == project_id]
    
    total = len(entities)
    start = (page - 1) * page_size
    items = entities[start:start + page_size]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }


@router.get("/entities/{entity_id}", response_model=Dict)
async def get_entity(entity_id: str) -> Dict[str, Any]:
    """获取实体详情"""
    entity = _entities_db.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities/by-station/{station}", response_model=Dict)
async def get_entity_by_station(station: str) -> Dict[str, Any]:
    """按桩号查询实体"""
    entities = [
        e for e in _entities_db.values() 
        if e.get("station") == station
    ]
    return {
        "station": station,
        "entities": entities,
        "count": len(entities)
    }


# ==================== 照片数据接口 ====================

@router.post("/photos", response_model=Dict)
async def upload_photo(photo: PhotoCreate) -> Dict[str, Any]:
    """上传照片"""
    photo_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    photo_data = {
        "id": photo_id,
        "entity_id": photo.entity_id,
        "station": photo.station,
        "filename": photo.filename,
        "file_path": photo.file_path,
        "uploaded_at": now.isoformat(),
        "verified": False
    }
    
    _photos_db[photo_id] = photo_data
    
    return {
        "id": photo_id,
        "uploaded_at": now.isoformat()
    }


@router.get("/photos", response_model=Dict)
async def list_photos(
    entity_id: Optional[str] = Query(None),
    station: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """查询照片列表"""
    photos = list(_photos_db.values())
    
    if entity_id:
        photos = [p for p in photos if p.get("entity_id") == entity_id]
    if station:
        photos = [p for p in photos if p.get("station") == station]
    if verified is not None:
        photos = [p for p in photos if p.get("verified") == verified]
    
    total = len(photos)
    start = (page - 1) * page_size
    items = photos[start:start + page_size]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }


@router.get("/photos/{photo_id}", response_model=Dict)
async def get_photo(photo_id: str) -> Dict[str, Any]:
    """获取照片详情"""
    photo = _photos_db.get(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.post("/photos/{photo_id}/verify", response_model=Dict)
async def verify_photo(photo_id: str, confirmation: Dict) -> Dict[str, Any]:
    """人工确认照片"""
    if photo_id not in _photos_db:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    now = datetime.utcnow()
    _photos_db[photo_id].update({
        "verified": True,
        "verified_by": confirmation.get("confirmed_by", "unknown"),
        "verified_at": now.isoformat(),
        "notes": confirmation.get("notes", "")
    })
    
    # 同时创建区块链存证
    record_data = {
        "data_id": photo_id,
        "data_type": "quality_confirmation",
        "confirmation_id": str(uuid.uuid4()),
        "issue_id": _photos_db[photo_id].get("entity_id"),
        "confirmed_by": confirmation.get("confirmed_by", "unknown"),
        "result": "verified",
        "confirmed_at": now.isoformat()
    }
    
    data_hash = HashComputer.compute_data_hash(record_data, "quality_confirmation")
    chain_record = {
        "data_id": photo_id,
        "data_hash": data_hash,
        "record_data": record_data,
        "created_at": now.isoformat()
    }
    _chain_records_db.save(chain_record)
    
    return {
        "verified": True,
        "chain_record_id": chain_record.get("chain_id"),
        "verified_at": now.isoformat()
    }


# ==================== 问题跟踪接口 ====================

@router.post("/issues", response_model=Dict)
async def create_issue(issue: IssueCreate) -> Dict[str, Any]:
    """创建问题"""
    issue_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    issue_data = {
        "id": issue_id,
        "station": issue.station,
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "description": issue.description,
        "status": "open",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    _issues_db[issue_id] = issue_data
    
    return {
        "id": issue_id,
        "created_at": now.isoformat()
    }


@router.get("/issues", response_model=Dict)
async def list_issues(
    status: Optional[str] = Query(None, description="问题状态"),
    severity: Optional[str] = Query(None, description="严重级别"),
    station: Optional[str] = Query(None, description="桩号"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """查询问题列表"""
    issues = list(_issues_db.values())
    
    if status:
        issues = [i for i in issues if i.get("status") == status]
    if severity:
        issues = [i for i in issues if i.get("severity") == severity]
    if station:
        issues = [i for i in issues if i.get("station") == station]
    
    total = len(issues)
    start = (page - 1) * page_size
    items = issues[start:start + page_size]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }


@router.put("/issues/{issue_id}/status", response_model=Dict)
async def update_issue_status(issue_id: str, status_update: Dict) -> Dict[str, Any]:
    """更新问题状态"""
    if issue_id not in _issues_db:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    now = datetime.utcnow()
    new_status = status_update.get("status")
    
    if new_status not in ["open", "in_progress", "resolved", "closed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    _issues_db[issue_id].update({
        "status": new_status,
        "updated_at": now.isoformat(),
        "resolution_notes": status_update.get("notes", "")
    })
    
    return _issues_db[issue_id]


# ==================== 区块链接口 ====================

@router.post("/chain/record", response_model=Dict)
async def submit_chain_record(record: ChainRecordCreate) -> Dict[str, Any]:
    """
    提交存证
    
    计算数据哈希并存储到链上
    """
    now = datetime.utcnow()
    
    # 计算数据哈希
    data_hash = HashComputer.compute_data_hash(record.data, record.data_type)
    
    # 创建存证记录
    chain_record = {
        "data_id": record.data_id or str(uuid.uuid4()),
        "data_type": record.data_type,
        "data_hash": data_hash,
        "record_data": record.data,
        "operator": record.operator,
        "created_at": now.isoformat()
    }
    
    # 保存到存储
    _chain_records_db.save(chain_record)
    
    return {
        "id": chain_record.get("chain_id"),
        "data_id": chain_record["data_id"],
        "data_hash": data_hash,
        "created_at": now.isoformat()
    }


@router.get("/chain/verify/{data_id}", response_model=Dict)
async def verify_chain_record(
    data_id: str, 
    current_hash: str = Query(..., description="当前数据哈希")
) -> Dict[str, Any]:
    """
    验真数据
    
    比对当前数据哈希与链上存储的哈希
    """
    verifier = ChainVerifier(_chain_records_db)
    result = verifier.verify(data_id, current_hash)
    
    return {
        "verified": result.is_verified,
        "message": result.message,
        "chain_record": result.chain_record
    }


@router.get("/chain/history/{data_id}", response_model=Dict)
async def get_chain_history(data_id: str) -> Dict[str, Any]:
    """获取存证历史"""
    verifier = ChainVerifier(_chain_records_db)
    return verifier.get_history(data_id)


# ==================== AI问答接口 ====================

@router.post("/qa/query", response_model=Dict)
async def query_qa(question: Dict) -> Dict[str, Any]:
    """
    知识问答
    
    TODO: 实现完整的问答系统
    """
    return {
        "answer": "QA system not fully implemented",
        "question": question.get("question"),
        "confidence": 0.0
    }


@router.post("/qa/drawing-query", response_model=Dict)
async def query_drawing(query: Dict) -> Dict[str, Any]:
    """
    图纸语义查询
    
    TODO: 实现图纸问答系统
    """
    return {
        "answer": "Drawing query system not fully implemented",
        "query": query.get("query"),
        "drawings": []
    }


# ==================== 依赖注入 ====================

def get_projects_db() -> Dict[str, Dict]:
    """获取项目数据库"""
    return _projects_db


def get_chain_storage():
    """获取区块链存储"""
    return _chain_records_db


# ==================== 路由创建（兼容旧接口） ====================

def create_rest_routes() -> List[Dict[str, Any]]:
    """
    创建REST路由定义（兼容旧接口）
    
    Returns:
        路由定义列表
    """
    routes = []
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "method": list(route.methods)[0] if route.methods else "GET",
                "description": route.summary or "",
                "handler": route.name
            })
    return routes
