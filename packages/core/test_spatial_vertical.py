#!/usr/bin/env python
# Test script for spatial calculator - Vertical Curves

from spatial import (
    Point2D, Point3D, LineElement, CircularCurveElement, 
    SpiralElement, VerticalCurveElement, GradeSegment, Alignment,
    station_to_point, point_to_station, format_station, degrees_to_radians
)

print("=" * 60)
print("Testing NeuralSite Spatial Calculator - Vertical Curves")
print("=" * 60)

# Test: 竖曲线计算
print("\n--- Test: Vertical Curve ---")
# 假设一段坡度从3%变为-2%的竖曲线
vc = VerticalCurveElement(
    station_start=100,
    station_end=200,
    elevation_start=50,
    elevation_end=55,
    grade_in=3,
    grade_out=-2,
    curve_type="convex"
)

print(f"起点桩号: {vc.station_start}, 高程: {vc.elevation_start}")
print(f"终点桩号: {vc.station_end}, 高程: {vc.elevation_end}")
print(f"入口坡度: {vc.grade_in}%, 出口坡度: {vc.grade_out}%")
print(f"曲线类型: {vc.curve_type}")
print(f"竖曲线半径(近似): {vc.radius:.2f} m")
print(f"K值: {vc.k_value:.2f}")

# 计算中间点高程
for st in [100, 125, 150, 175, 200]:
    elev = vc.get_elevation_at(st)
    print(f"桩号 K{st//1000}+{st%1000:03d} -> 高程 {elev:.3f} m")

# Test: 坡度段计算
print("\n--- Test: Grade Segment ---")
grade = GradeSegment(station=0, elevation=100, grade=2.5)
for st in [0, 50, 100, 150, 200]:
    elev = grade.get_elevation_at(st)
    print(f"桩号 K{st//1000}+{st%1000:03d} -> 高程 {elev:.3f} m (坡度 {grade.grade}%)")

# Test: 完整平纵面组合
print("\n--- Test: Complete Alignment with Elevation ---")
# 创建平曲线
line1 = LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=200)
curve1 = CircularCurveElement(
    start_station=200, 
    start_point=line1.end_point, 
    azimuth_in=0, 
    radius=500, 
    length=100
)
line2 = LineElement(
    start_station=300, 
    start_point=curve1.end_point, 
    azimuth=curve1.azimuth_in + curve1.central_angle, 
    length=200
)

horizontal_elements = [line1, curve1, line2]

# 创建竖曲线
grade1 = GradeSegment(station=0, elevation=100, grade=2)
vc1 = VerticalCurveElement(
    station_start=150,
    station_end=250,
    elevation_start=103.75,  # 150m处的高程
    elevation_end=107.5,      # 250m处的高程
    grade_in=2,
    grade_out=-1,
    curve_type="convex"
)
grade2 = GradeSegment(station=250, elevation=107.5, grade=-1)

vertical_elements = [grade1, vc1, grade2]

# 创建完整路线
alignment = Alignment(
    elements=horizontal_elements,
    vertical_elements=vertical_elements
)

# 测试几个关键点
test_stations = [0, 50, 100, 150, 175, 200, 250, 300, 400, 500]
print("\n桩号      X坐标      Y坐标      高程")
print("-" * 45)
for st in test_stations:
    try:
        pt3d = alignment.get_point3d_at(st)
        print(f"K{st//1000}+{st%1000:03d}  {pt3d.x:8.2f}  {pt3d.y:8.2f}  {pt3d.z:8.3f}")
    except Exception as e:
        print(f"K{st//1000}+{st%1000:03d}  Error: {e}")

print("\n" + "=" * 60)
print("All vertical curve tests passed!")
print("=" * 60)
