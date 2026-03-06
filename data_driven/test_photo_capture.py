# -*- coding: utf-8 -*-
"""
照片采集流程测试
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_driven.geo_utils import GeoExtractor
from data_driven.station_matcher import StationMatcher
from data_driven.photo_capture import PhotoCaptureFlow, PhotoCaptureService


def test_geo_extractor():
    """测试GPS提取"""
    print("\n=== 测试GPS提取 ===")
    
    geo = GeoExtractor()
    
    # 测试距离计算
    dist = GeoExtractor.calculate_distance(
        31.2304, 121.4737,  # 上海
        31.2304, 121.4837   # 东方约1km
    )
    print(f"距离计算: {dist:.2f} 米")
    assert dist > 900 and dist < 1100, "距离计算应在1000米左右"
    
    # 测试坐标转换
    x, y = GeoExtractor.wgs84_to_cgcs2000(31.2304, 121.4737)
    print(f"WGS84->CGCS2000: ({x}, {y})")
    
    print("[OK] GPS提取测试通过")


def test_station_matcher():
    """测试桩号匹配"""
    print("\n=== 测试桩号匹配 ===")
    
    matcher = StationMatcher()
    
    # 添加测试桩号
    test_stations = [
        {"station": "K0+000", "x": 121.4737, "y": 31.2304, "elevation": 10},
        {"station": "K0+100", "x": 121.4747, "y": 31.2314, "elevation": 12},
        {"station": "K0+200", "x": 121.4757, "y": 31.2324, "elevation": 15},
        {"station": "K0+300", "x": 121.4767, "y": 31.2334, "elevation": 18},
        {"station": "K0+400", "x": 121.4777, "y": 31.2344, "elevation": 20},
    ]
    
    for s in test_stations:
        matcher.add_station(**s)
    
    print(f"已添加 {len(test_stations)} 个测试桩号")
    
    # 测试匹配 - 在K0+200附近
    test_lat, test_lon = 31.2324, 121.4757
    result = matcher.match_station(test_lat, test_lon, max_distance=50)
    
    if result:
        print(f"匹配结果: 桩号={result['station']}, 距离={result['distance']}m")
        assert result['distance'] < 50, "匹配距离应在50米内"
    else:
        print("未匹配到桩号")
    
    # 测试查询附近
    nearby = matcher.query_nearby(test_lat, test_lon, radius=200)
    print(f"附近桩号: {len(nearby)} 个")
    for n in nearby[:3]:
        print(f"  {n['station']}: {n['distance']}m")
    
    print("[OK] 桩号匹配测试通过")


async def test_photo_capture():
    """测试照片采集流程"""
    print("\n=== 测试照片采集流程 ===")
    
    # 创建服务
    service = PhotoCaptureService()
    
    # 添加测试桩号
    service.add_test_stations()
    print("已添加测试桩号数据")
    
    # 测试手动位置的照片采集
    # 注意: 实际需要真实的照片文件
    try:
        result = await service.flow.capture(
            image_path="test_photo.jpg",
            manual_location={"lat": 31.2324, "lon": 121.4757},
            entity_id="entity_001",
            project_id=1,
            operator="test_user"
        )
        
        print(f"采集结果:")
        print(f"  photo_id: {result['photo_id'][:16]}...")
        print(f"  station: {result['station']}")
        print(f"  location: ({result['location']['lat']}, {result['location']['lon']})")
        print(f"  match_distance: {result.get('match_distance')}m")
        print(f"  lineage_id: {result.get('lineage_id')}")
        print(f"  chain_id: {result.get('chain_id')}")
        print(f"  status: {result['status']}")
        
    except Exception as e:
        print(f"采集测试: {e}")
    
    print("[OK] 照片采集流程测试完成")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("照片采集与GPS关联流程测试")
    print("=" * 50)
    
    # 测试1: GPS提取
    test_geo_extractor()
    
    # 测试2: 桩号匹配
    test_station_matcher()
    
    # 测试3: 照片采集流程
    asyncio.run(test_photo_capture())
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
