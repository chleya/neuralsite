# NeuralSite API 依赖注入
# 数据库会话管理 + 当前用户获取

import os
from typing import Generator, Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.p0_models import Base, User

# ==================== 配置 ====================

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neuralsite:neuralsite@localhost:5432/neuralsite"
)

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# ==================== 数据库引擎 ====================

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


# ==================== 依赖函数 ====================

def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖
    
    使用:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 密码加密 ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


# ==================== JWT认证 ====================

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", ACCESS_TOKEN_EXPIRE_MINUTES))
    from datetime import datetime, timedelta
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ==================== 当前用户 ====================

class CurrentUser:
    """当前登录用户"""
    def __init__(self, user_id: uuid.UUID, username: str, role: str, project_id: Optional[uuid.UUID] = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.project_id = project_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    获取当前登录用户
    
    从JWT token中解析用户信息
    
    Raises:
        HTTPException: 认证失败
    
    Returns:
        CurrentUser: 当前用户对象
    """
    token = credentials.credentials
    
    # 解码token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    username: str = payload.get("username")
    role: str = payload.get("role", "worker")
    project_id: str = payload.get("project_id")
    
    if user_id is None or username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌信息不完整",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证用户是否存在
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
        )
    
    user = db.query(User).filter(User.user_id == user_uuid).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已停用",
        )
    
    return CurrentUser(
        user_id=user_uuid,
        username=username,
        role=role,
        project_id=uuid.UUID(project_id) if project_id else None
    )


def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """获取当前活跃用户（可选额外检查）"""
    return current_user


# ==================== 角色权限检查 ====================

def require_role(*allowed_roles: str):
    """
    角色权限装饰器
    
    使用:
        @router.put("/users/{user_id}")
        def update_user(
            user_id: uuid.UUID,
            user: UserUpdate,
            current_user: CurrentUser = Depends(require_role("admin", "manager"))
        ):
            ...
    """
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# ==================== 错误处理 ====================

class APIException(HTTPException):
    """API统一异常"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(APIException):
    """资源不存在"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource}不存在: {identifier}"
        )


class ConflictError(APIException):
    """资源冲突"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ValidationError(APIException):
    """验证错误"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
