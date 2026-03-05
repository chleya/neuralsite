# -*- coding: utf-8 -*-
"""
AI质量检测 - 缺陷检测器
使用OpenCV进行裂缝、破损、钢筋外露等缺陷检测
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import sys
sys.path.insert(0, '.')

from .models import DetectionResult, DefectType, BoundingBox


class DefectDetector:
    """缺陷检测器"""
    
    def __init__(self, min_contour_area: int = 50):
        """
        初始化检测器
        
        Args:
            min_contour_area: 最小轮廓面积阈值
        """
        self.min_contour_area = min_contour_area
    
    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        """
        检测图像中的缺陷
        
        Args:
            image: BGR格式的图像
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 裂缝检测
        crack_results = self._detect_crack(gray, image)
        results.extend(crack_results)
        
        # 破损/剥落检测
        spalling_results = self._detect_spalling(gray, image)
        results.extend(spalling_results)
        
        # 钢筋外露检测
        rebar_results = self._detect_rebar_exposed(gray, image)
        results.extend(rebar_results)
        
        # 不平整检测
        unevenness_results = self._detect_unevenness(gray)
        results.extend(unevenness_results)
        
        return results
    
    def _detect_crack(self, gray: np.ndarray, image: np.ndarray) -> List[DetectionResult]:
        """检测裂缝"""
        results = []
        
        # 高斯模糊降噪
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 使用Canny边缘检测
        edges = cv2.Canny(blurred, 30, 100)
        
        # 形态学操作：闭运算连接断裂的边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_contour_area:
                continue
            
            # 计算轮廓特征
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h > 0 else 0
            
            # 裂缝特征：长宽比大（线性）
            if aspect_ratio > 3 or aspect_ratio < 0.33:
                # 计算可疑度评分
                suspicion = self._calculate_crack_suspicion(contour, area, aspect_ratio)
                
                # 严重程度
                severity = "critical" if suspicion > 80 else "warning" if suspicion > 50 else "normal"
                
                results.append(DetectionResult(
                    defect_type=DefectType.CRACK,
                    confidence=min(aspect_ratio / 10, 0.95),
                    suspicion_score=suspicion,
                    bounding_box=BoundingBox(x, y, w, h),
                    description=f"检测到线性裂缝，可疑度: {suspicion}",
                    severity=severity,
                    metadata={"area": area, "aspect_ratio": aspect_ratio}
                ))
        
        return results
    
    def _detect_spalling(self, gray: np.ndarray, image: np.ndarray) -> List[DetectionResult]:
        """检测破损/剥落"""
        results = []
        
        # 使用自适应阈值
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 形态学操作去除噪声
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_contour_area * 2:  # 破损通常面积较大
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # 计算轮廓的实心度
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            
            # 破损特征：实心度较低（凹凸不平）
            if solidity < 0.8:
                suspicion = int(solidity * 100)
                
                severity = "critical" if area > 5000 else "warning" if area > 1000 else "normal"
                
                results.append(DetectionResult(
                    defect_type=DefectType.SPALLING,
                    confidence=1 - solidity,
                    suspicion_score=suspicion,
                    bounding_box=BoundingBox(x, y, w, h),
                    description=f"检测到破损/剥落区域，面积: {area}px²",
                    severity=severity,
                    metadata={"area": area, "solidity": round(solidity, 3)}
                ))
        
        return results
    
    def _detect_rebar_exposed(self, gray: np.ndarray, image: np.ndarray) -> List[DetectionResult]:
        """检测钢筋外露"""
        results = []
        
        # 转换为HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 锈蚀/钢筋颜色范围 (橙红色)
        lower_brown = np.array([0, 100, 50])
        upper_brown = np.array([20, 255, 200])
        
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_contour_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # 钢筋外露特征：通常是长条形或簇状
            aspect_ratio = float(max(w, h)) / min(w, h) if min(w, h) > 0 else 0
            
            if aspect_ratio > 1.5:  # 长条形
                suspicion = min(int(area / 50), 100)
                
                severity = "critical" if suspicion > 70 else "warning" if suspicion > 40 else "normal"
                
                results.append(DetectionResult(
                    defect_type=DefectType.REBAR_EXPOSED,
                    confidence=min(aspect_ratio / 5, 0.95),
                    suspicion_score=suspicion,
                    bounding_box=BoundingBox(x, y, w, h),
                    description=f"检测到钢筋外露/锈蚀",
                    severity=severity,
                    metadata={"area": area, "aspect_ratio": aspect_ratio}
                ))
        
        return results
    
    def _detect_unevenness(self, gray: np.ndarray) -> List[DetectionResult]:
        """检测不平整"""
        results = []
        
        # 计算梯度
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(sobelx**2 + sobely**2)
        
        # 统计高梯度区域
        high_gradient_ratio = np.sum(gradient > 50) / gradient.size
        
        # 如果高梯度区域比例异常，判定为不平整
        if high_gradient_ratio > 0.15:
            suspicion = int(min(high_gradient_ratio * 200, 100))
            
            severity = "critical" if suspicion > 80 else "warning" if suspicion > 50 else "normal"
            
            results.append(DetectionResult(
                defect_type=DefectType.UNEVENNESS,
                confidence=high_gradient_ratio,
                suspicion_score=suspicion,
                description=f"检测到表面不平整",
                severity=severity,
                metadata={"high_gradient_ratio": round(high_gradient_ratio, 3)}
            ))
        
        return results
    
    def _calculate_crack_suspicion(self, contour, area: float, aspect_ratio: float) -> int:
        """计算裂缝可疑度评分"""
        # 基于面积和长宽比计算可疑度
        # 裂缝越长、可疑度越高
        length_score = min(area / 100, 50)
        
        # 长宽比越极端（越细长），越可能是裂缝
        ratio_score = min(abs(aspect_ratio - 1) / 5 * 50, 50)
        
        return int(length_score + ratio_score)
    
    def batch_detect(self, images: list) -> list:
        """
        批量检测
        
        Args:
            images: 图像列表
            
        Returns:
            list: 检测结果列表
        """
        return [self.detect(img) for img in images]
    
    def detect_from_file(self, image_path: str) -> List[DetectionResult]:
        """
        从文件路径检测
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        return self.detect(image)
    
    def detect_from_bytes(self, image_bytes: bytes) -> List[DetectionResult]:
        """
        从字节数据检测
        
        Args:
            image_bytes: 图像字节数据
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解码图像数据")
        return self.detect(image)


def create_detector(min_contour_area: int = 50) -> DefectDetector:
    """创建检测器实例"""
    return DefectDetector(min_contour_area=min_contour_area)
