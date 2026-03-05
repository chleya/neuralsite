# -*- coding: utf-8 -*-
"""
AI质量检测演示脚本
"""

import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.ai_detection import (
    create_workflow, create_classifier, create_detector, create_scorer,
    ConstructionPart, ConstructionPhase, DefectType, ReviewStatus
)


def create_demo_images():
    """创建演示图像"""
    images = {}
    
    # 1. 正常路面 - 灰色均匀背景
    img1 = np.ones((480, 640, 3), dtype=np.uint8) * 150
    # 添加一些噪点模拟真实路面
    noise = np.random.randint(-15, 15, img1.shape, dtype=np.int16)
    img1 = np.clip(img1.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # 添加一些线条模拟车道
    cv2.line(img1, (320, 0), (320, 480), (200, 200, 200), 3)
    images["normal"] = img1
    
    # 2. 有裂缝的路面 - 更明显
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 140
    noise = np.random.randint(-10, 10, img2.shape, dtype=np.int16)
    img2 = np.clip(img2.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # 绘制更长的裂缝线
    cv2.line(img2, (50, 20), (600, 450), (40, 40, 40), 4)
    cv2.line(img2, (80, 30), (550, 420), (50, 50, 50), 2)
    images["crack"] = img2
    
    # 3. 有破损的区域 - 明显不同
    img3 = np.ones((480, 640, 3), dtype=np.uint8) * 130
    noise = np.random.randint(-10, 10, img3.shape, dtype=np.int16)
    img3 = np.clip(img3.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # 绘制不规则区域
    pts = np.array([[200, 100], [400, 100], [450, 300], [300, 380], [150, 250]], np.int32)
    cv2.fillPoly(img3, [pts], (80, 80, 80))
    # 添加一些细节
    cv2.circle(img3, (250, 180), 20, (60, 60, 60), -1)
    cv2.circle(img3, (350, 220), 30, (90, 90, 90), -1)
    images["spalling"] = img3
    
    # 4. 有钢筋外露/锈蚀
    img4 = np.ones((480, 640, 3), dtype=np.uint8) * 120
    noise = np.random.randint(-10, 10, img4.shape, dtype=np.int16)
    img4 = np.clip(img4.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # 绘制锈迹区域 - 橙红色
    cv2.rectangle(img4, (180, 80), (420, 320), (60, 40, 20), -1)
    # 绘制长条形钢筋
    cv2.rectangle(img4, (200, 120), (400, 140), (70, 50, 30), -1)
    cv2.rectangle(img4, (220, 180), (380, 200), (65, 45, 25), -1)
    cv2.rectangle(img4, (190, 240), (410, 260), (70, 50, 30), -1)
    # 边缘高亮
    cv2.rectangle(img4, (180, 80), (420, 320), (90, 60, 40), 3)
    images["rebar"] = img4
    
    # 5. 不平整路面
    img5 = np.ones((480, 640, 3), dtype=np.uint8) * 135
    # 创建不均匀的梯度
    for i in range(0, 480, 20):
        val = 120 + (i * 0.3) % 50
        cv2.line(img5, (0, i), (640, i), (val, val, val), 20)
    # 添加一些凸起
    for _ in range(10):
        x, y = np.random.randint(50, 590), np.random.randint(50, 430)
        r = np.random.randint(20, 50)
        brightness = np.random.randint(100, 160)
        cv2.circle(img5, (x, y), r, (brightness, brightness, brightness), -1)
    images["uneven"] = img5
    
    return images


def main():
    """主函数"""
    print("=" * 60)
    print("NeuralSite AI 质量检测模块演示")
    print("=" * 60)
    
    # 创建工作流
    workflow = create_workflow()
    
    # 创建演示图像
    print("\n[1] 生成演示图像...")
    images = create_demo_images()
    
    # 保存图像
    os.makedirs("output/ai_detection", exist_ok=True)
    for name, img in images.items():
        cv2.imwrite(f"output/ai_detection/{name}.jpg", img)
    print(f"    已保存 {len(images)} 张演示图像到 output/ai_detection/")
    
    # 处理每张图像
    print("\n[2] AI 检测分析...")
    print("-" * 60)
    
    task_results = []
    for name, img in images.items():
        # 临时保存
        temp_path = f"output/ai_detection/{name}.jpg"
        
        task = workflow.process_image(
            image_path=temp_path,
            project_id=1,
            location=f"演示路段-{name}"
        )
        
        print(f"\n图像: {name}.jpg")
        print(f"  分类: {task.classification.part.value} / {task.classification.phase.value}")
        print(f"  置信度: {task.classification.confidence:.2%}")
        print(f"  检测到缺陷数: {len(task.detections)}")
        
        for d in task.detections:
            print(f"    - {d.defect_type.value}: 可疑度={d.suspicion_score}, 严重程度={d.severity}")
            if d.bounding_box:
                print(f"      位置: ({d.bounding_box.x}, {d.bounding_box.y}) "
                      f"尺寸: {d.bounding_box.width}x{d.bounding_box.height}")
        
        print(f"  状态: {task.status.value}")
        
        task_results.append((name, task))
    
    # 统计
    print("\n" + "=" * 60)
    print("[3] 统计信息")
    print("-" * 60)
    
    stats = workflow.get_statistics()
    print(f"  总任务数: {stats['total']}")
    print(f"  有缺陷: {stats['with_defects']}")
    print(f"  待审核: {stats['pending']}")
    print(f"  已通过: {stats['approved']}")
    print(f"  平均评分: {stats['avg_score']}")
    
    # 模拟审核
    print("\n" + "=" * 60)
    print("[4] 模拟审核流程")
    print("-" * 60)
    
    for name, task in task_results:
        if task.has_defects:
            approved = task.max_suspicion_score < 50
            comment = "AI判定为轻微缺陷，建议通过" if approved else "需要人工复核"
            
            workflow.review_task(
                task.task_id,
                reviewer_id="质检员A",
                approved=approved,
                comment=comment
            )
            print(f"  {name}.jpg: 已审核 -> {'通过' if approved else '需复查'}")
        else:
            print(f"  {name}.jpg: 无缺陷 -> 自动通过")
    
    # 最终统计
    print("\n" + "=" * 60)
    print("[5] 审核后统计")
    print("-" * 60)
    
    stats = workflow.get_statistics()
    print(f"  待审核: {stats['pending']}")
    print(f"  已通过: {stats['approved']}")
    print(f"  已驳回: {stats['rejected']}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    
    return workflow, task_results


if __name__ == "__main__":
    main()
