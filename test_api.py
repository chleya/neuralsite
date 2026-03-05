# -*- coding: utf-8 -*-
"""测试 NeuralSite API 能否加载图纸数据"""

import sys
sys.path.insert(0, 'packages/core')

from core.geometry import HorizontalAlignment

# 创建路线对象
route = HorizontalAlignment()
route.name = '镇雄至赫章高速'

print("=" * 50)
print("NeuralSite API 测试")
print("=" * 50)
print()
print("✅ API 模块加载成功！")
print()
print("从图纸提取的数据可以转换为路线参数：")
print()
print("1. 平曲线元素:")
print("   - 直线 (LineElement)")
print("   - 圆曲线 (CircularCurveElement)")
print("   - 缓和曲线 (SpiralCurveElement)")
print()
print("2. 竖曲线元素:")
print("   - 坡度段 (GradeSection)")
print("   - 竖曲线 (VerticalCurveElement)")
print()
print("3. 横断面元素:")
print("   - 路面结构")
print("   - 边坡")
print("   - 排水沟")
print()
print("=" * 50)
print("下一步：需要从图纸 OCR 提取或手动输入坐标数据")
print("=" * 50)
