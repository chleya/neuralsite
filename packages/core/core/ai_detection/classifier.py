# -*- coding: utf-8 -*-
"""
AI质量检测 - 照片分类器
使用简单图像特征进行施工部位和施工阶段分类
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import sys
sys.path.insert(0, '.')

from .models import ClassificationResult, ConstructionPart, ConstructionPhase


class ImageClassifier:
    """图像分类器 - 基于颜色和纹理特征"""
    
    # 颜色阈值 (HSV)
    COLOR_RANGES = {
        # 灰色系 (路面)
        ConstructionPart.ROAD: {
            'lower': np.array([0, 0, 50]),
            'upper': np.array([180, 50, 200])
        },
        # 混凝土色 (桥梁/隧道)
        ConstructionPart.BRIDGE: {
            'lower': np.array([0, 0, 100]),
            'upper': np.array([180, 30, 220])
        },
        ConstructionPart.TUNNEL: {
            'lower': np.array([0, 0, 80]),
            'upper': np.array([180, 40, 200])
        },
        # 绿色系 (边坡)
        ConstructionPart.SLOPE: {
            'lower': np.array([25, 30, 30]),
            'upper': np.array([85, 255, 200])
        },
    }
    
    def __init__(self):
        self.parts = list(ConstructionPart)
        self.phases = list(ConstructionPhase)
    
    def classify(self, image: np.ndarray) -> ClassificationResult:
        """
        对图像进行分类
        
        Args:
            image: BGR格式的图像
            
        Returns:
            ClassificationResult: 分类结果
        """
        # 分类施工部位
        part, part_confidence = self._classify_part(image)
        
        # 分类施工阶段
        phase, phase_confidence = self._classify_phase(image)
        
        # 取两者的最小值作为总体置信度
        confidence = min(part_confidence, phase_confidence)
        
        return ClassificationResult(
            part=part,
            phase=phase,
            confidence=confidence,
            metadata={
                "part_confidence": part_confidence,
                "phase_confidence": phase_confidence
            }
        )
    
    def _classify_part(self, image: np.ndarray) -> Tuple[ConstructionPart, float]:
        """分类施工部位"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        scores = {}
        
        for part, color_range in self.COLOR_RANGES.items():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            ratio = np.sum(mask > 0) / mask.size
            scores[part] = ratio
        
        # 添加纹理分析作为补充
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        texture_score = self._analyze_texture(gray)
        
        # 路面通常有车道线纹理
        if texture_score > 0.1:
            scores[ConstructionPart.ROAD] = scores.get(ConstructionPart.ROAD, 0) + texture_score
        
        # 如果没有明显匹配，返回UNKNOWN
        if not scores or max(scores.values()) < 0.05:
            return ConstructionPart.UNKNOWN, 0.3
        
        # 返回得分最高的部位
        best_part = max(scores, key=scores.get)
        confidence = min(scores[best_part] * 5, 0.95)  # 归一化到0-0.95
        
        return best_part, max(confidence, 0.3)
    
    def _classify_phase(self, image: np.ndarray) -> Tuple[ConstructionPhase, float]:
        """分类施工阶段"""
        # 分析图像特征
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算对比度
        contrast = np.std(gray)
        
        # 计算亮度
        brightness = np.mean(gray)
        
        # 分析边缘密度（施工中通常有更多边缘/纹理）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 简单规则分类
        scores = {}
        
        # 施工前：通常较暗、对比度低（裸土/基础）
        if brightness < 100 and contrast < 50:
            scores[ConstructionPhase.BEFORE] = 0.7
        
        # 施工中：边缘多、对比度高（有结构物/施工痕迹）
        if edge_density > 0.05:
            scores[ConstructionPhase.DURING] = edge_density * 10
        
        # 施工后：较亮、对比度适中、表面较平整
        if brightness > 120 and contrast < 60 and edge_density < 0.03:
            scores[ConstructionPhase.AFTER] = 0.6
        
        if not scores:
            # 默认返回UNKNOWN
            return ConstructionPhase.UNKNOWN, 0.3
        
        best_phase = max(scores, key=scores.get)
        confidence = min(scores[best_phase], 0.85)
        
        return best_phase, max(confidence, 0.3)
    
    def _analyze_texture(self, gray: np.ndarray) -> float:
        """分析图像纹理"""
        # 使用LBP-like方法分析纹理
        # 简化版：计算局部方差
        kernel_size = 5
        mean = cv2.blur(gray.astype(float), (kernel_size, kernel_size))
        variance = cv2.blur((gray.astype(float) - mean) ** 2, (kernel_size, kernel_size))
        
        # 返回平均方差作为纹理分数
        return float(np.mean(variance) / 1000)
    
    def batch_classify(self, images: list) -> list:
        """
        批量分类
        
        Args:
            images: 图像列表
            
        Returns:
            list: ClassificationResult列表
        """
        return [self.classify(img) for img in images]
    
    def classify_from_file(self, image_path: str) -> ClassificationResult:
        """
        从文件路径分类图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            ClassificationResult: 分类结果
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        return self.classify(image)
    
    def classify_from_bytes(self, image_bytes: bytes) -> ClassificationResult:
        """
        从字节数据分类图像
        
        Args:
            image_bytes: 图像字节数据
            
        Returns:
            ClassificationResult: 分类结果
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解码图像数据")
        return self.classify(image)


def create_classifier() -> ImageClassifier:
    """创建分类器实例"""
    return ImageClassifier()
