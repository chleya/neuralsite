# -*- coding: utf-8 -*-
"""
AI质量检测 - API路由
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
sys.path.insert(0, '.')

from .workflow import InspectionWorkflow
from .models import (
    InspectionTask, BatchDetectionResult, ReviewStatus
)

# 全局工作流实例
_workflow: Optional[InspectionWorkflow] = None


def get_workflow() -> InspectionWorkflow:
    """获取工作流实例"""
    global _workflow
    if _workflow is None:
        _workflow = InspectionWorkflow()
    return _workflow


router = APIRouter(prefix="/api/v1/ai-detection", tags=["AI质量检测"])


class ProcessImageRequest:
    """处理图像请求"""
    pass


class ReviewRequest(BaseModel):
    """审核请求"""
    task_id: str
    reviewer_id: str
    approved: bool
    comment: str = ""


@router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    location: str = Form(""),
    inspector_id: Optional[str] = Form(None)
):
    """
    处理单张图像
    """
    try:
        # 读取图像数据
        image_data = await file.read()
        
        workflow = get_workflow()
        
        task = workflow.process_image(
            image_data=image_data,
            project_id=project_id,
            location=location,
            inspector_id=inspector_id
        )
        
        return {
            "status": "success",
            "task": task.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/batch")
async def process_batch(
    files: List[UploadFile] = File(...),
    project_id: Optional[int] = Form(None),
    location: str = Form(""),
    inspector_id: Optional[str] = Form(None)
):
    """
    批量处理图像
    """
    try:
        # 读取所有图像数据
        image_data_list = []
        for f in files:
            data = await f.read()
            image_data_list.append(data)
        
        workflow = get_workflow()
        
        result = workflow.process_batch(
            image_data_list=image_data_list,
            project_id=project_id,
            location=location,
            inspector_id=inspector_id
        )
        
        return {
            "status": "success",
            "result": result.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task(task_id: str):
    """
    获取任务详情
    """
    workflow = get_workflow()
    task = workflow.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "status": "success",
        "task": task.to_dict()
    }


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    project_id: Optional[int] = None
):
    """
    获取任务列表
    """
    workflow = get_workflow()
    
    if status:
        try:
            status_enum = ReviewStatus(status)
            tasks = workflow.get_tasks_by_status(status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")
    elif project_id is not None:
        tasks = workflow.get_tasks_by_project(project_id)
    else:
        tasks = list(workflow._tasks.values())
    
    return {
        "status": "success",
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }


@router.get("/tasks/pending")
async def get_pending_tasks():
    """
    获取待审核任务
    """
    workflow = get_workflow()
    tasks = workflow.get_pending_tasks()
    
    return {
        "status": "success",
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }


@router.post("/review")
async def review_task(
    task_id: str,
    reviewer_id: str,
    approved: bool,
    comment: str = ""
):
    """
    审核任务
    """
    try:
        workflow = get_workflow()
        
        task = workflow.review_task(
            task_id=task_id,
            reviewer_id=reviewer_id,
            approved=approved,
            comment=comment
        )
        
        return {
            "status": "success",
            "task": task.to_dict()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(project_id: Optional[int] = None):
    """
    获取统计信息
    """
    workflow = get_workflow()
    stats = workflow.get_statistics(project_id)
    
    return {
        "status": "success",
        "statistics": stats
    }


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务
    """
    workflow = get_workflow()
    
    if workflow.delete_task(task_id):
        return {"status": "success", "message": "任务已删除"}
    
    raise HTTPException(status_code=404, detail="任务不存在")


@router.delete("/tasks")
async def clear_tasks():
    """
    清空所有任务
    """
    workflow = get_workflow()
    workflow.clear_all_tasks()
    
    return {"status": "success", "message": "所有任务已清空"}


@router.post("/demo")
async def demo_detection():
    """
    演示：生成测试数据
    """
    import numpy as np
    import cv2
    
    workflow = get_workflow()
    workflow.clear_all_tasks()
    
    # 生成测试图像
    test_images = []
    
    # 正常路面
    img1 = np.ones((480, 640, 3), dtype=np.uint8) * 150
    test_images.append(("demo_normal.jpg", img1))
    
    # 有裂缝的路面
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 140
    cv2.line(img2, (100, 50), (500, 400), (50, 50, 50), 3)
    test_images.append(("demo_crack.jpg", img2))
    
    # 有破损的路面
    img3 = np.ones((480, 640, 3), dtype=np.uint8) * 130
    cv2.circle(img3, (320, 240), 50, (80, 80, 80), -1)
    test_images.append(("demo_spalling.jpg", img3))
    
    tasks = []
    for name, img in test_images:
        # 保存临时文件并处理
        temp_path = f"/tmp/{name}"
        cv2.imwrite(temp_path, img)
        
        task = workflow.process_image(
            image_path=temp_path,
            project_id=1,
            location="演示路段"
        )
        tasks.append(task)
    
    return {
        "message": "演示数据生成完成",
        "total": len(tasks),
        "with_defects": sum(1 for t in tasks if t.has_defects),
        "pending_review": sum(1 for t in tasks if t.status == ReviewStatus.PENDING),
        "tasks": [t.to_dict() for t in tasks]
    }
