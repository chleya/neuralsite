"""
NeuralSite 配置加载模块
从环境变量加载配置，支持开发/生产环境

使用方式:
    from packages.core.config import settings
    print(settings.DATABASE_URL)
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    DATABASE_URL: str = Field(
        default="postgresql://neuralsite:changeme@localhost:5432/neuralsite",
        description="PostgreSQL 连接字符串"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, description="连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="最大溢出连接数")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="连接池超时时间(秒)")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间(秒)")
    DATABASE_ECHO: bool = Field(default=False, description="是否打印 SQL 日志")
    
    # PostgreSQL 特定配置
    DATABASE_HOST: Optional[str] = None
    DATABASE_PORT: Optional[int] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_NAME: Optional[str] = None


class RedisSettings(BaseSettings):
    """Redis 配置"""
    
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接字符串"
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="最大连接数")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Socket 超时时间(秒)")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Socket 连接超时(秒)")


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    SECRET_KEY: str = Field(
        default="changeme_generate_with_openssl_rand_hex_32",
        description="应用密钥"
    )
    JWT_SECRET_KEY: str = Field(default="", description="JWT 密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="访问令牌过期时间(分钟)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌过期时间(天)")


class AppSettings(BaseSettings):
    """应用配置"""
    
    APP_ENV: str = Field(default="development", description="环境: development/staging/production")
    APP_DEBUG: bool = Field(default=True, description="调试模式")
    APP_HOST: str = Field(default="0.0.0.0", description="监听地址")
    APP_PORT: int = Field(default=8000, description="监听端口")
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="CORS 允许的源"
    )
    
    # API
    API_V1_PREFIX: str = Field(default="/api/v1", description="API 前缀")
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="默认分页大小")
    MAX_PAGE_SIZE: int = Field(default=100, description="最大分页大小")
    
    # 文件上传
    UPLOAD_DIR: str = Field(default="./uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(default=52428800, description="最大文件大小(50MB)")


class Settings(BaseSettings):
    """主配置类 - 合并所有配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略未定义的额外字段
    )
    
    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    app: AppSettings = Field(default_factory=AppSettings)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果未单独设置 JWT_SECRET_KEY，使用 SECRET_KEY
        if not self.security.JWT_SECRET_KEY:
            self.security.JWT_SECRET_KEY = self.security.SECRET_KEY
    
    @property
    def is_development(self) -> bool:
        return self.app.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app.APP_ENV == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.app.APP_ENV == "staging"
    
    def get_database_url(self) -> str:
        """获取数据库 URL，优先使用 DATABASE_URL，否则组装"""
        if self.database.DATABASE_URL:
            return self.database.DATABASE_URL
        
        # 手动组装
        host = self.database.DATABASE_HOST or "localhost"
        port = self.database.DATABASE_PORT or 5432
        user = self.database.DATABASE_USER or "neuralsite"
        password = self.database.DATABASE_PASSWORD or "changeme"
        db = self.database.DATABASE_NAME or "neuralsite"
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def get_redis_url(self) -> str:
        """获取 Redis URL"""
        return self.redis.REDIS_URL


# 全局单例
@lru_cache()
def get_settings() -> Settings:
    """获取配置单例 (带缓存)"""
    return Settings()


# 导出便捷访问
settings = get_settings()


# ==================== 数据库连接池 ====================

def get_database_config() -> dict:
    """获取 SQLAlchemy 数据库配置"""
    return {
        "url": settings.get_database_url(),
        "pool_size": settings.database.DATABASE_POOL_SIZE,
        "max_overflow": settings.database.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.database.DATABASE_POOL_TIMEOUT,
        "pool_recycle": settings.database.DATABASE_POOL_RECYCLE,
        "echo": settings.database.DATABASE_ECHO,
        "pool_pre_ping": True,  # 连接前 ping 检查
    }


def get_redis_config() -> dict:
    """获取 Redis 配置"""
    return {
        "url": settings.get_redis_url(),
        "max_connections": settings.redis.REDIS_MAX_CONNECTIONS,
        "socket_timeout": settings.redis.REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": settings.redis.REDIS_SOCKET_CONNECT_TIMEOUT,
    }


# ==================== 便捷函数 ====================

def get_database_url() -> str:
    """获取数据库连接 URL"""
    return settings.get_database_url()


def get_redis_url() -> str:
    """获取 Redis 连接 URL"""
    return settings.get_redis_url()


def get_cors_origins() -> list:
    """获取 CORS 允许的源列表"""
    return [origin.strip() for origin in settings.app.CORS_ORIGINS.split(",") if origin.strip()]


def is_development() -> bool:
    """是否开发环境"""
    return settings.is_development


def is_production() -> bool:
    """是否生产环境"""
    return settings.is_production
