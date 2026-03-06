"""
NeuralSite 4D Service - FastAPI Router
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
from datetime import datetime
import json

from .models import Schedule4DResponse, EventInput
from .service import get_4d_service

router = APIRouter(prefix="/api/v1/4d", tags=["4D施工模拟"])


@router.get("/schedule")
async def get_schedule(
    project_id: str = Query("default", description="项目ID"),
    date: Optional[str] = Query(None, description="查询日期 YYYY-MM-DD")
):
    """
    获取4D调度数据
    """
    service = get_4d_service()
    data = service.get_schedule(project_id, date)
    return data


@router.get("/schedule/at/{date}")
async def get_schedule_at_date(
    date: str,
    project_id: str = Query("default")
):
    """
    获取指定日期的施工状态
    """
    service = get_4d_service()
    data = service.get_schedule(project_id, date)
    return data


@router.post("/event")
async def add_event(event: EventInput):
    """
    添加施工事件（开工/完工/延期/问题）
    """
    service = get_4d_service()
    result = service.add_event(
        entity_id=event.entity_id,
        entity_type=event.entity_type,
        event_type=event.event_type,
        event_data=event.event_data,
        occurred_at=event.occurred_at
    )
    return result


@router.get("/tasks")
async def get_tasks(
    project_id: str = Query("default"),
    date: Optional[str] = Query(None)
):
    """
    获取任务列表
    """
    service = get_4d_service()
    schedule = service.get_schedule(project_id, date)
    return {
        "tasks": schedule.get("tasks", []),
        "count": len(schedule.get("tasks", []))
    }


@router.get("/progress")
async def get_progress(
    project_id: str = Query("default"),
    date: Optional[str] = Query(None)
):
    """
    获取总体进度
    """
    service = get_4d_service()
    if date:
        status = service.events_gen.get_status_at_date(date)
    else:
        schedule = service.generate_schedule()
        tasks = schedule.get("tasks", [])
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        total = len(tasks)
        progress = int((completed / total) * 100) if total > 0 else 0
        status = {
            "overall_progress": progress,
            "completed": completed,
            "total": total
        }
    return status


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)
    
    async def broadcast(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket实时推送"""
    await manager.connect(websocket, project_id)
    try:
        while True:
            # 保持连接，可以接收前端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理前端消息
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "get_schedule":
                service = get_4d_service()
                schedule = service.get_schedule(project_id)
                await websocket.send_json({"type": "schedule", "data": schedule})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
