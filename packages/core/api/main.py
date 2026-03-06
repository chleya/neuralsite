# -*- coding: utf-8 -*-
"""
NeuralSite Core API
FastAPI入口
"""

from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from api.v1.routes import calculate
from api.v1.routes.knowledge import router as knowledge_router
from api.v1.routes.lod import router as lod_router
from api.v1.routes.engineering import router as engineering_router
from api.v1.routes.import_routes import router as import_router
from api.v1.routes.workflow import router as workflow_router
from api.v1.routes.advisor import router as advisor_router
from api.v1.routes.spatial import router as spatial_router

# 新增V1路由
from api.v1.routes.spatial_v1 import router as spatial_v1_router
from api.v1.routes.knowledge_v1 import router as knowledge_v1_router
from api.v1.routes.dashboard_v1 import router as dashboard_router
from api.v1.routes.stations import router as stations_router
from api.v1.routes.cross_sections import router as cross_sections_router
from api.v1.routes.spatial_api import router as spatial_api_router
from api.v1.routes.qa_api import router as qa_router
from core.ai_detection.api import router as ai_detection_router

# P0路由 (照片管理+问题跟踪+离线同步)
try:
    from api.v1.p0_routes import router as p0_router
    P0_ROUTES_AVAILABLE = True
except ImportError:
    P0_ROUTES_AVAILABLE = False

# Project & Route API
try:
    from api.v1.projects import router as projects_router
    from api.v1.route_api import router as routes_router
    PROJECT_ROUTES_AVAILABLE = True
except ImportError as e:
    PROJECT_ROUTES_AVAILABLE = False
    print(f"Project routes not available: {e}")

# 依赖注入
from api.dependencies import get_feature_flags, get_settings

# 监控指标
from core.monitoring import get_metrics


# 创建应用
app = FastAPI(
    title="NeuralSite Core API",
    description="公路参数化建模系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - 生产环境应配置具体域名
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(calculate.router)
app.include_router(knowledge_router)
app.include_router(lod_router)
app.include_router(engineering_router)
app.include_router(import_router)
app.include_router(workflow_router)
app.include_router(advisor_router)
app.include_router(spatial_router)

# 注册V1路由
app.include_router(spatial_v1_router)
app.include_router(knowledge_v1_router)
app.include_router(dashboard_router)
app.include_router(stations_router)
app.include_router(cross_sections_router)
app.include_router(spatial_api_router)
app.include_router(qa_router)
app.include_router(ai_detection_router)

# 注册P0路由 (照片管理+问题跟踪+离线同步)
if P0_ROUTES_AVAILABLE:
    app.include_router(p0_router)
    print("P0 routes registered")

# 注册Project & Route路由
if PROJECT_ROUTES_AVAILABLE:
    app.include_router(projects_router)
    app.include_router(routes_router)
    print("Project & Route routes registered")


@app.get("/")
async def root():
    return {
        "name": "NeuralSite Core API",
        "version": "1.0.0",
        "description": "公路参数化建模系统",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check(
    feature_flags = Depends(get_feature_flags),
    settings = Depends(get_settings)
):
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": feature_flags.get_all(),
        "config": {
            "api_host": settings.get("api_host"),
            "api_port": settings.get("api_port"),
        }
    }


@app.get("/features")
async def list_features(feature_flags = Depends(get_feature_flags)):
    """列出所有特性开关"""
    return {
        "features": feature_flags.get_all()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus 监控指标端点"""
    return Response(content=get_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
