"""
NeuralSite 4D Service - Pydantic Models
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class Task4D(BaseModel):
    """单个施工任务"""
    id: str
    name: str
    start: Optional[str] = None
    end: Optional[str] = None
    duration_days: int = 0
    status: str = "pending"  # pending / active / completed / delayed
    progress: int = 0
    entity_type: Optional[str] = None


class Project4D(BaseModel):
    """项目信息"""
    name: str
    schema: Optional[str] = None


class Schedule4DResponse(BaseModel):
    """4D调度响应"""
    project: Project4D
    current_date: str
    tasks: List[Task4D]
    overall_progress: int
    gantt: List[dict] = []
    generated_at: str


class EventInput(BaseModel):
    """事件输入"""
    entity_id: str
    entity_type: str
    event_type: str  # start / complete / delay / issue
    event_data: dict = {}
    occurred_at: str


class ScheduleQuery(BaseModel):
    """调度查询"""
    project_id: str = "default"
    date: Optional[str] = None
