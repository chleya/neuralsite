# -*- coding: utf-8 -*-
"""
业务校验规则

包含：路面厚度、平曲线半径、桥梁跨径、挖填方等业务校验
"""

from typing import Tuple, Optional, List


class BusinessValidator:
    """业务校验规则"""
    
    # ==================== 范围常量 ====================
    
    # 路面结构层厚度范围 (米)
    PAVEMENT_THICKNESS_RANGE = (0.15, 0.50)
    
    # 平曲线半径范围 (米)
    CURVE_RADIUS_RANGE = (100, 10000)
    
    # 桥梁跨径范围 (米)
    SPAN_RANGE = (5, 500)
    
    # 挖方深度范围 (米)
    EXCAVATION_RANGE = (0, 50)
    
    # 填方高度范围 (米)
    FILL_RANGE = (0, 40)
    
    # 纵坡坡度范围 (%)
    GRADIENT_RANGE = (0, 10)
    
    # 横坡坡度范围 (%)
    CROSS_SLOPE_RANGE = (1, 6)
    
    # 边坡高度范围 (米)
    SLOPE_HEIGHT_RANGE = (0, 30)
    
    # 隧道净空面积范围 (平方米)
    TUNNEL_AREA_RANGE = (30, 200)
    
    # 涵洞孔径范围 (米)
    CULVERT_SPAN_RANGE = (0.5, 10)
    
    # 挡土墙高度范围 (米)
    RETAINING_WALL_RANGE = (0, 20)
    
    # ==================== 路面结构校验 ====================
    
    @staticmethod
    def validate_pavement_thickness(thickness: float) -> Tuple[bool, str]:
        """
        校验路面厚度
        
        Args:
            thickness: 路面厚度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_t, max_t = BusinessValidator.PAVEMENT_THICKNESS_RANGE
        if thickness < min_t:
            return False, f"路面厚度{thickness}m小于最小值{min_t}m"
        if thickness > max_t:
            return False, f"路面厚度{thickness}m大于最大值{max_t}m"
        return True, "通过"
    
    # ==================== 线性工程校验 ====================
    
    @staticmethod
    def validate_curve_radius(radius: float) -> Tuple[bool, str]:
        """
        校验平曲线半径
        
        Args:
            radius: 平曲线半径 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_r, max_r = BusinessValidator.CURVE_RADIUS_RANGE
        if radius < min_r:
            return False, f"平曲线半径{radius}m小于最小值{min_r}m"
        if radius > max_r:
            return False, f"平曲线半径{radius}m大于最大值{max_r}m"
        return True, "通过"
    
    @staticmethod
    def validate_gradient(gradient: float) -> Tuple[bool, str]:
        """
        校验纵坡坡度
        
        Args:
            gradient: 纵坡坡度 (%)
            
        Returns:
            (是否通过, 消息)
        """
        min_g, max_g = BusinessValidator.GRADIENT_RANGE
        if gradient < min_g:
            return False, f"纵坡坡度{gradient}%小于最小值{min_g}%"
        if gradient > max_g:
            return False, f"纵坡坡度{gradient}%大于最大值{max_g}%"
        return True, "通过"
    
    @staticmethod
    def validate_cross_slope(slope: float) -> Tuple[bool, str]:
        """
        校验横坡坡度
        
        Args:
            slope: 横坡坡度 (%)
            
        Returns:
            (是否通过, 消息)
        """
        min_s, max_s = BusinessValidator.CROSS_SLOPE_RANGE
        if slope < min_s:
            return False, f"横坡坡度{slope}%小于最小值{min_s}%"
        if slope > max_s:
            return False, f"横坡坡度{slope}%大于最大值{max_s}%"
        return True, "通过"
    
    # ==================== 桥梁工程校验 ====================
    
    @staticmethod
    def validate_span(span: float) -> Tuple[bool, str]:
        """
        校验桥梁跨径
        
        Args:
            span: 桥梁跨径 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_s, max_s = BusinessValidator.SPAN_RANGE
        if span < min_s:
            return False, f"桥梁跨径{span}m小于最小值{min_s}m"
        if span > max_s:
            return False, f"桥梁跨径{span}m大于最大值{max_s}m"
        return True, "通过"
    
    @staticmethod
    def validate_pier_height(height: float) -> Tuple[bool, str]:
        """
        校验桥墩高度
        
        Args:
            height: 桥墩高度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        if height < 0:
            return False, f"桥墩高度{height}m不能为负值"
        if height > 50:
            return False, f"桥墩高度{height}m超过合理范围50m"
        return True, "通过"
    
    # ==================== 隧道工程校验 ====================
    
    @staticmethod
    def validate_tunnel_area(area: float) -> Tuple[bool, str]:
        """
        校验隧道净空面积
        
        Args:
            area: 隧道净空面积 (平方米)
            
        Returns:
            (是否通过, 消息)
        """
        min_a, max_a = BusinessValidator.TUNNEL_AREA_RANGE
        if area < min_a:
            return False, f"隧道净空面积{area}㎡小于最小值{min_a}㎡"
        if area > max_a:
            return False, f"隧道净空面积{area}㎡大于最大值{max_a}㎡"
        return True, "通过"
    
    @staticmethod
    def validate_tunnel_length(length: float) -> Tuple[bool, str]:
        """
        校验隧道长度
        
        Args:
            length: 隧道长度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        if length < 0:
            return False, f"隧道长度{length}m不能为负值"
        if length > 20000:
            return False, f"隧道长度{length}m超过合理范围20km"
        return True, "通过"
    
    # ==================== 涵洞工程校验 ====================
    
    @staticmethod
    def validate_culvert_span(span: float) -> Tuple[bool, str]:
        """
        校验涵洞孔径
        
        Args:
            span: 涵洞孔径 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_s, max_s = BusinessValidator.CULVERT_SPAN_RANGE
        if span < min_s:
            return False, f"涵洞孔径{span}m小于最小值{min_s}m"
        if span > max_s:
            return False, f"涵洞孔径{span}m大于最大值{max_s}m"
        return True, "通过"
    
    # ==================== 边坡工程校验 ====================
    
    @staticmethod
    def validate_excavation_depth(depth: float) -> Tuple[bool, str]:
        """
        校验挖方深度
        
        Args:
            depth: 挖方深度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_d, max_d = BusinessValidator.EXCAVATION_RANGE
        if depth < min_d:
            return False, f"挖方深度{depth}m小于最小值{min_d}m"
        if depth > max_d:
            return False, f"挖方深度{depth}m大于最大值{max_d}m"
        return True, "通过"
    
    @staticmethod
    def validate_fill_height(height: float) -> Tuple[bool, str]:
        """
        校验填方高度
        
        Args:
            height: 填方高度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_h, max_h = BusinessValidator.FILL_RANGE
        if height < min_h:
            return False, f"填方高度{height}m小于最小值{min_h}m"
        if height > max_h:
            return False, f"填方高度{height}m大于最大值{max_h}m"
        return True, "通过"
    
    @staticmethod
    def validate_slope_height(height: float) -> Tuple[bool, str]:
        """
        校验边坡高度
        
        Args:
            height: 边坡高度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_h, max_h = BusinessValidator.SLOPE_HEIGHT_RANGE
        if height < min_h:
            return False, f"边坡高度{height}m小于最小值{min_h}m"
        if height > max_h:
            return False, f"边坡高度{height}m大于最大值{max_h}m"
        return True, "通过"
    
    @staticmethod
    def validate_slope_ratio(ratio: float) -> Tuple[bool, str]:
        """
        校验边坡坡率
        
        Args:
            ratio: 边坡坡率 (如 1:0.5 输入 0.5)
            
        Returns:
            (是否通过, 消息)
        """
        if ratio <= 0:
            return False, f"边坡坡率{ratio}必须大于0"
        if ratio > 3:
            return False, f"边坡坡率{ratio}:1超过合理范围1:3"
        return True, "通过"
    
    # ==================== 挡土墙校验 ====================
    
    @staticmethod
    def validate_retaining_wall_height(height: float) -> Tuple[bool, str]:
        """
        校验挡土墙高度
        
        Args:
            height: 挡土墙高度 (米)
            
        Returns:
            (是否通过, 消息)
        """
        min_h, max_h = BusinessValidator.RETAINING_WALL_RANGE
        if height < min_h:
            return False, f"挡土墙高度{height}m小于最小值{min_h}m"
        if height > max_h:
            return False, f"挡土墙高度{height}m大于最大值{max_h}m"
        return True, "通过"
    
    # ==================== 综合校验 ====================
    
    @classmethod
    def validate_all(cls, **kwargs) -> List[Tuple[str, bool, str]]:
        """
        综合校验多个字段
        
        Args:
            **kwargs: 字段名=值的字典
            
        Returns:
            [(字段名, 是否通过, 消息), ...]
        """
        results = []
        
        # 映射字段名到校验方法
        validators = {
            "pavement_thickness": cls.validate_pavement_thickness,
            "curve_radius": cls.validate_curve_radius,
            "gradient": cls.validate_gradient,
            "cross_slope": cls.validate_cross_slope,
            "span": cls.validate_span,
            "pier_height": cls.validate_pier_height,
            "tunnel_area": cls.validate_tunnel_area,
            "tunnel_length": cls.validate_tunnel_length,
            "culvert_span": cls.validate_culvert_span,
            "excavation_depth": cls.validate_excavation_depth,
            "fill_height": cls.validate_fill_height,
            "slope_height": cls.validate_slope_height,
            "slope_ratio": cls.validate_slope_ratio,
            "retaining_wall_height": cls.validate_retaining_wall_height,
        }
        
        for field, value in kwargs.items():
            if field in validators and value is not None:
                is_valid, msg = validators[field](value)
                results.append((field, is_valid, msg))
        
        return results
