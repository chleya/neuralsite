/**
 * Scheduler3D - 施工调度3D可视化主组件
 * 集成设备模型、轨迹回放、热力图的综合3D调度视图
 */

import React, { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { 
  OrbitControls, 
  Grid, 
  Environment, 
  ContactShadows,
  Html,
  useProgress,
  PerspectiveCamera,
} from '@react-three/drei';
import * as THREE from 'three';

import EquipmentModel, { EquipmentShadow } from './EquipmentModel';
import TrajectoryPlayer, { TrajectoryControlUI } from './TrajectoryPlayer';
import ProgressHeatmap, { ProgressStatsPanel } from './ProgressHeatmap';

import type { 
  Equipment, 
  ConstructionZone, 
  EquipmentTrajectory,
  TimelineState,
  HeatmapCell,
} from '../../types/schedule';

// 加载进度组件
function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div style={{ 
        color: 'white', 
        background: 'rgba(0,0,0,0.8)', 
        padding: '20px', 
        borderRadius: '8px',
        fontSize: '14px',
      }}>
        加载中... {progress.toFixed(0)}%
      </div>
    </Html>
  );
}

// 地面网格组件
function GroundGrid({ size = 100, divisions = 50 }) {
  return (
    <group>
      <Grid
        args={[size, divisions]}
        position={[0, 0, 0]}
        cellSize={size / divisions}
        cellThickness={0.5}
        cellColor="#404040"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#606060"
        fadeDistance={80}
        fadeStrength={1}
        followCamera={false}
      />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <planeGeometry args={[size, size]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
    </group>
  );
}

// 区域边界组件
function ZoneBoundary({ 
  zone,
  selected,
}: { 
  zone: ConstructionZone;
  selected?: boolean;
}) {
  const position: [number, number, number] = [
    zone.position.x,
    zone.position.y,
    zone.position.z,
  ];
  
  const dimensions: [number, number, number] = [
    zone.dimensions.width,
    zone.dimensions.height || 1,
    zone.dimensions.length,
  ];

  // 根据进度计算颜色
  const color = useMemo(() => {
    if (zone.progress >= 100) return '#00FF00';
    if (zone.progress >= 50) return '#FFFF00';
    return '#FFA500';
  }, [zone.progress]);

  return (
    <group position={position}>
      {/* 区域边框 */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(...dimensions)]} />
        <lineBasicMaterial 
          color={selected ? '#3B82F6' : color} 
          transparent 
          opacity={selected ? 1 : 0.6} 
          linewidth={2}
        />
      </lineSegments>
      
      {/* 进度覆盖层 */}
      <mesh 
        rotation={[-Math.PI / 2, 0, 0]} 
        position={[0, 0.02, 0]}
      >
        <planeGeometry args={[zone.dimensions.width * 0.98, zone.dimensions.length * 0.98]} />
        <meshBasicMaterial 
          color={color} 
          transparent 
          opacity={zone.progress / 300}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* 区域标签 */}
      <Html
        position={[0, zone.dimensions.height / 2 + 1, 0]}
        center
        distanceFactor={30}
      >
        <div style={{
          background: selected ? 'rgba(59, 130, 246, 0.9)' : 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          whiteSpace: 'nowrap',
          border: selected ? '2px solid #3B82F6' : '1px solid rgba(255,255,255,0.2)',
        }}>
          <div style={{ fontWeight: 'bold' }}>{zone.name}</div>
          <div style={{ color }}>进度: {zone.progress}%</div>
        </div>
      </Html>
    </group>
  );
}

// 场景内容组件
function SceneContent({
  equipment,
  zones,
  selectedEquipmentId,
  selectedZoneId,
  timelineState,
  heatmapCells,
  showHeatmap,
  onEquipmentClick,
  onZoneClick,
}: {
  equipment: Equipment[];
  zones: ConstructionZone[];
  selectedEquipmentId?: string;
  selectedZoneId?: string;
  timelineState: TimelineState;
  heatmapCells: HeatmapCell[];
  showHeatmap: boolean;
  onEquipmentClick: (eq: Equipment) => void;
  onZoneClick: (zone: ConstructionZone) => void;
}) {
  // 获取选中设备的轨迹
  const selectedEquipment = useMemo(() => {
    return equipment.find(eq => eq.id === selectedEquipmentId);
  }, [equipment, selectedEquipmentId]);

  const trajectory = selectedEquipment?.trajectory || null;

  return (
    <>
      {/* 环境设置 */}
      <Environment preset="daylight" />
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[20, 30, 10]}
        intensity={1}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-far={100}
        shadow-camera-left={-50}
        shadow-camera-right={50}
        shadow-camera-top={50}
        shadow-camera-bottom={-50}
      />
      
      {/* 地面 */}
      <GroundGrid size={200} divisions={40} />
      
      {/* 区域边界 */}
      {zones.map(zone => (
        <group 
          key={zone.id} 
          onClick={(e) => {
            e.stopPropagation();
            onZoneClick(zone);
          }}
        >
          <ZoneBoundary 
            zone={zone} 
            selected={zone.id === selectedZoneId} 
          />
        </group>
      ))}
      
      {/* 热力图 */}
      {showHeatmap && heatmapCells.length > 0 && (
        <ProgressHeatmap
          cells={heatmapCells}
          minIntensity={0}
          maxIntensity={100}
          opacity={0.7}
          cellSize={2}
          showLegend={true}
          animated={true}
          colorScheme="inferno"
        />
      )}
      
      {/* 机械设备 */}
      {equipment.map(eq => (
        <group key={eq.id}>
          <EquipmentModel
            equipment={eq}
            isSelected={eq.id === selectedEquipmentId}
            showLabel={true}
            onClick={onEquipmentClick}
          />
          <EquipmentShadow equipment={eq} />
        </group>
      ))}
      
      {/* 轨迹回放 */}
      {selectedEquipmentId && trajectory && (
        <TrajectoryPlayer
          trajectory={trajectory}
          isPlaying={timelineState.isPlaying}
          playbackSpeed={timelineState.playbackSpeed}
          progress={timelineState.progress}
          onProgressChange={() => {}}
          showTrail={true}
          trailColor="#00AAFF"
          showMarkers={true}
          equipmentColor={selectedEquipment?.type === 'excavator' ? '#FFA500' : '#4169E1'}
        />
      )}
      
      {/* 阴影 */}
      <ContactShadows
        position={[0, 0, 0]}
        opacity={0.4}
        scale={200}
        blur={2}
        far={50}
      />
    </>
  );
}

// 主组件接口
interface Scheduler3DProps {
  equipment: Equipment[];
  zones: ConstructionZone[];
  heatmapData?: Map<string, HeatmapCell[]>;
  selectedEquipmentId?: string;
  selectedZoneId?: string;
  onEquipmentSelect?: (equipment: Equipment | null) => void;
  onZoneSelect?: (zone: ConstructionZone | null) => void;
  showHeatmap?: boolean;
  showControls?: boolean;
  initialCameraPosition?: [number, number, number];
  className?: string;
}

// 主组件
export function Scheduler3D({
  equipment,
  zones,
  heatmapData,
  selectedEquipmentId,
  selectedZoneId,
  onEquipmentSelect,
  onZoneSelect,
  showHeatmap = false,
  showControls = true,
  initialCameraPosition = [30, 30, 30],
  className,
}: Scheduler3DProps) {
  // 状态管理
  const [selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null);
  const [selectedZone, setSelectedZone] = useState<ConstructionZone | null>(null);
  const [timelineState, setTimelineState] = useState<TimelineState>({
    currentTime: new Date().toISOString(),
    isPlaying: false,
    playbackSpeed: 1,
    duration: 0,
    progress: 0,
  });

  // 计算热力图单元格
  const heatmapCells = useMemo(() => {
    if (!heatmapData) return [];
    
    const cells: HeatmapCell[] = [];
    heatmapData.forEach((zoneCells) => {
      cells.push(...zoneCells);
    });
    return cells;
  }, [heatmapData]);

  // 处理设备点击
  const handleEquipmentClick = useCallback((eq: Equipment) => {
    setSelectedEquipment(eq);
    setSelectedZone(null);
    onEquipmentSelect?.(eq);
    onZoneSelect?.(null);
    
    // 如果有轨迹，初始化时间轴
    if (eq.trajectory) {
      const startTime = new Date(eq.trajectory.startTime).getTime();
      const endTime = new Date(eq.trajectory.endTime).getTime();
      const duration = (endTime - startTime) / 1000;
      
      setTimelineState(prev => ({
        ...prev,
        duration,
        progress: 0,
      }));
    }
  }, [onEquipmentSelect, onZoneSelect]);

  // 处理区域点击
  const handleZoneClick = useCallback((zone: ConstructionZone) => {
    setSelectedZone(zone);
    setSelectedEquipment(null);
    onZoneSelect?.(zone);
    onEquipmentSelect?.(null);
  }, [onEquipmentSelect, onZoneSelect]);

  // 时间轴控制
  const handlePlayPause = useCallback(() => {
    setTimelineState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying,
    }));
  }, []);

  const handleSpeedChange = useCallback((speed: number) => {
    setTimelineState(prev => ({
      ...prev,
      playbackSpeed: speed,
    }));
  }, []);

  const handleProgressChange = useCallback((progress: number) => {
    setTimelineState(prev => ({
      ...prev,
      progress,
    }));
  }, []);

  const handleRestart = useCallback(() => {
    setTimelineState(prev => ({
      ...prev,
      progress: 0,
      isPlaying: false,
    }));
  }, []);

  // 更新选中设备
  useEffect(() => {
    if (selectedEquipmentId) {
      const eq = equipment.find(e => e.id === selectedEquipmentId);
      if (eq) {
        setSelectedEquipment(eq);
        if (eq.trajectory) {
          const startTime = new Date(eq.trajectory.startTime).getTime();
          const endTime = new Date(eq.trajectory.endTime).getTime();
          const duration = (endTime - startTime) / 1000;
          setTimelineState(prev => ({ ...prev, duration }));
        }
      }
    }
  }, [selectedEquipmentId, equipment]);

  return (
    <div className={className} style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        shadows
        gl={{ 
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1,
        }}
        camera={{
          position: initialCameraPosition,
          fov: 60,
          near: 0.1,
          far: 1000,
        }}
      >
        <Suspense fallback={<Loader />}>
          <OrbitControls
            makeDefault
            enableDamping
            dampingFactor={0.05}
            minDistance={5}
            maxDistance={200}
            maxPolarAngle={Math.PI / 2.1}
          />
          
          <SceneContent
            equipment={equipment}
            zones={zones}
            selectedEquipmentId={selectedEquipment?.id}
            selectedZoneId={selectedZone?.id}
            timelineState={timelineState}
            heatmapCells={showHeatmap ? heatmapCells : []}
            showHeatmap={showHeatmap}
            onEquipmentClick={handleEquipmentClick}
            onZoneClick={handleZoneClick}
          />
        </Suspense>
      </Canvas>

      {/* 进度统计面板 */}
      <ProgressStatsPanel zones={zones} />

      {/* 轨迹回放控制 UI */}
      {selectedEquipment?.trajectory && showControls && (
        <TrajectoryControlUI
          isPlaying={timelineState.isPlaying}
          playbackSpeed={timelineState.playbackSpeed}
          progress={timelineState.progress}
          duration={timelineState.duration}
          onPlayPause={handlePlayPause}
          onSpeedChange={handleSpeedChange}
          onProgressChange={handleProgressChange}
          onRestart={handleRestart}
        />
      )}

      {/* 选中的设备信息 */}
      {selectedEquipment && (
        <div
          style={{
            position: 'absolute',
            bottom: '20px',
            left: '20px',
            background: 'rgba(0, 0, 0, 0.8)',
            borderRadius: '8px',
            padding: '16px',
            color: 'white',
            fontSize: '12px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            maxWidth: '250px',
          }}
        >
          <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '8px' }}>
            {selectedEquipment.name}
          </div>
          <div style={{ display: 'grid', gap: '4px', opacity: 0.8 }}>
            <div>类型: {selectedEquipment.type}</div>
            <div>状态: {selectedEquipment.status}</div>
            <div>位置: ({selectedEquipment.position.x.toFixed(1)}, {selectedEquipment.position.z.toFixed(1)})</div>
            {selectedEquipment.operator && <div>操作员: {selectedEquipment.operator}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

// 导出组件和类型
export type { Scheduler3DProps };
export default Scheduler3D;
