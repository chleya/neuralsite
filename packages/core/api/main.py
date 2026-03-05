# -*- coding: utf-8 -*-
"""
NeuralSite Core API
FastAPI入口
"""

from fastapi import FastAPI, Depends
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
from core.ai_detection.api import router as ai_detection_router

# 依赖注入
from api.dependencies import get_feature_flags, get_settings


# 创建应用
app = FastAPI(
    title="NeuralSite Core API",
    description="公路参数化建模系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(ai_detection_router)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
