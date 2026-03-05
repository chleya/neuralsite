# NeuralSite 认证模块
# JWT Token生成和验证 + 用户登录/注册

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from api.deps import (
    get_db, get_password_hash, verify_password,
    create_access_token, get_current_user, CurrentUser,
    NotFoundError, ConflictError
)
from models.p0_models import User, UserCreate, UserResponse, UserRole

# ==================== 路由 ====================

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# ==================== 请求/响应模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    username: str
    role: str
    real_name: Optional[str] = None


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    real_name: Optional[str] = None
    role: UserRole = UserRole.WORKER
    phone: Optional[str] = None
    project_id: Optional[uuid.UUID] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').replace('-', '').isalnum(), '用户名只能包含字母、数字、下划线和连字符'
        return v


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str  # user_id
    username: str
    role: str
    project_id: Optional[str] = None


# ==================== 认证接口 ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - username: 用户名（唯一）
    - password: 密码（会自动哈希存储）
    - role: 角色（默认worker）
    - project_id: 所属项目（可选）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise ConflictError(f"用户名 '{request.username}' 已被注册")
    
    # 创建用户
    user = User(
        user_id=uuid.uuid4(),
        username=request.username,
        password_hash=get_password_hash(request.password),
        real_name=request.real_name,
        role=request.role.value,
        project_id=request.project_id,
        phone=request.phone,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - username: 用户名
    - password: 密码
    
    返回:
    - access_token: JWT访问令牌
    - token_type: 令牌类型
    - user_id: 用户ID
    - username: 用户名
    - role: 角色
    """
    # 查找用户
    user = db.query(User).filter(User.username == request.username).first()
    
    # 验证用户存在且活跃
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被停用"
        )
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成JWT令牌
    token_data = {
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role,
    }
    if user.project_id:
        token_data["project_id"] = str(user.project_id)
    
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        real_name=user.real_name
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新令牌
    
    使用当前用户的有效信息生成新令牌
    """
    # 获取最新用户信息
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已停用"
        )
    
    # 生成新令牌
    token_data = {
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role,
    }
    if user.project_id:
        token_data["project_id"] = str(user.project_id)
    
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        real_name=user.real_name
    )


@router.post("/logout")
def logout(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    用户登出
    
    注意: JWT是无状态的，真正的登出需要在黑名单中存储令牌
    这里只是一个占位接口，实际的登出需要配合Redis等黑名单机制
    """
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise NotFoundError("用户", str(current_user.user_id))
    return user


@router.put("/me/password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改当前用户密码"""
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise NotFoundError("用户", str(current_user.user_id))
    
    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}
