# -*- coding: utf-8 -*-
"""
Settings - 应用配置管理

从环境变量或配置文件加载配置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class Settings:
    """
    应用设置管理器
    
    配置来源（优先级从高到低）:
    1. 环境变量
    2. 配置文件 (config.json)
    3. 默认值
    """
    
    # 默认配置
    DEFAULTS: Dict[str, Any] = {
        # API 配置
        "api_host": "0.0.0.0",
        "api_port": 8000,
        "api_debug": False,
        
        # 数据库配置
        "db_path": "neuralsite.db",
        "db_echo": False,
        
        # Neo4j 配置
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        
        # 引擎配置
        "engine_cache_enabled": True,
        "engine_max_cache_size": 100,
        
        # 默认路线数据（示例数据）
        "default_route": {
            "route_id": "default",
            "design_speed": 80,
            "horizontal_alignment": [
                {
                    "element_type": "直线",
                    "start_station": "K0+000",
                    "end_station": "K0+500",
                    "azimuth": 45,
                    "x0": 500000,
                    "y0": 3000000
                },
                {
                    "element_type": "缓和曲线",
                    "start_station": "K0+500",
                    "end_station": "K0+600",
                    "azimuth": 45,
                    "x0": 500353.553,
                    "y0": 3000353.553,
                    "A": 300,
                    "R": 800,
                    "direction": "右"
                },
                {
                    "element_type": "圆曲线",
                    "start_station": "K0+600",
                    "end_station": "K1+200",
                    "azimuth": 45,
                    "x0": 500424.264,
                    "y0": 3000424.264,
                    "R": 800,
                    "cx": 500424.264,
                    "cy": 3000224.264,
                    "direction": "右"
                }
            ],
            "vertical_alignment": [
                {"station": "K0+000", "elevation": 100, "grade_out": 20},
                {"station": "K0+500", "elevation": 110, "grade_in": 20, "grade_out": -15, "length": 200},
                {"station": "K1+200", "elevation": 99.5, "grade_in": -15}
            ],
            "cross_section_template": {
                "width": 26,
                "lanes": 4,
                "crown_slope": 2.0
            }
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_file = config_file or self._get_default_config_file()
        
        # 加载配置
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()
    
    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        # 相对于 core 目录
        base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "config.json")
    
    def _load_defaults(self):
        """加载默认配置"""
        self._config = self.DEFAULTS.copy()
    
    def _load_from_file(self):
        """从配置文件加载"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config from {self._config_file}: {e}")
    
    def _load_from_env(self):
        """从环境变量加载"""
        # API 配置
        if host := os.environ.get("NEURALSITE_API_HOST"):
            self._config["api_host"] = host
        if port := os.environ.get("NEURALSITE_API_PORT"):
            self._config["api_port"] = int(port)
        if debug := os.environ.get("NEURALSITE_API_DEBUG"):
            self._config["api_debug"] = debug.lower() in ("true", "1", "yes")
        
        # 数据库配置
        if db_path := os.environ.get("NEURALSITE_DB_PATH"):
            self._config["db_path"] = db_path
        
        # Neo4j 配置
        if uri := os.environ.get("NEURALSITE_NEO4J_URI"):
            self._config["neo4j_uri"] = uri
        if user := os.environ.get("NEURALSITE_NEO4J_USER"):
            self._config["neo4j_user"] = user
        if password := os.environ.get("NEURALSITE_NEO4J_PASSWORD"):
            self._config["neo4j_password"] = password
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def get_default_route(self) -> Dict[str, Any]:
        """获取默认路线配置"""
        return self._config.get("default_route", self.DEFAULTS["default_route"])
    
    def set(self, key: str, value: Any):
        """设置配置值（运行时）"""
        self._config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取设置实例（带缓存）"""
    return Settings()


# 便捷访问
settings = get_settings()
