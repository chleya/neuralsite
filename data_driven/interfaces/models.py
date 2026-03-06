# -*- coding: utf-8 -*-
"""
数据模型定义
Pydantic models for API request/response
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProjectStatus(str, Enum):
    """项目状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class IssueSeverity(str, Enum):
    """问题严重级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    """问题状态"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ==================== 项目模型 ====================

class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[str] = Field("active", description="项目状态")


class Project(BaseModel):
    """项目完整信息"""
    id: str = Field(..., description="项目ID")
    name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: str
    updated_at: str


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: str
    updated_at: Optional[str] = None


# ==================== 空间数据模型 ====================

class SpatialStation(BaseModel):
    """桩号信息"""
    station: str = Field(..., description="桩号")
    easting: float = Field(..., description="东坐标")
    northing: float = Field(..., description="北坐标")
    elevation: Optional[float] = Field(None, description="高程")


class SpatialStationResponse(BaseModel):
    """桩号响应"""
    station: str
    easting: float
    northing: float
    elevation: Optional[float] = None
    distance: Optional[float] = None


# ==================== 区块链模型 ====================

class ChainRecordCreate(BaseModel):
    """创建存证请求"""
    data_id: Optional[str] = Field(None, description="数据ID")
    data_type: str = Field(..., description="数据类型")
    data: Dict[str, Any] = Field(..., description="业务数据")
    operator: str = Field(..., description="操作人")


class ChainRecord(BaseModel):
    """存证记录"""
    chain_id: str
    data_id: str
    data_type: str
    data_hash: str
    record_data: Dict[str, Any]
    created_at: str


class ChainRecordResponse(BaseModel):
    """存证响应"""
    id: str
    data_id: str
    data_hash: str
    created_at: str


# ==================== 工程实体模型 ====================

class Entity(BaseModel):
    """工程实体"""
    id: str
    project_id: str
    entity_type: str
    station: str
    name: str
    properties: Dict[str, Any] = {}
    created_at: str


class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    project_id: str
    entity_type: str
    station: str
    name: str
    properties: Dict[str, Any]
    created_at: str


# ==================== 照片模型 ====================

class PhotoCreate(BaseModel):
    """上传照片请求"""
    entity_id: str = Field(..., description="关联实体ID")
    station: str = Field(..., description="桩号")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")


class Photo(BaseModel):
    """照片记录"""
    id: str
    entity_id: str
    station: str
    filename: str
    file_path: str
    uploaded_at: str
    verified: bool = False


class PhotoResponse(BaseModel):
    """照片响应"""
    id: str
    entity_id: str
    station: str
    filename: str
    file_path: str
    uploaded_at: str
    verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None


# ==================== 问题模型 ====================

class IssueCreate(BaseModel):
    """创建问题请求"""
    station: str = Field(..., description="桩号")
    issue_type: str = Field(..., description="问题类型")
    severity: str = Field(..., description="严重级别")
    description: str = Field(..., description="问题描述")


class Issue(BaseModel):
    """问题记录"""
    id: str
    station: str
    issue_type: str
    severity: str
    description: str
    status: str = "open"
    created_at: str
    updated_at: str


class IssueResponse(BaseModel):
    """问题响应"""
    id: str
    station: str
    issue_type: str
    severity: str
    description: str
    status: str
    created_at: str
    updated_at: Optional[str] = None


# ==================== 通用响应模型 ====================

class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: Optional[int] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
