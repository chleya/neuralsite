"""
NeuralSite 4D Service
施工进度4D模拟服务

快速开始:
    from packages.4d_service.router import router
    app.include_router(router)

API端点:
    GET  /api/v1/4d/schedule - 获取4D调度
    GET  /api/v1/4d/schedule/at/{date} - 指定日期状态
    POST /api/v1/4d/event - 添加施工事件
    GET  /api/v1/4d/tasks - 任务列表
    GET  /api/v1/4d/progress - 总体进度
    WS   /api/v1/4d/ws/{project_id} - WebSocket实时推送
"""
from .router import router
from .service import get_4d_service, FourDService
from .models import Task4D, Project4D, Schedule4DResponse, EventInput

__all__ = [
    "router",
    "get_4d_service",
    "FourDService",
    "Task4D",
    "Project4D", 
    "Schedule4DResponse",
    "EventInput",
]
