#!/usr/bin/env python
# Test script for spatial calculator

from spatial import (
    Point2D, Point3D, LineElement, CircularCurveElement, 
    SpiralElement, Alignment, station_to_point, point_to_station,
    format_station, degrees_to_radians
)

print("=" * 50)
print("Testing NeuralSite Spatial Calculator")
print("=" * 50)

# Test 1: 直线计算
print("\n--- Test 1: Line Element ---")
line = LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=100)
pt = line.get_point_at(50)
print(f"Line point at station 50: ({pt.x:.2f}, {pt.y:.2f})")
assert abs(pt.x - 50) < 0.01 and abs(pt.y - 0) < 0.01

# Test 2: 圆曲线计算
print("\n--- Test 2: Circular Curve ---")
curve = CircularCurveElement(
    start_station=100, 
    start_point=Point2D(100, 0), 
    azimuth_in=0, 
    radius=500, 
    length=78.54  # ~45度
)
pt_curve = curve.get_point_at(139.27)
print(f"Curve point at station 139.27: ({pt_curve.x:.2f}, {pt_curve.y:.2f})")

# Test 3: station_to_point 函数
print("\n--- Test 3: station_to_point ---")
elements = [line, curve]
result = station_to_point(50, elements=elements)
print(f"station_to_point(50): ({result.x:.2f}, {result.y:.2f})")
assert abs(result.x - 50) < 0.01

# Test 4: format_station
print("\n--- Test 4: format_station ---")
formatted = format_station(1200)
print(f"format_station(1200): {formatted}")
assert formatted == "K1+200"

# Test 5: 45度方向直线
print("\n--- Test 5: 45-degree direction line ---")
line2 = LineElement(
    start_station=0, 
    start_point=Point2D(0, 0), 
    azimuth=degrees_to_radians(45), 
    length=100
)
pt45 = line2.get_point_at(50)
print(f"45度方向50米处: ({pt45.x:.2f}, {pt45.y:.2f})")
expected = 50 * 0.70710678  # 50/sqrt(2)
assert abs(pt45.x - expected) < 0.01
assert abs(pt45.y - expected) < 0.01

# Test 6: point_to_station (坐标转桩号)
print("\n--- Test 6: point_to_station ---")
station = point_to_station(Point2D(50, 0), elements=[line])
print(f"point_to_station(Point2D(50, 0)): {station}")
assert station == 50.0

# Test 7: 完整路线计算
print("\n--- Test 7: Complete Alignment ---")
alignment_elements = [
    LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=200),
    CircularCurveElement(start_station=200, start_point=Point2D(200, 0), azimuth_in=0, radius=500, length=100),
    LineElement(start_station=300, start_point=None, azimuth=0, length=200)  # 这需要修复
]

# 正确的完整路线
line1 = LineElement(start_station=0, start_point=Point2D(0, 0), azimuth=0, length=200)
curve1 = CircularCurveElement(start_station=200, start_point=line1.end_point, azimuth_in=0, radius=500, length=100)
line2 = LineElement(start_station=300, start_point=curve1.end_point, azimuth=curve1.azimuth_in + curve1.central_angle, length=200)

full_elements = [line1, curve1, line2]
pt_full = station_to_point(350, elements=full_elements)
print(f"Point at station 350: ({pt_full.x:.2f}, {pt_full.y:.2f})")

print("\n" + "=" * 50)
print("All tests passed!")
print("=" * 50)
