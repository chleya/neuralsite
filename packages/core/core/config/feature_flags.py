# -*- coding: utf-8 -*-
"""
Feature Flags - 特性开关系统

支持从环境变量或配置文件读取特性开关状态
"""

import os
from typing import Dict, Any, Optional
from functools import lru_cache


class FeatureFlags:
    """
    特性开关管理器
    
    使用方法:
        from core.config.feature_flags import feature_flags
        
        if feature_flags.is_enabled("new_calculation_engine"):
            # 使用新引擎
        else:
            # 使用旧引擎
    """
    
    # 默认特性开关配置
    DEFAULT_FLAGS: Dict[str, bool] = {
        # API 相关
        "enable_batch_calculation": True,
        "enable_cross_section": True,
        "enable_text_parser": True,
        "enable_lod_calculation": True,
        
        # 空间数据API (MVP)
        "enable_chainage_query": True,
        "enable_coordinate_transform": True,
        "enable_range_query": True,
        
        # 知识图谱API (MVP)
        "enable_qa_system": True,
        "enable_knowledge_graph": True,
        "enable_kg_reasoning": True,
        
        # 引擎相关
        "enable_cache": True,
        "enable_parallel_processing": False,
        
        # 存储相关
        "enable_database": True,
        "enable_graph_db": False,
        
        # 实验性功能
        "experimental_3d_model": False,
        "experimental_earthwork": False,
    }
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载特性开关"""
        prefix = "NEURALSITE_FLAG_"
        
        for key, default_value in self.DEFAULT_FLAGS.items():
            env_key = prefix + key.upper()
            env_value = os.environ.get(env_key)
            
            if env_value is not None:
                # 解析环境变量值
                self._flags[key] = env_value.lower() in ("true", "1", "yes", "on")
            else:
                self._flags[key] = default_value
    
    def is_enabled(self, flag_name: str) -> bool:
        """检查特性是否启用"""
        return self._flags.get(flag_name, self.DEFAULT_FLAGS.get(flag_name, False))
    
    def is_disabled(self, flag_name: str) -> bool:
        """检查特性是否禁用"""
        return not self.is_enabled(flag_name)
    
    def get(self, flag_name: str, default: bool = False) -> bool:
        """获取特性开关状态"""
        return self._flags.get(flag_name, default)
    
    def set(self, flag_name: str, value: bool):
        """设置特性开关（运行时）"""
        self._flags[flag_name] = value
    
    def get_all(self) -> Dict[str, bool]:
        """获取所有特性开关"""
        return {**self.DEFAULT_FLAGS, **self._flags}
    
    def enable(self, flag_name: str):
        """启用特性"""
        self.set(flag_name, True)
    
    def disable(self, flag_name: str):
        """禁用特性"""
        self.set(flag_name, False)


# 全局单例（仅用于兼容旧代码）
@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlags:
    """获取特性开关实例（带缓存）"""
    return FeatureFlags()


# 便捷访问
feature_flags = get_feature_flags()
