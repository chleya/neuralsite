# NeuralSite Spatial Calculator
# 空间计算引擎 - 桩号坐标转换、平竖曲线计算
# 
# 功能:
# 1. 桩号转坐标 (station_to_point)
# 2. 坐标转桩号 (point_to_station)
# 3. 平曲线计算 (直线、圆曲线、螺旋线)
# 4. 竖曲线计算

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union


# ==================== 数据模型 ====================

@dataclass
class Point2D:
    """二维坐标点"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point2D') -> float:
        """计算到另一点的距离"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def __add__(self, other: 'Point2D') -> 'Point2D':
        return Point2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point2D') -> 'Point2D':
        return Point2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point2D':
        return Point2D(self.x * scalar, self.y * scalar)


@dataclass
class Point3D:
    """三维坐标点"""
    x: float
    y: float
    z: float  # 高程
    
    def distance_to(self, other: 'Point3D') -> float:
        """计算到另一点的水平距离"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Vector2D:
    """二维向量"""
    x: float
    y: float
    
    @property
    def magnitude(self) -> float:
        """向量长度"""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    @property
    def angle(self) -> float:
        """向量角度(弧度)"""
        return math.atan2(self.y, self.x)
    
    def normalized(self) -> 'Vector2D':
        """单位向量"""
        mag = self.magnitude
        if mag < 1e-10:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def dot(self, other: 'Vector2D') -> float:
        """点积"""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2D') -> float:
        """叉积(2D)"""
        return self.x * other.y - self.y * other.x


# ==================== 平曲线元素 ====================

@dataclass
class LineElement:
    """直线元素"""
    start_station: float      # 起点桩号
    start_point: Point2D      # 起点坐标
    azimuth: float            # 方位角(弧度)
    length: float             # 长度
    
    @property
    def end_station(self) -> float:
        return self.start_station + self.length
    
    @property
    def end_point(self) -> Point2D:
        """计算终点坐标"""
        return Point2D(
            self.start_point.x + self.length * math.cos(self.azimuth),
            self.start_point.y + self.length * math.sin(self.azimuth)
        )
    
    def get_point_at(self, station: float) -> Point2D:
        """获取指定桩号对应的坐标"""
        if station < self.start_station or station > self.end_station:
            raise ValueError(f"桩号 {station} 不在直线范围 [{self.start_station}, {self.end_station}] 内")
        
        offset = station - self.start_station
        return Point2D(
            self.start_point.x + offset * math.cos(self.azimuth),
            self.start_point.y + offset * math.sin(self.azimuth)
        )
    
    def get_station_at(self, point: Point2D) -> Optional[float]:
        """计算点对应的桩号(直线段)"""
        # 使用最近点投影
        dx = point.x - self.start_point.x
        dy = point.y - self.start_point.y
        
        # 投影到直线方向
        offset = dx * math.cos(self.azimuth) + dy * math.sin(self.azimuth)
        
        if offset < 0 or offset > self.length:
            return None
        
        return self.start_station + offset


@dataclass
class CircularCurveElement:
    """圆曲线元素"""
    start_station: float      # 起点桩号
    start_point: Point2D      # 起点坐标
    azimuth_in: float         # 起点方位角(弧度)
    radius: float              # 半径(左转为正,右转为负)
    length: float             # 曲线长度
    
    @property
    def end_station(self) -> float:
        return self.start_station + self.length
    
    @property
    def center(self) -> Point2D:
        """计算圆心"""
        # 圆心位置: 沿起点切线方向偏移R得到圆心
        # 左转(R>0): 圆心在左侧; 右转(R<0): 圆心在右侧
        if self.radius > 0:
            # 左转, 圆心在切线左侧90度
            center_azimuth = self.azimuth_in - math.pi / 2
        else:
            # 右转, 圆心在切线右侧90度
            center_azimuth = self.azimuth_in + math.pi / 2
        
        abs_radius = abs(self.radius)
        return Point2D(
            self.start_point.x + abs_radius * math.cos(center_azimuth),
            self.start_point.y + abs_radius * math.sin(center_azimuth)
        )
    
    @property
    def central_angle(self) -> float:
        """圆心角(弧度)"""
        return self.length / abs(self.radius)
    
    @property
    def end_point(self) -> Point2D:
        """计算终点坐标"""
        return self.get_point_at(self.end_station)
    
    def get_point_at(self, station: float) -> Point2D:
        """获取指定桩号对应的坐标"""
        if station < self.start_station or station > self.end_station:
            raise ValueError(f"桩号 {station} 不在圆曲线范围 [{self.start_station}, {self.end_station}] 内")
        
        offset = station - self.start_station
        angle = offset / abs(self.radius)  # 转角
        
        # 从起点沿圆弧移动
        if self.radius > 0:
            # 左转
            start_angle = self.azimuth_in - math.pi / 2
            current_angle = start_angle + angle
        else:
            # 右转
            start_angle = self.azimuth_in + math.pi / 2
            current_angle = start_angle - angle
        
        r = abs(self.radius)
        return Point2D(
            self.center.x + r * math.cos(current_angle),
            self.center.y + r * math.sin(current_angle)
        )
    
    def get_station_at(self, point: Point2D) -> Optional[float]:
        """计算点对应的桩号(圆曲线段)"""
        # 计算点到圆心的距离和角度
        dx = point.x - self.center.x
        dy = point.y - self.center.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        
        if abs(dist - abs(self.radius)) > 0.01:  # 允许一定误差
            return None
        
        # 计算角度
        angle = math.atan2(dy, dx)
        
        # 计算相对于起点的转角
        if self.radius > 0:
            # 左转
            start_angle = self.azimuth_in - math.pi / 2
            delta_angle = angle - start_angle
        else:
            # 右转
            start_angle = self.azimuth_in + math.pi / 2
            delta_angle = start_angle - angle
        
        # 规范化角度到 [0, 2π)
        while delta_angle < 0:
            delta_angle += 2 * math.pi
        while delta_angle >= 2 * math.pi:
            delta_angle -= 2 * math.pi
        
        arc_length = delta_angle * abs(self.radius)
        
        if arc_length > self.length:
            return None
        
        return self.start_station + arc_length


@dataclass
class SpiralElement:
    """螺旋线/缓和曲线元素
    
    使用回旋线(Helianthoid)公式:
    A² = R * L
    其中: A - 螺旋参数, R - 圆曲线半径, L - 缓和曲线长度
    """
    start_station: float      # 起点桩号
    start_point: Point2D      # 起点坐标
    azimuth_in: float          # 起点方位角(弧度)
    radius_start: float        # 起点半径(起点处半径,无穷大用0表示)
    radius_end: float          # 终点半径(接圆曲线处半径)
    length: float             # 缓和曲线长度
    direction: int            # 方向: 1=左转, -1=右转
    
    @property
    def end_station(self) -> float:
        return self.start_station + self.length
    
    @property
    def spiral_param_a(self) -> float:
        """计算螺旋参数 A"""
        if self.radius_end == 0:
            return 0
        return math.sqrt(abs(self.radius_end) * self.length)
    
    @property
    def end_point(self) -> Point2D:
        """计算终点坐标"""
        return self.get_point_at(self.end_station)
    
    def _spiral_angle(self, l: float) -> float:
        """计算螺旋线上任意点处的转角(弧度)"""
        # 转角 = l² / (2 * A²) = l / (2 * R)
        if self.spiral_param_a == 0:
            return 0
        return l ** 2 / (2 * self.spiral_param_a ** 2)
    
    def _spiral_radius(self, l: float) -> float:
        """计算螺旋线上任意点处的曲率半径"""
        if l < 1e-6:
            return float('inf') if self.radius_start == 0 else self.radius_start
        return self.spiral_param_a ** 2 / l
    
    def get_point_at(self, station: float) -> Point2D:
        """获取指定桩号对应的坐标(近似计算)"""
        if station < self.start_station or station > self.end_station:
            raise ValueError(f"桩号 {station} 不在螺旋线范围 [{self.start_station}, {self.end_station}] 内")
        
        offset = station - self.start_station
        
        # 使用近似积分计算坐标
        # 将螺旋线分段进行数值积分
        n_segments = max(10, int(offset / 1))  # 每米至少一个分段
        
        x, y = 0.0, 0.0
        ds = offset / n_segments
        
        current_azimuth = self.azimuth_in
        
        for i in range(n_segments):
            l = i * ds + ds / 2  # 中点
            # 该点的切线方向角
            theta = self._spiral_angle(l)
            if self.direction > 0:  # 左转
                theta = -theta
            seg_azimuth = current_azimuth + theta
            # 累加坐标
            x += ds * math.cos(seg_azimuth)
            y += ds * math.sin(seg_azimuth)
        
        # 旋转和平移到起点
        cos_a = math.cos(self.azimuth_in)
        sin_a = math.sin(self.azimuth_in)
        
        final_x = self.start_point.x + x * cos_a - y * sin_a
        final_y = self.start_point.y + x * sin_a + y * cos_a
        
        return Point2D(final_x, final_y)
    
    def get_station_at(self, point: Point2D) -> Optional[float]:
        """计算点对应的桩号(螺旋线段) - 近似解"""
        # 转换到局部坐标系
        dx = point.x - self.start_point.x
        dy = point.y - self.start_point.y
        
        cos_a = math.cos(-self.azimuth_in)
        sin_a = math.sin(-self.azimuth_in)
        
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a
        
        # 近似: 沿起点切线方向的偏移即为桩号增量
        # 这是一个简化计算,实际需要迭代求解
        approx_offset = local_x if abs(self.direction) else math.sqrt(local_x**2 + local_y**2)
        
        if approx_offset < 0 or approx_offset > self.length:
            return None
        
        return self.start_station + approx_offset


# ==================== 竖曲线元素 ====================

@dataclass
class GradeSegment:
    """坡度段"""
    station: float        # 起点桩号
    elevation: float      # 起点高程
    grade: float          # 坡度(%)，上坡为正，下坡为负
    
    def get_elevation_at(self, station: float) -> float:
        """计算指定桩号的高程"""
        offset = station - self.station
        return self.elevation + offset * self.grade / 100


@dataclass
class VerticalCurveElement:
    """竖曲线元素"""
    station_start: float      # 起点桩号
    station_end: float         # 终点桩号
    elevation_start: float     # 起点高程
    elevation_end: float       # 终点高程
    grade_in: float            # 入口坡度(%)
    grade_out: float           # 出口坡度(%)
    curve_type: str = "convex"  # "convex"(凸) 或 "concave"(凹)
    
    @property
    def length(self) -> float:
        return self.station_end - self.station_start
    
    @property
    def radius(self) -> float:
        """竖曲线近似半径"""
        if abs(self.grade_in - self.grade_out) < 1e-6:
            return float('inf')
        # 竖曲线半径 R = L / |i1 - i2| (近似公式)
        return self.length / abs(self.grade_in - self.grade_out) * 100
    
    @property
    def k_value(self) -> float:
        """K值 = 竖曲线长度 / 坡度差"""
        diff = abs(self.grade_in - self.grade_out)
        if diff < 1e-6:
            return float('inf')
        return self.length / diff
    
    def get_elevation_at(self, station: float) -> float:
        """计算指定桩号的高程"""
        if station < self.station_start or station > self.station_end:
            raise ValueError(f"桩号 {station} 不在竖曲线范围 [{self.station_start}, {self.station_end}] 内")
        
        # 切线高程
        offset = station - self.station_start
        tangent_elevation = self.elevation_start + offset * self.grade_in / 100
        
        # 竖曲线改正数
        diff = self.grade_out - self.grade_in  # 坡度差
        # 竖曲线方程: y = (diff / (2 * L)) * x²
        correction = (diff / (2 * self.length)) * offset ** 2 / 100
        
        # 凸曲线向下修正，凹曲线向上修正
        if self.curve_type == "convex":
            return tangent_elevation - correction
        else:
            return tangent_elevation + correction
    
    def get_station_at_elevation(self, elevation: float) -> Optional[float]:
        """根据高程反求桩号(可能有兩個解)"""
        # 这是一个二次方程求解
        # (diff / (2 * L)) * x² + (grade_in / 100) * x + (elevation_start - elevation) = 0
        
        a = (self.grade_out - self.grade_in) / (2 * self.length * 100)
        b = self.grade_in / 100
        c = self.elevation_start - elevation
        
        if abs(a) < 1e-10:
            # 近似直线
            if abs(b) < 1e-10:
                return None
            x = -c / b
            if self.station_start <= x <= self.station_end:
                return x
            return None
        
        # 二次方程求根
        discriminant = b ** 2 - 4 * a * c
        
        if discriminant < 0:
            return None
        
        sqrt_d = math.sqrt(discriminant)
        x1 = (-b + sqrt_d) / (2 * a)
        x2 = (-b - sqrt_d) / (2 * a)
        
        results = []
        for x in [x1, x2]:
            if self.station_start <= x <= self.station_end:
                results.append(x)
        
        return results[0] if results else None


# ==================== 路线/纵断面组合 ====================

@dataclass
class Alignment:
    """路线平纵面组合"""
    elements: List[Union[LineElement, CircularCurveElement, SpiralElement]]
    vertical_elements: List[Union[GradeSegment, VerticalCurveElement]]
    
    def get_point_at(self, station: float) -> Point2D:
        """根据桩号获取平面坐标"""
        for elem in self.elements:
            if hasattr(elem, 'end_station') and hasattr(elem, 'start_station'):
                if elem.start_station <= station <= elem.end_station:
                    return elem.get_point_at(station)
            elif hasattr(elem, 'start_station'):
                if elem.start_station <= station:
                    try:
                        return elem.get_point_at(station)
                    except ValueError:
                        continue
        raise ValueError(f"桩号 {station} 不在任何线元范围内")
    
    def get_station_at(self, point: Point2D) -> Optional[float]:
        """根据坐标获取桩号"""
        best_station = None
        min_dist = float('inf')
        
        for elem in self.elements:
            try:
                station = elem.get_station_at(point)
                if station is not None:
                    # 计算实际距离
                    pt = elem.get_point_at(station)
                    dist = pt.distance_to(point)
                    if dist < min_dist:
                        min_dist = dist
                        best_station = station
            except:
                continue
        
        return best_station
    
    def get_elevation_at(self, station: float) -> float:
        """根据桩号获取高程"""
        for elem in self.vertical_elements:
            if isinstance(elem, GradeSegment):
                if station >= elem.station:
                    return elem.get_elevation_at(station)
            elif isinstance(elem, VerticalCurveElement):
                if elem.station_start <= station <= elem.station_end:
                    return elem.get_elevation_at(station)
        
        # 如果不在任何元素内，尝试使用最后一个元素外推
        if self.vertical_elements:
            last = self.vertical_elements[-1]
            if isinstance(last, GradeSegment):
                return last.get_elevation_at(station)
            elif isinstance(last, VerticalCurveElement) and station > last.station_end:
                return last.get_elevation_at(last.station_end) + (station - last.station_end) * last.grade_out / 100
        
        raise ValueError(f"桩号 {station} 无法计算高程")
    
    def get_point3d_at(self, station: float) -> Point3D:
        """根据桩号获取三维坐标"""
        point2d = self.get_point_at(station)
        elevation = self.get_elevation_at(station)
        return Point3D(point2d.x, point2d.y, elevation)


# ==================== 核心计算函数 ====================

def station_to_point(
    station: float,
    route_id: str = None,
    alignment: Alignment = None,
    elements: List[Union[LineElement, CircularCurveElement, SpiralElement]] = None
) -> Point2D:
    """桩号转坐标
    
    根据路线线元获取指定桩号对应的平面坐标
    
    Args:
        station: 桩号(米)
        route_id: 路线ID(可选,用于数据库查询)
        alignment: 路线平纵面对象
        elements: 线元列表
    
    Returns:
        Point2D: 平面坐标 (x, y)
    
    Example:
        >>> elements = [
        ...     LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=100),
        ...     CircularCurveElement(start_station=100, start_point=Point2D(100, 0), azimuth=0, radius=500, length=50)
        ... ]
        >>> pt = station_to_point(50, elements=elements)
        >>> print(f"x={pt.x}, y={pt.y}")
    """
    if alignment:
        return alignment.get_point_at(station)
    
    if elements:
        for elem in elements:
            try:
                if elem.start_station <= station <= elem.end_station:
                    return elem.get_point_at(station)
            except (AttributeError, ValueError):
                continue
        
        raise ValueError(f"桩号 {station} 不在线元范围内")
    
    raise ValueError("必须提供 alignment 或 elements 参数")


def point_to_station(
    point: Point2D,
    alignment: Alignment = None,
    elements: List[Union[LineElement, CircularCurveElement, SpiralElement]] = None
) -> Optional[float]:
    """坐标转桩号
    
    根据平面坐标计算对应的桩号
    
    Args:
        point: 平面坐标
        alignment: 路线平纵面对象
        elements: 线元列表
    
    Returns:
        float: 桩号(米), 如果点不在线路上返回 None
    
    Example:
        >>> elements = [
        ...     LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=100)
        ... ]
        >>> station = point_to_station(Point2D(50, 0), elements=elements)
        >>> print(f"station={station}")
    """
    if alignment:
        return alignment.get_station_at(point)
    
    if elements:
        best_station = None
        min_dist = float('inf')
        
        for elem in elements:
            try:
                station = elem.get_station_at(point)
                if station is not None:
                    pt = elem.get_point_at(station)
                    dist = pt.distance_to(point)
                    if dist < min_dist:
                        min_dist = dist
                        best_station = station
            except:
                continue
        
        return best_station
    
    raise ValueError("必须提供 alignment 或 elements 参数")


def calculate_horizontal_curve(
    start_station: float,
    start_point: Point2D,
    azimuth_in: float,
    radius: float,
    length: float
) -> CircularCurveElement:
    """创建圆曲线
    
    Args:
        start_station: 起点桩号
        start_point: 起点坐标
        azimuth_in: 起点方位角(弧度)
        radius: 曲线半径(左转为正,右转为负)
        length: 曲线长度
    
    Returns:
        CircularCurveElement: 圆曲线对象
    
    Example:
        >>> curve = calculate_horizontal_curve(
        ...     start_station=100,
        ...     start_point=Point2D(100, 0),
        ...     azimuth_in=0,
=500,
        ...     length=        ...     radius78.54
        ... )
    """
    return CircularCurveElement(
        start_station=start_station,
        start_point=start_point,
        azimuth_in=azimuth_in,
        radius=radius,
        length=length
    )


def calculate_spiral_curve(
    start_station: float,
    start_point: Point2D,
    azimuth_in: float,
    radius_start: float,
    radius_end: float,
    length: float,
    direction: int = 1
) -> SpiralElement:
    """创建螺旋线/缓和曲线
    
    Args:
        start_station: 起点桩号
        start_point: 起点坐标
        azimuth_in: 起点方位角(弧度)
        radius_start: 起点曲率半径(0表示无穷大)
        radius_end: 终点曲率半径
        length: 曲线长度
        direction: 方向 (1=左转, -1=右转)
    
    Returns:
        SpiralElement: 螺旋线对象
    """
    return SpiralElement(
        start_station=start_station,
        start_point=start_point,
        azimuth_in=azimuth_in,
        radius_start=radius_start,
        radius_end=radius_end,
        length=length,
        direction=direction
    )


def calculate_vertical_curve(
    station_start: float,
    station_end: float,
    elevation_start: float,
    elevation_end: float,
    grade_in: float,
    grade_out: float
) -> VerticalCurveElement:
    """创建竖曲线
    
    Args:
        station_start: 起点桩号
        station_end: 终点桩号
        elevation_start: 起点高程
        elevation_end: 终点高程
        grade_in: 入口坡度(%)
        grade_out: 出口坡度(%)
    
    Returns:
        VerticalCurveElement: 竖曲线对象
    
    Example:
        >>> vc = calculate_vertical_curve(
        ...     station_start=100,
        ...     station_end=200,
        ...     elevation_start=50,
        ...     elevation_end=55,
        ...     grade_in=3,
        ...     grade_out=-2
        ... )
        >>> elev = vc.get_elevation_at(150)
    """
    # 判断曲线类型
    is_convex = (grade_out - grade_in) < 0  # 坡度下降为凸曲线
    
    return VerticalCurveElement(
        station_start=station_start,
        station_end=station_end,
        elevation_start=elevation_start,
        elevation_end=elevation_end,
        grade_in=grade_in,
        grade_out=grade_out,
        curve_type="convex" if is_convex else "concave"
    )


# ==================== 辅助函数 ====================

def format_station(station: float) -> str:
    """格式化桩号显示
    
    Args:
        station: 桩号(米)
    
    Returns:
        str: 格式化后的桩号, 如 "K1+200"
    
    Example:
        >>> format_station(1200)
        'K1+200'
    """
    km = int(station // 1000)
    m = int(station % 1000)
    if km > 0:
        return f"K{km}+{m:03d}"
    return f"0+{m:03d}"


def parse_station(station_str: str) -> float:
    """解析桩号字符串
    
    Args:
        station_str: 桩号字符串, 如 "K1+200"
    
    Returns:
        float: 桩号(米)
    
    Example:
        >>> parse_station("K1+200")
        1200.0
    """
    import re
    match = re.match(r'K?(\d+)\+(\d+)', station_str)
    if match:
        km = int(match.group(1))
        m = int(match.group(2))
        return km * 1000 + m
    return float(station_str)


def degrees_to_radians(degrees: float) -> float:
    """角度转弧度"""
    return degrees * math.pi / 180


def radians_to_degrees(radians: float) -> float:
    """弧度转角度"""
    return radians * 180 / math.pi


# ==================== 导出 ====================

__all__ = [
    'Point2D',
    'Point3D', 
    'Vector2D',
    'LineElement',
    'CircularCurveElement',
    'SpiralElement',
    'GradeSegment',
    'VerticalCurveElement',
    'Alignment',
    'station_to_point',
    'point_to_station',
    'calculate_horizontal_curve',
    'calculate_spiral_curve',
    'calculate_vertical_curve',
    'format_station',
    'parse_station',
    'degrees_to_radians',
    'radians_to_degrees',
]
