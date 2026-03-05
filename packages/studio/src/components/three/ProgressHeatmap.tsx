/**
 * ProgressHeatmap - 施工进度热力图组件
 * 显示施工区域的进度热力分布
 */

import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { HeatmapCell, ConstructionZone } from '../../types/schedule';

interface ProgressHeatmapProps {
  cells: HeatmapCell[];
  zone?: ConstructionZone;
  minIntensity?: number;
  maxIntensity?: number;
  opacity?: number;
  cellSize?: number;
  showLegend?: boolean;
  animated?: boolean;
  colorScheme?: 'default' | 'viridis' | 'inferno' | 'plasma';
}

// 颜色映射函数
function getHeatmapColor(value: number, scheme: string = 'default'): THREE.Color {
  const color = new THREE.Color();
  
  switch (scheme) {
    case 'viridis':
      // 紫-青-绿-黄
      color.setHSL(0.75 - value * 0.75, 0.8, 0.5);
      break;
    case 'inferno':
      // 黑-紫-橙-黄
      if (value < 0.25) {
        color.setRGB(value * 4, 0, 0.25 - value);
      } else if (value < 0.5) {
        color.setRGB(1, (value - 0.25) * 4, 0);
      } else if (value < 0.75) {
        color.setRGB(1, 1, (value - 0.5) * 4);
      } else {
        color.setRGB(1, 1, 0.5 + (value - 0.75) * 2);
      }
      break;
    case 'plasma':
      // 蓝-紫-橙-黄
      if (value < 0.33) {
        color.setRGB(0.05, value * 3, 0.5 + value);
      } else if (value < 0.66) {
        color.setRGB((value - 0.33) * 3, 0.5 - (value - 0.33), 1);
      } else {
        color.setRGB(1, (value - 0.66) * 3, 1 - (value - 0.66) * 1.5);
      }
      break;
    default:
      // 默认：蓝-青-绿-黄-红
      if (value < 0.25) {
        color.setRGB(0, value * 4, 1);
      } else if (value < 0.5) {
        color.setRGB(0, 1, 1 - (value - 0.25) * 4);
      } else if (value < 0.75) {
        color.setRGB((value - 0.5) * 4, 1, 0);
      } else {
        color.setRGB(1, 1 - (value - 0.75) * 4, 0);
      }
  }
  
  return color;
}

// 热力图单元格组件
function HeatmapCellMesh({
  cell,
  cellSize,
  opacity,
  animated,
  colorScheme,
}: {
  cell: HeatmapCell;
  cellSize: number;
  opacity: number;
  animated: boolean;
  colorScheme: string;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  
  const normalizedIntensity = cell.intensity;
  const color = getHeatmapColor(normalizedIntensity, colorScheme);

  useFrame(() => {
    if (animated && materialRef.current) {
      // 动态效果：强度脉冲
      const pulse = Math.sin(Date.now() * 0.003 + cell.x + cell.z) * 0.1;
      materialRef.current.emissiveIntensity = normalizedIntensity * 0.5 + pulse;
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={[cell.x, cell.y + 0.05, cell.z]}
    >
      <boxGeometry args={[cellSize * 0.9, 0.1, cellSize * 0.9]} />
      <meshStandardMaterial
        ref={materialRef}
        color={color}
        transparent
        opacity={opacity * normalizedIntensity}
        emissive={color}
        emissiveIntensity={normalizedIntensity * 0.3}
        metalness={0.1}
        roughness={0.8}
      />
    </mesh>
  );
}

// 区域进度显示
function ZoneProgressOverlay({
  zone,
}: {
  zone?: ConstructionZone;
}) {
  if (!zone) return null;

  return (
    <group>
      {/* 区域边框 */}
      <lineSegments position={[zone.position.x, 0.02, zone.position.z]}>
        <edgesGeometry args={[new THREE.BoxGeometry(
          zone.dimensions.width,
          zone.dimensions.height || 0.1,
          zone.dimensions.length
        )]} />
        <lineBasicMaterial color="#FFFFFF" transparent opacity={0.5} />
      </lineSegments>
      
      {/* 进度覆盖层 */}
      <mesh
        position={[
          zone.position.x,
          0.03,
          zone.position.z
        ]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <planeGeometry args={[zone.dimensions.width, zone.dimensions.length]} />
        <meshBasicMaterial
          color="#00FF00"
          transparent
          opacity={zone.progress / 200}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}

// 图例组件
function HeatmapLegend({
  minIntensity,
  maxIntensity,
  colorScheme,
}: {
  minIntensity: number;
  maxIntensity: number;
  colorScheme: string;
}) {
  const gradientStops = useMemo(() => {
    const stops = [];
    for (let i = 0; i <= 10; i++) {
      const value = i / 10;
      const color = getHeatmapColor(value, colorScheme);
      stops.push({ value, color: `#${color.getHexString()}` });
    }
    return stops;
  }, [colorScheme]);

  return (
    <div
      style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        borderRadius: '8px',
        padding: '16px',
        color: 'white',
        fontSize: '12px',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>施工进度</div>
      <div
        style={{
          width: '150px',
          height: '16px',
          background: `linear-gradient(to right, ${gradientStops.map(s => s.color).join(', ')})`,
          borderRadius: '4px',
          marginBottom: '4px',
        }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>{minIntensity}%</span>
        <span>{maxIntensity}%</span>
      </div>
    </div>
  );
}

// 主组件
export function ProgressHeatmap({
  cells,
  zone,
  minIntensity = 0,
  maxIntensity = 100,
  opacity = 0.8,
  cellSize = 1,
  showLegend = true,
  animated = false,
  colorScheme = 'default',
}: ProgressHeatmapProps) {
  const groupRef = useRef<THREE.Group>(null);

  // 计算单元格的归一化强度
  const normalizedCells = useMemo(() => {
    const range = maxIntensity - minIntensity;
    return cells.map(cell => ({
      ...cell,
      intensity: range > 0 ? (cell.intensity - minIntensity) / range : 0,
    }));
  }, [cells, minIntensity, maxIntensity]);

  // 过滤有效单元格
  const validCells = useMemo(() => {
    return normalizedCells.filter(cell => cell.intensity > 0);
  }, [normalizedCells]);

  return (
    <group ref={groupRef}>
      {/* 热力图单元格 */}
      {validCells.map((cell, idx) => (
        <HeatmapCellMesh
          key={`${cell.x}-${cell.z}-${idx}`}
          cell={cell}
          cellSize={cellSize}
          opacity={opacity}
          animated={animated}
          colorScheme={colorScheme}
        />
      ))}

      {/* 区域进度覆盖 */}
      <ZoneProgressOverlay zone={zone} />

      {/* 图例 */}
      {showLegend && (
        <HeatmapLegend
          minIntensity={minIntensity}
          maxIntensity={maxIntensity}
          colorScheme={colorScheme}
        />
      )}
    </group>
  );
}

// 批量热力图组件（支持多个区域）
interface MultiZoneHeatmapProps {
  zones: ConstructionZone[];
  heatmapData: Map<string, HeatmapCell[]>;
  cellSize?: number;
  showLegend?: boolean;
  animated?: boolean;
  colorScheme?: 'default' | 'viridis' | 'inferno' | 'plasma';
}

export function MultiZoneHeatmap({
  zones,
  heatmapData,
  cellSize = 1,
  showLegend = true,
  animated = false,
  colorScheme = 'default',
}: MultiZoneHeatmapProps) {
  return (
    <group>
      {zones.map(zone => {
        const cells = heatmapData.get(zone.id) || [];
        return (
          <ProgressHeatmap
            key={zone.id}
            cells={cells}
            zone={zone}
            cellSize={cellSize}
            showLegend={false}
            animated={animated}
            colorScheme={colorScheme}
          />
        );
      })}
      
      {showLegend && (
        <HeatmapLegend
          minIntensity={0}
          maxIntensity={100}
          colorScheme={colorScheme}
        />
      )}
    </group>
  );
}

// 进度统计面板
interface ProgressStatsPanelProps {
  zones: ConstructionZone[];
}

export function ProgressStatsPanel({ zones }: ProgressStatsPanelProps) {
  const totalProgress = useMemo(() => {
    if (zones.length === 0) return 0;
    const sum = zones.reduce((acc, zone) => acc + zone.progress, 0);
    return Math.round(sum / zones.length);
  }, [zones]);

  const completedZones = useMemo(() => {
    return zones.filter(z => z.progress >= 100).length;
  }, [zones]);

  const inProgressZones = useMemo(() => {
    return zones.filter(z => z.progress > 0 && z.progress < 100).length;
  }, [zones]);

  const notStartedZones = useMemo(() => {
    return zones.filter(z => z.progress === 0).length;
  }, [zones]);

  return (
    <div
      style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        borderRadius: '8px',
        padding: '16px',
        color: 'white',
        fontSize: '12px',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        minWidth: '180px',
      }}
    >
      <div style={{ marginBottom: '12px', fontWeight: 'bold', fontSize: '14px' }}>
        施工进度统计
      </div>
      
      {/* 总体进度 */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span>总体进度</span>
          <span style={{ fontWeight: 'bold', color: '#00FF00' }}>{totalProgress}%</span>
        </div>
        <div
          style={{
            width: '100%',
            height: '8px',
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '4px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${totalProgress}%`,
              height: '100%',
              background: 'linear-gradient(to right, #00FF00, #FFFF00, #FF0000)',
              borderRadius: '4px',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* 区域统计 */}
      <div style={{ display: 'grid', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00FF00' }} />
            已完成
          </span>
          <span>{completedZones} 个区域</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#FFFF00' }} />
            进行中
          </span>
          <span>{inProgressZones} 个区域</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#808080' }} />
            未开始
          </span>
          <span>{notStartedZones} 个区域</span>
        </div>
      </div>
    </div>
  );
}

export default ProgressHeatmap;
