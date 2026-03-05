/**
 * TrajectoryPlayer - 轨迹回放组件
 * 支持设备轨迹的时间轴控制回放
 */

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { EquipmentTrajectory, PositionPoint } from '../../types/schedule';

interface TrajectoryPlayerProps {
  trajectory: EquipmentTrajectory | null;
  isPlaying: boolean;
  playbackSpeed: number;
  progress: number;
  onProgressChange: (progress: number) => void;
  showTrail?: boolean;
  trailColor?: string;
  showMarkers?: boolean;
  equipmentColor?: string;
}

// 时间格式化
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 解析时间字符串为秒数
function parseTimeToSeconds(timeStr: string): number {
  const date = new Date(timeStr);
  return date.getTime() / 1000;
}

// 轨迹线组件
function TrajectoryLine({
  points,
  color,
  opacity = 0.6,
  lineWidth = 2,
}: {
  points: THREE.Vector3[];
  color: string;
  opacity?: number;
  lineWidth?: number;
}) {
  const lineRef = useRef<THREE.Line>(null);
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    return geo;
  }, [points]);

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineBasicMaterial
        color={color}
        transparent
        opacity={opacity}
        linewidth={lineWidth}
      />
    </line>
  );
}

// 轨迹点标记
function TrajectoryMarker({
  position,
  index,
  isActive,
  label,
}: {
  position: THREE.Vector3;
  index: number;
  isActive: boolean;
  label?: string;
}) {
  return (
    <group position={[position.x, position.y + 0.5, position.z]}>
      <mesh>
        <sphereGeometry args={[isActive ? 0.3 : 0.15, 16, 16]} />
        <meshBasicMaterial
          color={isActive ? '#00FF00' : '#FFFFFF'}
          transparent
          opacity={isActive ? 1 : 0.5}
        />
      </mesh>
      {isActive && (
        <mesh>
          <ringGeometry args={[0.3, 0.5, 16]} />
          <meshBasicMaterial
            color="#00FF00"
            transparent
            opacity={0.5}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  );
}

// 当前设备位置指示器
function CurrentPositionIndicator({
  position,
  heading,
  color,
}: {
  position: THREE.Vector3;
  heading?: number;
  color: string;
}) {
  const groupRef = useRef<THREE.Group>(null);

  return (
    <group
      ref={groupRef}
      position={[position.x, position.y + 0.3, position.z]}
      rotation={[0, heading || 0, 0]}
    >
      {/* 方向箭头 */}
      <mesh position={[0, 0, 0.5]}>
        <coneGeometry args={[0.2, 0.5, 8]} />
        <meshBasicMaterial color={color} />
      </mesh>
      
      {/* 位置光晕 */}
      <pointLight color={color} intensity={1} distance={5} />
    </group>
  );
}

// 主组件
export function TrajectoryPlayer({
  trajectory,
  isPlaying,
  playbackSpeed,
  progress,
  onProgressChange,
  showTrail = true,
  trailColor = '#00AAFF',
  showMarkers = false,
  equipmentColor = '#FFA500',
}: TrajectoryPlayerProps) {
  const currentPositionRef = useRef<THREE.Vector3>(new THREE.Vector3());
  const animationRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  // 计算轨迹总时长
  const duration = useMemo(() => {
    if (!trajectory || trajectory.points.length < 2) return 0;
    const start = parseTimeToSeconds(trajectory.points[0].timestamp);
    const end = parseTimeToSeconds(trajectory.points[trajectory.points.length - 1].timestamp);
    return end - start;
  }, [trajectory]);

  // 将进度转换为轨迹点索引
  const currentPointIndex = useMemo(() => {
    if (!trajectory || trajectory.points.length === 0) return 0;
    return Math.floor(progress * (trajectory.points.length - 1));
  }, [trajectory, progress]);

  // 生成轨迹线点
  const trailPoints = useMemo(() => {
    if (!trajectory) return [];
    return trajectory.points.map(
      (p) => new THREE.Vector3(p.position.x, p.position.y + 0.1, p.position.z)
    );
  }, [trajectory]);

  // 已完成轨迹（绿色）
  const completedTrailPoints = useMemo(() => {
    if (!trajectory || currentPointIndex <= 0) return [];
    return trailPoints.slice(0, currentPointIndex + 1);
  }, [trajectory, currentPointIndex, trailPoints]);

  // 剩余轨迹（灰色）
  const remainingTrailPoints = useMemo(() => {
    if (!trajectory || currentPointIndex >= trailPoints.length - 1) return [];
    return trailPoints.slice(currentPointIndex);
  }, [trajectory, currentPointIndex, trailPoints]);

  // 获取当前位置
  const currentPosition = useMemo(() => {
    if (!trajectory || trajectory.points.length === 0) {
      return new THREE.Vector3(0, 0, 0);
    }
    const point = trajectory.points[Math.min(currentPointIndex, trajectory.points.length - 1)];
    return new THREE.Vector3(point.position.x, point.position.y, point.position.z);
  }, [trajectory, currentPointIndex]);

  // 获取当前heading
  const currentHeading = useMemo(() => {
    if (!trajectory || trajectory.points.length < 2) return 0;
    const idx = Math.min(currentPointIndex, trajectory.points.length - 1);
    const point = trajectory.points[idx];
    return point.rotation?.y || 0;
  }, [trajectory, currentPointIndex]);

  // 动画帧更新
  useFrame((state) => {
    if (!isPlaying || !trajectory) return;

    const currentTime = state.clock.elapsedTime;
    const deltaTime = currentTime - lastTimeRef.current;
    lastTimeRef.current = currentTime;

    // 根据播放速度和进度更新位置
    const progressDelta = (deltaTime * playbackSpeed) / duration;
    const newProgress = Math.min(progress + progressDelta, 1);

    if (newProgress >= 1) {
      onProgressChange(0); // 循环播放
    } else {
      onProgressChange(newProgress);
    }
  });

  // 没有轨迹数据时返回null
  if (!trajectory || trajectory.points.length === 0) {
    return null;
  }

  const currentPoint = trajectory.points[currentPointIndex];
  const currentTime = currentPoint ? parseTimeToSeconds(currentPoint.timestamp) : 0;

  return (
    <group>
      {/* 已完成轨迹（绿色） */}
      {showTrail && completedTrailPoints.length > 1 && (
        <TrajectoryLine
          points={completedTrailPoints}
          color="#00FF00"
          opacity={0.8}
          lineWidth={3}
        />
      )}

      {/* 剩余轨迹（灰色） */}
      {showTrail && remainingTrailPoints.length > 1 && (
        <TrajectoryLine
          points={remainingTrailPoints}
          color="#888888"
          opacity={0.3}
          lineWidth={1}
        />
      )}

      {/* 轨迹标记点 */}
      {showMarkers && trajectory.points.map((point, idx) => (
        <TrajectoryMarker
          key={idx}
          position={new THREE.Vector3(point.position.x, point.position.y, point.position.z)}
          index={idx}
          isActive={idx === currentPointIndex}
        />
      ))}

      {/* 当前设备位置 */}
      <CurrentPositionIndicator
        position={currentPosition}
        heading={currentHeading}
        color={equipmentColor}
      />

      {/* 起点标记 */}
      {trailPoints.length > 0 && (
        <mesh position={trailPoints[0]}>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshBasicMaterial color="#00FF00" />
        </mesh>
      )}

      {/* 终点标记 */}
      {trailPoints.length > 1 && (
        <mesh position={trailPoints[trailPoints.length - 1]}>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshBasicMaterial color="#FF0000" />
        </mesh>
      )}
    </group>
  );
}

// 轨迹回放控制UI组件
interface TrajectoryControlUIProps {
  isPlaying: boolean;
  playbackSpeed: number;
  progress: number;
  duration: number;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onProgressChange: (progress: number) => void;
  onRestart: () => void;
}

export function TrajectoryControlUI({
  isPlaying,
  playbackSpeed,
  progress,
  duration,
  onPlayPause,
  onSpeedChange,
  onProgressChange,
  onRestart,
}: TrajectoryControlUIProps) {
  const formatDuration = (seconds: number) => formatTime(seconds);
  const currentTime = progress * duration;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0, 0, 0, 0.8)',
        borderRadius: '8px',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        color: 'white',
        fontSize: '14px',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* 播放/暂停按钮 */}
      <button
        onClick={onPlayPause}
        style={{
          background: '#3B82F6',
          border: 'none',
          borderRadius: '50%',
          width: '36px',
          height: '36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: 'white',
          fontSize: '16px',
        }}
      >
        {isPlaying ? '⏸' : '▶'}
      </button>

      {/* 重新开始按钮 */}
      <button
        onClick={onRestart}
        style={{
          background: 'transparent',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '4px',
          padding: '6px 12px',
          cursor: 'pointer',
          color: 'white',
          fontSize: '12px',
        }}
      >
        ⟲ 重置
      </button>

      {/* 时间显示 */}
      <div style={{ minWidth: '100px', textAlign: 'center' }}>
        {formatDuration(currentTime)} / {formatDuration(duration)}
      </div>

      {/* 进度条 */}
      <input
        type="range"
        min="0"
        max="1"
        step="0.001"
        value={progress}
        onChange={(e) => onProgressChange(parseFloat(e.target.value))}
        style={{
          width: '200px',
          cursor: 'pointer',
        }}
      />

      {/* 速度控制 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '12px', opacity: 0.7 }}>速度:</span>
        {[1, 2, 5, 10].map((speed) => (
          <button
            key={speed}
            onClick={() => onSpeedChange(speed)}
            style={{
              background: playbackSpeed === speed ? '#3B82F6' : 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '4px',
              padding: '4px 8px',
              cursor: 'pointer',
              color: 'white',
              fontSize: '12px',
              minWidth: '36px',
            }}
          >
            {speed}x
          </button>
        ))}
      </div>
    </div>
  );
}

export default TrajectoryPlayer;
