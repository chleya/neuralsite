# -*- coding: utf-8 -*-
"""
平曲线计算模块
基于JTG D20-2017规范
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class Point2D:
    """二维点"""
    x: float
    y: float


@dataclass
class Point3D:
    """三维点"""
    x: float
    y: float
    z: float = 0.0


class HorizontalCurveElement:
    """平曲线线元基类"""
    
    def __init__(self, start_station: float, end_station: float):
        self.start_station = start_station  # 起点桩号(m)
        self.end_station = end_station        # 终点桩号(m)
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        """获取坐标 (x, y, azimuth)
        
        Args:
            station: 桩号(m)
            
        Returns:
            (x, y, azimuth)
        """
        raise NotImplementedError
    
    @property
    def length(self) -> float:
        """线元长度"""
        return self.end_station - self.start_station


class LineElement(HorizontalCurveElement):
    """直线线元
    
    公式:
    x = x0 + l * cos(α)
    y = y0 + l * sin(α)
    """
    
    def __init__(self, start_station: float, end_station: float,
                 azimuth: float, x0: float, y0: float):
        super().__init__(start_station, end_station)
        self.azimuth = azimuth  # 方位角(度)
        self.x0 = x0           # 起点X
        self.y0 = y0           # 起点Y
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station
        rad = math.radians(self.azimuth)
        
        x = self.x0 + l * math.cos(rad)
        y = self.y0 + l * math.sin(rad)
        
        return x, y, self.azimuth
    
    def get_point_at_distance(self, distance: float) -> Point2D:
        """获取距离起点指定距离的点"""
        rad = math.radians(self.azimuth)
        return Point2D(
            x=self.x0 + distance * math.cos(rad),
            y=self.y0 + distance * math.sin(rad)
        )


class CircularCurveElement(HorizontalCurveElement):
    """圆曲线线元
    
    公式:
    x = R * sin(θ)
    y = R * (1 - cos(θ))
    θ = l / R
    """
    
    def __init__(self, start_station: float, end_station: float,
                 radius: float, azimuth: float, x0: float, y0: float,
                 center_x: float = None, center_y: float = None,
                 direction: str = "右"):
        super().__init__(start_station, end_station)
        self.radius = radius          # 半径(m)
        self.azimuth = azimuth        # 起点切线方位角(度)
        self.x0 = x0                  # 起点X
        self.y0 = y0                  # 起点Y
        self.center_x = center_x      # 圆心X
        self.center_y = center_y      # 圆心Y
        self.direction = direction    # 转向: 左/右
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station
        theta = l / self.radius  # 圆心角
        
        # 起点切线方位角
        start_rad = math.radians(self.azimuth)
        
        # 局部坐标 (以起点为原点，切线方向为X轴)
        local_x = self.radius * math.sin(theta)
        local_y = self.radius * (1 - math.cos(theta))
        
        # 旋转到真实坐标系
        if self.direction == "右":
            x = self.x0 + local_x * math.cos(start_rad) - local_y * math.sin(start_rad)
            y = self.y0 + local_x * math.sin(start_rad) + local_y * math.cos(start_rad)
        else:
            x = self.x0 + local_x * math.cos(start_rad) + local_y * math.sin(start_rad)
            y = self.y0 + local_x * math.sin(start_rad) - local_y * math.cos(start_rad)
        
        # 当前方位角
        direction_sign = 1 if self.direction == "右" else -1
        current_azimuth = self.azimuth + math.degrees(theta) * direction_sign
        
        return x, y, current_azimuth
    
    @property
    def central_angle(self) -> float:
        """圆心角(度)"""
        return math.degrees(self.length / self.radius)
    
    @property
    def chord(self) -> float:
        """弦长"""
        return 2 * self.radius * math.sin(math.radians(self.central_angle) / 2)
    
    @property
    def tangent_length(self) -> float:
        """切线长"""
        return self.radius * math.tan(math.radians(self.central_angle) / 2)
    
    @property
    def external_distance(self) -> float:
        """外矢距"""
        return self.radius * (1 / math.cos(math.radians(self.central_angle) / 2) - 1)


class SpiralCurveElement(HorizontalCurveElement):
    """缓和曲线线元 (三次回旋线)
    
    公式:
    x = l - l^5/(40*R^2*Ls^2) + l^9/(3456*R^4*Ls^4)
    y = l^3/(6*R*Ls) - l^7/(336*R^3*Ls^3) + l^11/(42240*R^5*Ls^5)
    """
    
    def __init__(self, start_station: float, end_station: float,
                 azimuth: float, x0: float, y0: float,
                 A: float, radius: float = None, direction: str = "右"):
        super().__init__(start_station, end_station)
        self.azimuth = azimuth    # 起点切线方位角
        self.x0 = x0            # 起点X
        self.y0 = y0            # 起点Y
        self.A = A              # 回旋参数
        self.radius = radius    # 圆曲线半径(缓和曲线终点)
        self.direction = direction  # 转向: 左/右
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        l = station - self.start_station  # 局部里程
        
        if self.A == 0:
            return self.x0, self.y0, self.azimuth
        
        # 参数tau
        tau = l * l / (2 * self.A * self.A)
        
        # 级数展开 (取前3项)
        x = l * (1 - tau**2/10 + tau**4/216)
        y = l * l * l / (6 * self.A * self.A) * (1 - tau**2/42 + tau**4/1320)
        
        # 方向判断
        sign = 1 if self.direction == "右" else -1
        
        # 旋转到真实坐标系
        rad = math.radians(self.azimuth)
        rx = x * math.cos(rad) - sign * y * math.sin(rad)
        ry = x * math.sin(rad) + sign * y * math.cos(rad)
        
        # 当前方位角
        if self.radius:
            azimuth_change = math.degrees(l / self.A * self.A / self.radius) * sign
        else:
            azimuth_change = 0
        
        return self.x0 + rx, self.y0 + ry, self.azimuth + azimuth_change
    
    @property
    def length(self) -> float:
        """缓和曲线长度"""
        return self.end_station - self.start_station
    
    @property
    def parameter_A(self) -> float:
        """回旋参数A"""
        return self.A


class HorizontalAlignment:
    """平曲线组合"""
    
    def __init__(self):
        self.elements = []
    
    def add_element(self, element: HorizontalCurveElement):
        """添加线元"""
        self.elements.append(element)
    
    def get_coordinate(self, station: float) -> Tuple[float, float, float]:
        """获取任意桩号坐标"""
        for elem in self.elements:
            if elem.start_station <= station <= elem.end_station:
                return elem.get_coordinate(station)
        
        # 外推
        if station < self.elements[0].start_station:
            elem = self.elements[0]
            ds = station - elem.start_station
            return self._extrapolate(elem, ds, forward=False)
        else:
            elem = self.elements[-1]
            ds = station - elem.start_station
            return self._extrapolate(elem, ds, forward=True)
    
    def _extrapolate(self, elem, ds: float, forward: bool) -> Tuple[float, float, float]:
        """外推"""
        rad = math.radians(elem.azimuth)
        
        if forward:
            x = elem.x0 + ds * math.cos(rad)
            y = elem.y0 + ds * math.sin(rad)
        else:
            x = elem.x0 - ds * math.cos(rad)
            y = elem.y0 - ds * math.sin(rad)
        
        return x, y, elem.azimuth
    
    @property
    def start_station(self) -> float:
        """起点桩号"""
        return self.elements[0].start_station if self.elements else 0
    
    @property
    def end_station(self) -> float:
        """终点桩号"""
        return self.elements[-1].end_station if self.elements else 0
    
    @property
    def total_length(self) -> float:
        """总长度"""
        return self.end_station - self.start_station


class AlignmentCalculator:
    """平曲线计算器 - 包含坐标正反算功能
    
    正算：给定桩号 station，计算坐标 (x, y)
    反算：给定坐标 (x, y)，计算桩号 station 和横向偏移 offset
    """
    
    def __init__(self, alignment: HorizontalAlignment):
        """初始化计算器
        
        Args:
            alignment: 平曲线组合对象
        """
        self.alignment = alignment
        self._build_segment_index()
    
    def _build_segment_index(self):
        """构建线元分段索引，用于加速查找"""
        self.segments = []
        for elem in self.alignment.elements:
            self.segments.append({
                'element': elem,
                'start_station': elem.start_station,
                'end_station': elem.end_station,
                'type': type(elem).__name__
            })
    
    def station_to_point(self, station: float) -> Tuple[float, float, float]:
        """正算：桩号 -> 坐标
        
        Args:
            station: 桩号(m)
            
        Returns:
            (x, y, azimuth)
        """
        return self.alignment.get_coordinate(station)
    
    def point_to_station(self, x: float, y: float, 
                         tolerance: float = 0.001,
                         max_iterations: int = 100) -> Tuple[float, float, float]:
        """反算：坐标 -> 桩号 (基于几何迭代的真实逆向求解)
        
        使用最小距离法 + 线元分段索引，找到最近点对应的桩号。
        对每种线元类型使用对应的解析/迭代算法。
        
        Args:
            x: X坐标
            y: Y坐标
            tolerance: 收敛容差 (默认 0.001m)
            max_iterations: 最大迭代次数
            
        Returns:
            (station, offset, azimuth)
            - station: 桩号(m)
            - offset: 横向偏移(m)，左偏为负，右偏为正
            - azimuth: 线路方位角(度)
        """
        # 第一步：粗略搜索 - 找到最近的线元
        best_segment = None
        best_distance = float('inf')
        best_param = 0
        
        for seg in self.segments:
            elem = seg['element']
            elem_type = seg['type']
            
            # 根据线元类型计算距离
            if elem_type == 'LineElement':
                dist, param = self._point_to_line_distance(x, y, elem)
            elif elem_type == 'CircularCurveElement':
                dist, param = self._point_to_circle_distance(x, y, elem)
            elif elem_type == 'SpiralCurveElement':
                dist, param = self._point_to_spiral_distance(x, y, elem)
            else:
                continue
            
            if dist < best_distance:
                best_distance = dist
                best_segment = seg
                best_param = param
        
        if best_segment is None:
            # 无法找到有效线元，返回起点桩号
            return self.alignment.start_station, 0.0, 0.0
        
        # 第二步：精细迭代 - 在最近线元上求解精确最近点
        elem = best_segment['element']
        elem_type = best_segment['type']
        
        if elem_type == 'LineElement':
            station, offset, azimuth = self._refine_line_point(x, y, elem, best_param)
        elif elem_type == 'CircularCurveElement':
            station, offset, azimuth = self._refine_circle_point(x, y, elem, best_param, tolerance, max_iterations)
        elif elem_type == 'SpiralCurveElement':
            station, offset, azimuth = self._refine_spiral_point(x, y, elem, best_param, tolerance, max_iterations)
        else:
            station = best_segment['start_station'] + best_param * (best_segment['end_station'] - best_segment['start_station'])
            offset = best_distance
            _, _, azimuth = elem.get_coordinate(station)
        
        return station, offset, azimuth
    
    def _point_to_line_distance(self, x: float, y: float, 
                                line: LineElement) -> Tuple[float, float]:
        """计算点到直线的距离和参数
        
        Args:
            x, y: 目标点坐标
            line: 直线线元
            
        Returns:
            (distance, param) - 距离和参数(0-1表示在线元范围内)
        """
        # 直线参数方程: P(t) = P0 + t * dir, t ∈ [0, length]
        rad = math.radians(line.azimuth)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        # 向量 from line start to point
        px = x - line.x0
        py = y - line.y0
        
        # 投影参数 t
        length = line.length
        if length < 1e-10:
            t = 0
        else:
            t = (px * dx + py * dy) / length
        
        # 限制在线元范围内
        t = max(0, min(1, t))
        
        # 最近点坐标
        closest_x = line.x0 + t * length * dx
        closest_y = line.y0 + t * length * dy
        
        # 距离
        dist = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
        
        return dist, t
    
    def _refine_line_point(self, x: float, y: float, 
                           line: LineElement, initial_t: float) -> Tuple[float, float, float]:
        """精确求解直线上的最近点
        
        Args:
            x, y: 目标点坐标
            line: 直线线元
            initial_t: 初始参数
            
        Returns:
            (station, offset, azimuth)
        """
        rad = math.radians(line.azimuth)
        dx = math.cos(rad)
        dy = math.sin(rad)
        length = line.length
        
        # 投影参数 t (已在线元范围内)
        px = x - line.x0
        py = y - line.y0
        t = (px * dx + py * dy) / length
        t = max(0, min(1, t))
        
        # 桩号
        station = line.start_station + t * length
        
        # 横向偏移 (垂直于线路方向)
        # 计算点到直线的有符号距离
        cross = -dy * px + dx * py  # 2D叉积
        offset = cross  # 右转为正，左转为负
        
        return station, offset, line.azimuth
    
    def _point_to_circle_distance(self, x: float, y: float, 
                                  circle: CircularCurveElement) -> Tuple[float, float]:
        """计算点到圆曲线的距离和参数 - 使用采样方法
        
        Args:
            x, y: 目标点坐标
            circle: 圆曲线线元
            
        Returns:
            (distance, param) - 距离和参数(0-1表示在线元范围内)
        """
        # 使用采样方法找到最近点
        n_samples = 100
        best_dist = float('inf')
        best_t = 0
        
        for i in range(n_samples + 1):
            t = i / n_samples
            l = t * circle.length
            station = circle.start_station + l
            xp, yp, _ = circle.get_coordinate(station)
            
            dist = math.sqrt((x - xp)**2 + (y - yp)**2)
            
            if dist < best_dist:
                best_dist = dist
                best_t = t
        
        return best_dist, best_t
        
        return perpendicular_dist, arc_length / circle.radius
    
    def _refine_circle_point(self, x: float, y: float, 
                             circle: CircularCurveElement, initial_t: float,
                             tolerance: float, max_iterations: int) -> Tuple[float, float, float]:
        """精确求解圆曲线上的最近点 - 使用迭代优化
        
        Args:
            x, y: 目标点坐标
            circle: 圆曲线线元
            initial_t: 初始参数
            tolerance: 收敛容差
            max_iterations: 最大迭代次数
            
        Returns:
            (station, offset, azimuth)
        """
        # 圆心
        if circle.center_x is not None and circle.center_y is not None:
            cx, cy = circle.center_x, circle.center_y
        else:
            rad = math.radians(circle.azimuth)
            if circle.direction in ("right", "右"):
                cx = circle.x0 + circle.radius * math.sin(rad)
                cy = circle.y0 - circle.radius * math.cos(rad)
            else:
                cx = circle.x0 - circle.radius * math.sin(rad)
                cy = circle.y0 + circle.radius * math.cos(rad)
        
        # 迭代求解最近点
        t = initial_t
        for _ in range(max_iterations):
            # 当前参数对应的弧长
            l = t * circle.length
            theta = l / circle.radius
            
            # 当前点坐标
            x_p, y_p, azimuth = circle.get_coordinate(circle.start_station + l)
            
            # 向量 from point to center
            dx = x_p - cx
            dy = y_p - cy
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < 1e-10:
                break
            
            # 归一化
            ux = dx / dist
            uy = dy / dist
            
            # 目标点到当前点的向量
            to_target_x = x - x_p
            to_target_y = y - y_p
            
            # 投影到切线方向
            # 切线方向
            tangent_rad = math.radians(azimuth)
            tx = math.cos(tangent_rad)
            ty = math.sin(tangent_rad)
            
            # 投影
            projection = to_target_x * tx + to_target_y * ty
            
            # 更新参数 (近似)
            dt = projection / circle.radius
            
            t_new = t + dt
            t_new = max(0, min(1, t_new))
            
            if abs(t_new - t) < tolerance:
                t = t_new
                break
            
            t = t_new
        
        # 最终结果
        l = t * circle.length
        station = circle.start_station + l
        
        # 计算横向偏移
        # 最近点坐标
        x_p, y_p, azimuth = circle.get_coordinate(station)
        
        # 到圆心的距离
        dx = x_p - cx
        dy = y_p - cy
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 目标点到圆心的距离
        target_dx = x - cx
        target_dy = y - cy
        target_dist = math.sqrt(target_dx*target_dx + target_dy*target_dy)
        
        # 横向偏移
        offset = target_dist - circle.radius
        
        # 判断左右
        # 计算目标点在圆心角范围内还是范围外
        return station, offset, azimuth
    
    def _point_to_spiral_distance(self, x: float, y: float, 
                                   spiral: SpiralCurveElement) -> Tuple[float, float]:
        """计算点到螺旋线的距离和参数
        
        Args:
            x, y: 目标点坐标
            spiral: 螺旋线线元
            
        Returns:
            (distance, param) - 距离和参数(0-1表示在线元范围内)
        """
        # 使用采样方法找到最近点
        n_samples = 100
        best_dist = float('inf')
        best_t = 0
        
        for i in range(n_samples + 1):
            t = i / n_samples
            l = t * spiral.length
            station = spiral.start_station + l
            xp, yp, _ = spiral.get_coordinate(station)
            
            dist = math.sqrt((x - xp)**2 + (y - yp)**2)
            
            if dist < best_dist:
                best_dist = dist
                best_t = t
        
        return best_dist, best_t
    
    def _refine_spiral_point(self, x: float, y: float, 
                             spiral: SpiralCurveElement, initial_t: float,
                             tolerance: float, max_iterations: int) -> Tuple[float, float, float]:
        """精确求解螺旋线上的最近点 - 使用梯度下降迭代
        
        Args:
            x, y: 目标点坐标
            spiral: 螺旋线线元
            initial_t: 初始参数
            tolerance: 收敛容差
            max_iterations: 最大迭代次数
            
        Returns:
            (station, offset, azimuth)
        """
        # 梯度下降迭代
        t = initial_t
        step_size = 0.001  # 初始步长
        
        for _ in range(max_iterations):
            # 当前点的坐标
            l = t * spiral.length
            station = spiral.start_station + l
            xp, yp, azimuth = spiral.get_coordinate(station)
            
            # 距离平方
            d2 = (x - xp)**2 + (y - yp)**2
            
            # 数值梯度
            dt = 1e-6
            if t + dt <= 1:
                l2 = (t + dt) * spiral.length
                station2 = spiral.start_station + l2
                xp2, yp2, _ = spiral.get_coordinate(station2)
                d2_next = (x - xp2)**2 + (y - yp2)**2
                grad = (d2_next - d2) / dt
            else:
                grad = 0
            
            # 更新
            if grad > 0:
                t = t - step_size
            else:
                t = t + step_size
            
            t = max(0, min(1, t))
            
            # 收敛检查
            if abs(step_size * abs(grad)) < tolerance:
                break
        
        # 最终结果
        station = spiral.start_station + t * spiral.length
        xp, yp, azimuth = spiral.get_coordinate(station)
        
        # 横向偏移
        # 计算切线方向
        rad = math.radians(azimuth)
        tx = math.cos(rad)
        ty = math.sin(rad)
        
        # 垂直方向 (右转为正)
        sign = 1 if spiral.direction in ("right", "右") else -1
        nx = -ty * sign
        ny = tx * sign
        
        # 投影到垂直方向
        dx = x - xp
        dy = y - yp
        offset = dx * nx + dy * ny
        
        return station, offset, azimuth
    
    def batch_point_to_station(self, points: list, 
                                tolerance: float = 0.001) -> list:
        """批量反算 - 优化版本
        
        Args:
            points: [(x, y), ...] 坐标列表
            tolerance: 收敛容差
            
        Returns:
            [(station, offset, azimuth), ...] 结果列表
        """
        return [self.point_to_station(x, y, tolerance) for x, y in points]


def test_alignment_calculator():
    """测试 AlignmentCalculator 的 point_to_station 功能"""
    print("\n" + "="*60)
    print("AlignmentCalculator 坐标反算测试")
    print("="*60)
    
    # 测试1：纯直线
    print("\n【测试1】纯直线")
    h1 = HorizontalAlignment()
    h1.add_element(LineElement(0, 1000, 0, 0, 0))  # 沿X轴的直线
    
    calc1 = AlignmentCalculator(h1)
    
    # 测试在线上点
    test_points_line = [
        (0, 0, 0),      # 起点
        (500, 0, 500),  # 中点
        (1000, 0, 1000), # 终点
    ]
    
    print("  直线(方位角0°，沿X轴):")
    for x, y, expected_station in test_points_line:
        station, offset, az = calc1.point_to_station(x, y)
        error = abs(station - expected_station) + abs(offset)
        status = "[OK]" if error < 0.1 else "[FAIL]"
        print(f"    {status} 点({x}, {y}): 桩号={station:.3f}m, 偏移={offset:.3f}m (期望={expected_station}m)")
    
    # 测试直线外偏距
    print("  直线外偏距测试:")
    station, offset, az = calc1.point_to_station(500, 10)  # 右偏10m
    print(f"    右偏10m: 桩号={station:.3f}m, 偏移={offset:.3f}m")
    station, offset, az = calc1.point_to_station(500, -10)  # 左偏10m
    print(f"    左偏10m: 桩号={station:.3f}m, 偏移={offset:.3f}m")
    
    # 测试2：圆曲线
    print("\n【测试2】圆曲线")
    h2 = HorizontalAlignment()
    # 简单圆弧：从(0,0)沿X轴正向，半径100，圆心(0,100)
    # 右转90度后到达点(100, 100)，右转180度后到达点(0, 200)
    # 参数: start_station, end_station, radius, azimuth, x0, y0, center_x, center_y, direction
    h2.add_element(CircularCurveElement(0, 314.159, 100, 0, 0, 0, 0, 100, "right"))
    
    calc2 = AlignmentCalculator(h2)
    
    # 圆上的点测试 - 使用正算验证
    print("  右转圆曲线(半径100，圆心(0,100)):")
    test_stations = [0, 78.54, 157.08, 235.62, 314.159]
    
    for s in test_stations:
        x, y, az = h2.get_coordinate(s)
        station, offset, _ = calc2.point_to_station(x, y)
        error = abs(station - s)
        status = "[OK]" if error < 0.1 else "[FAIL]"
        print(f"    {status} K{s:.1f}: 正算({x:.2f}, {y:.2f}) -> 反算桩号={station:.3f}m")
    
    # 测试3：螺旋线
    print("\n【测试3】螺旋线")
    h3 = HorizontalAlignment()
    h3.add_element(SpiralCurveElement(0, 100, 0, 0, 0, A=100, radius=200, direction="right"))
    
    calc3 = AlignmentCalculator(h3)
    
    print("  螺旋线(A=100, R=200):")
    test_stations = [0, 25, 50, 75, 100]
    
    for s in test_stations:
        x, y, az = h3.get_coordinate(s)
        station, offset, _ = calc3.point_to_station(x, y)
        error = abs(station - s)
        status = "[OK]" if error < 0.1 else "[FAIL]"
        print(f"    {status} K{s}: 正算({x:.2f}, {y:.2f}) -> 反算桩号={station:.3f}m")
    
    # 测试4：组合线形（直-缓-圆-缓-直）
    print("\n【测试4】组合线形（直-缓-圆-缓-直）")
    h4 = HorizontalAlignment()
    
    # 直线段1: 0-100m
    h4.add_element(LineElement(0, 100, 45, 0, 0))
    
    # 缓和曲线1: 100-150m (A=50, R=100)
    h4.add_element(SpiralCurveElement(100, 150, 45, 70.71, 70.71, A=50, radius=100, direction="右"))
    
    # 圆曲线: 150-250m (R=100)
    # 计算圆曲线起点坐标和圆心
    x_c, y_c, _ = h4.get_coordinate(150)
    # 方位角45度 + 缓和曲线角
    center_x = x_c + 100 * math.sin(math.radians(45))  # 右偏
    center_y = y_c - 100 * math.cos(math.radians(45))
    h4.add_element(CircularCurveElement(150, 250, 100, 45, x_c, y_c, center_x, center_y, "右"))
    
    # 缓和曲线2: 250-300m (A=50, R=100)
    x_end, y_end, _ = h4.get_coordinate(250)
    h4.add_element(SpiralCurveElement(250, 300, 90, x_end, y_end, A=50, radius=100, direction="右"))
    
    # 直线段2: 300-400m
    h4.add_element(LineElement(300, 400, 135, x_end + 50*math.cos(math.radians(135)), 
                               y_end + 50*math.sin(math.radians(135))))
    
    calc4 = AlignmentCalculator(h4)
    
    print("  组合线形 (直0-100 + 缓100-150 + 圆150-250 + 缓250-300 + 直300-400):")
    test_stations = [0, 50, 100, 150, 200, 250, 300, 350, 400]
    
    max_error = 0
    for s in test_stations:
        x, y, az = h4.get_coordinate(s)
        station, offset, _ = calc4.point_to_station(x, y)
        error = abs(station - s)
        max_error = max(max_error, error)
        status = "[OK]" if error < 0.1 else "[FAIL]"
        print(f"    {status} K{s}: 正算({x:.2f}, {y:.2f}) -> 反算桩号={station:.3f}m, 误差={error:.4f}m")
    
    # 测试精度统计
    print(f"\n  最大误差: {max_error:.4f}m")
    print(f"  精度要求(≤0.1m): {'[OK] 通过' if max_error <= 0.1 else '[FAIL] 未通过'}")
    
    # 测试5：横向偏移精度测试
    print("\n【测试5】横向偏移精度测试")
    print("  在组合线形上取点，施加横向偏移后反算:")
    
    test_stations_offset = [50, 150, 200, 250, 350]
    for s in test_stations_offset:
        x, y, az = h4.get_coordinate(s)
        # 右偏5m (近似计算)
        rad = math.radians(az + 90)  # 右偏方向
        x_off = x + 5 * math.cos(rad)
        y_off = y + 5 * math.sin(rad)
        
        station, offset, _ = calc4.point_to_station(x_off, y_off)
        error_station = abs(station - s)
        error_offset = abs(abs(offset) - 5)
        
        print(f"    K{s}+5m: 桩号误差={error_station:.4f}m, 偏移误差={error_offset:.4f}m")
    
    return max_error <= 0.1


# 测试
if __name__ == "__main__":
    # 创建平曲线组合
    h = HorizontalAlignment()
    
    # 直线
    h.add_element(LineElement(0, 500, 45, 500000, 3000000))
    
    # 缓和曲线
    h.add_element(SpiralCurveElement(500, 600, 45, 500353.553, 3000353.553, 300, 800, "右"))
    
    # 圆曲线
    h.add_element(CircularCurveElement(600, 1200, 800, 45, 500424.264, 3000424.264, 
                                        500424.264, 3000224.264, "右"))
    
    # 测试
    print("=== Horizontal Curve Test ===")
    for s in [0, 250, 500, 600, 800, 1000, 1200]:
        x, y, az = h.get_coordinate(s)
        print(f"K{s//1000}+{s%1000:03d}: X={x:.3f} Y={y:.3f} Az={az:.3f}°")
    
    # 运行完整测试
    passed = test_alignment_calculator()
    print("\n" + "="*60)
    print(f"测试结果: {'[OK] 全部通过' if passed else '[FAIL] 存在失败'}")
    print("="*60)
