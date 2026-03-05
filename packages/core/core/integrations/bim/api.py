# -*- coding: utf-8 -*-
"""
BIM 导入 API

提供文件上传、导入进度追踪、错误报告等功能
"""

import asyncio
import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime
import hashlib

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

import sys
sys.path.insert(0, '.')

from core.integrations.bim.models import (
    BIMProject,
    ImportProgress,
    ImportStatus,
    ImportError,
    IFCVersion
)
from core.integrations.bim.ifc_parser import IFCParser, create_parser
from core.integrations.bim.converter import BIMConverter, convert_bim_to_neuralsite

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bim", tags=["BIM导入"])


# ==================== 内存存储 ====================
# 生产环境应使用 Redis 或数据库
_import_progress_store: Dict[str, ImportProgress] = {}


# ==================== 请求/响应模型 ====================

class ImportRequest(BaseModel):
    """导入请求"""
    project_name: Optional[str] = None
    ifc_version: Optional[IFCVersion] = None


class ImportResponse(BaseModel):
    """导入响应"""
    task_id: str
    status: ImportStatus
    message: str


class ImportResult(BaseModel):
    """导入结果"""
    task_id: str
    status: ImportStatus
    progress: float
    
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    
    statistics: Optional[Dict[str, Any]] = None
    
    errors: List[ImportError] = []
    
    download_url: Optional[str] = None
    preview_data: Optional[Dict[str, Any]] = None


class ElementQuery(BaseModel):
    """构件查询"""
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    storey_id: Optional[str] = None
    material: Optional[str] = None
    
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ==================== 工具函数 ====================

def _calculate_file_hash(content: bytes) -> str:
    """计算文件哈希"""
    return hashlib.md5(content).hexdigest()


def _get_progress(task_id: str) -> Optional[ImportProgress]:
    """获取导入进度"""
    return _import_progress_store.get(task_id)


def _update_progress(task_id: str, progress: ImportProgress):
    """更新导入进度"""
    _import_progress_store[task_id] = progress


def _create_error(code: str, message: str, element_id: Optional[str] = None) -> ImportError:
    """创建错误对象"""
    return ImportError(
        code=code,
        message=message,
        element_id=element_id
    )


# ==================== 导入任务 ====================

async def _run_import_task(
    task_id: str,
    content: bytes,
    filename: str,
    project_name: Optional[str] = None
):
    """执行导入任务"""
    
    progress = ImportProgress(
        task_id=task_id,
        status=ImportStatus.PARSING,
        progress=0,
        message="正在初始化导入...",
        started_at=datetime.now()
    )
    _update_progress(task_id, progress)
    
    try:
        # 阶段 1: 解析 IFC 文件 (0-40%)
        progress.status = ImportStatus.PARSING
        progress.message = "正在解析 IFC 文件..."
        progress.progress = 5
        _update_progress(task_id, progress)
        
        parser = create_parser()
        
        # 检测版本
        version = parser.get_version_from_bytes(content)
        logger.info(f"Detected IFC version: {version}")
        
        # 解析
        bim_project = parser.parse_stream(content)
        
        # 更新项目名称
        if project_name:
            bim_project.name = project_name
        elif not bim_project.name:
            bim_project.name = Path(filename).stem
        
        progress.progress = 40
        progress.total_elements = bim_project.total_elements
        progress.message = f"已解析 {bim_project.total_elements} 个构件"
        _update_progress(task_id, progress)
        
        # 阶段 2: 转换数据 (40-80%)
        progress.status = ImportStatus.CONVERTING
        progress.message = "正在转换数据..."
        progress.progress = 45
        _update_progress(task_id, progress)
        
        converter = BIMConverter()
        result = converter.convert(bim_project)
        
        progress.progress = 80
        progress.processed_elements = bim_project.total_elements
        progress.message = "数据转换完成"
        _update_progress(task_id, progress)
        
        # 阶段 3: 完成
        progress.status = ImportStatus.COMPLETED
        progress.progress = 100
        progress.message = "导入完成"
        progress.completed_at = datetime.now()
        progress.result = bim_project
        
        # 添加统计信息
        progress.message = f"导入完成：{bim_project.total_elements} 个构件"
        _update_progress(task_id, progress)
        
        logger.info(f"Import task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Import task {task_id} failed: {e}", exc_info=True)
        
        progress.status = ImportStatus.FAILED
        progress.message = f"导入失败: {str(e)}"
        progress.errors.append(_create_error("IMPORT_FAILED", str(e)))
        progress.completed_at = datetime.now()
        _update_progress(task_id, progress)


# ==================== API 端点 ====================

@router.post("/import", response_model=ImportResponse)
async def import_bim_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="IFC 文件 (.ifc, .ifcXML)"),
    project_name: Optional[str] = Form(None, description="项目名称")
):
    """导入 BIM 文件
    
    支持格式:
    - IFC2x3 (.ifc)
    - IFC4 (.ifc)
    - IFC4X1 (.ifc)
    
    返回任务 ID，可通过 /import/{task_id} 查询进度
    """
    
    # 验证文件类型
    allowed_extensions = {'.ifc', '.ifcxml', '.ifcXML'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。支持: {', '.join(allowed_extensions)}"
        )
    
    # 验证文件大小 (最大 500MB)
    MAX_SIZE = 500 * 1024 * 1024
    
    # 读取文件内容
    content = await file.read()
    
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大: {len(content) / 1024 / 1024:.1f}MB。最大支持: {MAX_SIZE / 1024 / 1024}MB"
        )
    
    if len(content) < 100:
        raise HTTPException(
            status_code=400,
            detail="文件内容过小，不是有效的 IFC 文件"
        )
    
    # 创建任务
    task_id = str(uuid4())
    
    # 初始化进度
    progress = ImportProgress(
        task_id=task_id,
        status=ImportStatus.PENDING,
        progress=0,
        message="任务已创建，等待处理..."
    )
    _update_progress(task_id, progress)
    
    # 后台执行导入
    background_tasks.add_task(
        _run_import_task,
        task_id,
        content,
        file.filename,
        project_name
    )
    
    return ImportResponse(
        task_id=task_id,
        status=ImportStatus.PENDING,
        message="文件上传成功，导入任务已创建"
    )


@router.get("/import/{task_id}", response_model=ImportResult)
async def get_import_result(task_id: str):
    """查询导入结果"""
    
    progress = _get_progress(task_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"找不到任务: {task_id}"
        )
    
    result = ImportResult(
        task_id=progress.task_id,
        status=progress.status,
        progress=progress.progress,
        errors=progress.errors
    )
    
    if progress.result:
        result.project_id = progress.result.id
        result.project_name = progress.result.name
    
    if progress.status == ImportStatus.COMPLETED:
        # 添加统计数据
        if progress.result:
            result.statistics = {
                "total_elements": progress.result.total_elements,
                "element_type_counts": progress.result.element_type_counts,
                "building_count": len(progress.result.buildings)
            }
    
    return result


@router.get("/import/{task_id}/entities")
async def get_entities(
    task_id: str,
    entity_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """获取导入的实体列表"""
    
    progress = _get_progress(task_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if progress.status != ImportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Import not completed")
    
    if not progress.result:
        raise HTTPException(status_code=500, detail="No result data")
    
    # 转换数据
    converter = BIMConverter()
    result = converter.convert(progress.result)
    
    entities = result.get("entities", [])
    
    # 过滤
    if entity_type:
        entities = [e for e in entities if e.get("type") == entity_type]
    
    return {
        "total": len(entities),
        "limit": limit,
        "offset": offset,
        "entities": entities[offset:offset + limit]
    }


@router.get("/import/{task_id}/entity/{entity_id}")
async def get_entity_detail(task_id: str, entity_id: str):
    """获取实体详情"""
    
    progress = _get_progress(task_id)
    
    if not progress or progress.status != ImportStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if not progress.result:
        raise HTTPException(status_code=500, detail="No data")
    
    # 查找构件
    element = progress.result.elements.get(entity_id)
    
    if not element:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {
        "id": element.id,
        "global_id": element.global_id,
        "ifc_type": element.ifc_type,
        "element_type": element.element_type.value,
        "name": element.name,
        "description": element.description,
        "material": element.material,
        "properties": [
            {"name": p.name, "value": p.value, "type": p.type.value}
            for p in element.properties
        ],
        "geometry": element.geometry.dict() if element.geometry else None,
        "position": element.position,
        "storey_id": element.storey_id,
        "building_id": element.building_id
    }


@router.get("/import/{task_id}/preview")
async def get_preview_data(task_id: str):
    """获取预览数据 (用于 3D 查看)"""
    
    progress = _get_progress(task_id)
    
    if not progress or progress.status != ImportStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if not progress.result:
        raise HTTPException(status_code=500, detail="No data")
    
    bim = progress.result
    
    # 构建简化的预览数据
    preview = {
        "project": {
            "id": bim.id,
            "name": bim.name,
            "ifc_version": bim.ifc_version.value
        },
        "statistics": {
            "total_elements": bim.total_elements,
            "by_type": bim.element_type_counts
        },
        "buildings": [
            {
                "id": b.id,
                "name": b.name,
                "storeys": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "elevation": s.elevation,
                        "element_count": len(s.element_ids)
                    }
                    for s in b.storeys
                ]
            }
            for b in bim.buildings
        ],
        # 采样一些构件用于预览
        "sample_elements": [
            {
                "id": e.id,
                "type": e.element_type.value,
                "name": e.name,
                "geometry_type": e.geometry.type if e.geometry else None
            }
            for e in list(bim.elements.values())[:50]
        ]
    }
    
    return preview


@router.delete("/import/{task_id}")
async def cancel_import(task_id: str):
    """取消导入任务"""
    
    progress = _get_progress(task_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if progress.status in [ImportStatus.COMPLETED, ImportStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task already finished")
    
    # 标记为失败 (简化实现)
    progress.status = ImportStatus.FAILED
    progress.message = "任务已取消"
    progress.completed_at = datetime.now()
    _update_progress(task_id, progress)
    
    return {"status": "cancelled", "task_id": task_id}


@router.get("/formats")
async def list_supported_formats():
    """列出支持的 BIM 格式"""
    return {
        "formats": [
            {
                "id": "ifc2x3",
                "name": "IFC2x3",
                "extensions": [".ifc"],
                "description": "Industry Foundation Classes 2x3",
                "max_size": "500MB"
            },
            {
                "id": "ifc4",
                "name": "IFC4",
                "extensions": [".ifc"],
                "description": "Industry Foundation Classes 4",
                "max_size": "500MB"
            },
            {
                "id": "ifc4x1",
                "name": "IFC4X1",
                "extensions": [".ifc"],
                "description": "Industry Foundation Classes 4 X1",
                "max_size": "500MB"
            },
            {
                "id": "ifcxml",
                "name": "IFC-XML",
                "extensions": [".ifcxml", ".ifcXML"],
                "description": "IFC in XML format (experimental)",
                "max_size": "500MB"
            }
        ],
        "notes": [
            "建议使用 .ifc 格式",
            "ifcopenshell 库用于解析 (如未安装，将使用简单解析器)",
            "支持 Revit, Tekla, ArchiCAD 等主流 BIM 软件导出的 IFC"
        ]
    }


# 扩展 IFCParser 添加从字节流检测版本的方法
def _extend_parser():
    """扩展解析器功能"""
    original_parse_stream = IFCParser.parse_stream
    
    def parse_stream_with_version(self, content: bytes) -> BIMProject:
        # 写入临时文件进行版本检测
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            version = self.get_version(temp_path)
            return self._parse_with_ifcopenshell(temp_path, version)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def get_version_from_bytes(self, content: bytes) -> str:
        """从字节流检测版本"""
        # 简单检测
        content_str = content[:5000].decode('utf-8', errors='ignore')
        
        if "IFC4X1" in content_str or "IFC4X2" in content_str:
            return "IFC4X1"
        elif "IFC4" in content_str:
            return "IFC4"
        else:
            return "IFC2X3"
    
    IFCParser.parse_stream = parse_stream_with_version
    IFCParser.get_version_from_bytes = get_version_from_bytes


_extend_parser()
