/**
 * EquipmentModel - 机械设备3D模型组件
 * 支持挖掘机、摊铺机、压路机等设备的3D显示
 */

import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, Html } from '@react-three/drei';
import * as THREE from 'three';
import type { Equipment, EquipmentType } from '../../types/schedule';

interface EquipmentModelProps {
  equipment: Equipment;
  isSelected?: boolean;
  showLabel?: boolean;
  onClick?: (equipment: Equipment) => void;
  highlightColor?: string;
}

// 设备类型的默认颜色
const equipmentColors: Record<EquipmentType, string> = {
  excavator: '#FFA500', // 橙色
  paver: '#4169E1',     // 皇家蓝
  roller: '#FFD700',    // 金色
  bulldozer: '#FF6347', // 番茄红
  loader: '#32CD32',    // 绿宝石绿
  truck: '#8B4513',     // 鞍褐色
};

// 设备类型的默认GLTF模型路径（可替换为实际模型）
const equipmentModelPaths: Record<EquipmentType, string> = {
  excavator: '/models/excavator.glb',
  paver: '/models/paver.glb',
  roller: '/models/roller.glb',
  bulldozer: '/models/bulldozer.glb',
  loader: '/models/loader.glb',
  truck: '/models/truck.glb',
};

// 设备类型的中文名称
const equipmentNames: Record<EquipmentType, string> = {
  excavator: '挖掘机',
  paver: '摊铺机',
  roller: '压路机',
  bulldozer: '推土机',
  loader: '装载机',
  truck: '卡车',
};

// 状态指示器颜色
const statusColors: Record<string, string> = {
  idle: '#808080',      // 灰色
  working: '#00FF00',   // 绿色
  maintenance: '#FFA500', // 橙色
  offline: '#FF0000',   // 红色
};

// 加载GLTF模型
function useEquipmentModel(modelPath: string | undefined) {
  const { scene, nodes, materials } = useGLTF(modelPath || '/models/placeholder.glb');
  
  return useMemo(() => {
    if (!modelPath) return null;
    return { scene, nodes, materials };
  }, [modelPath, scene, nodes, materials]);
}

// 占位符模型（当没有GLTF模型时使用）
function PlaceholderModel({ 
  type, 
  color,
  isSelected 
}: { 
  type: EquipmentType;
  color: string;
  isSelected?: boolean;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // 根据设备类型创建不同的几何体
  const geometry = useMemo(() => {
    switch (type) {
      case 'excavator':
        return {
          body: new THREE.BoxGeometry(2, 1.5, 3),
          arm: new THREE.BoxGeometry(0.3, 2, 0.3),
          bucket: new THREE.BoxGeometry(0.8, 0.5, 0.8),
          cabin: new THREE.BoxGeometry(1.2, 1.2, 1.2),
        };
      case 'paver':
        return {
          body: new THREE.BoxGeometry(3, 1.5, 5),
          hopper: new THREE.BoxGeometry(2.5, 1, 1.5),
          screed: new THREE.BoxGeometry(3, 0.3, 1),
        };
      case 'roller':
        return {
          body: new THREE.BoxGeometry(2, 1.5, 3),
          frontWheel: new THREE.CylinderGeometry(0.8, 0.8, 2, 16),
          rearWheel: new THREE.CylinderGeometry(0.8, 0.8, 2, 16),
        };
      case 'bulldozer':
        return {
          body: new THREE.BoxGeometry(2.5, 1.5, 3),
          blade: new THREE.BoxGeometry(3, 1.2, 0.5),
          cabin: new THREE.BoxGeometry(1.5, 1.2, 1.5),
        };
      case 'loader':
        return {
          body: new THREE.BoxGeometry(2, 1.5, 3),
          bucket: new THREE.BoxGeometry(2, 0.8, 1),
          arm: new THREE.BoxGeometry(0.3, 1.5, 0.3),
        };
      case 'truck':
        return {
          body: new THREE.BoxGeometry(2, 1.5, 4),
          cabin: new THREE.BoxGeometry(1.8, 1.2, 1.5),
          wheels: new THREE.CylinderGeometry(0.4, 0.4, 1.8, 8),
        };
      default:
        return { body: new THREE.BoxGeometry(2, 1.5, 3) };
    }
  }, [type]);

  return (
    <group ref={groupRef}>
      {/* 主体 */}
      <mesh geometry={geometry.body} castShadow receiveShadow>
        <meshStandardMaterial 
          color={color} 
          metalness={0.4} 
          roughness={0.6}
          emissive={isSelected ? color : '#000000'}
          emissiveIntensity={isSelected ? 0.3 : 0}
        />
      </mesh>

      {/* 驾驶室 */}
      {geometry.cabin && (
        <mesh geometry={geometry.cabin} position={[0, 1.5, 0.5]} castShadow>
          <meshStandardMaterial color="#87CEEB" metalness={0.3} roughness={0.4} transparent opacity={0.7} />
        </mesh>
      )}

      {/* 铲斗/刀板 */}
      {geometry.bucket && (
        <mesh geometry={geometry.bucket} position={[0, 0.5, 2]} castShadow>
          <meshStandardMaterial color="#696969" metalness={0.6} roughness={0.4} />
        </mesh>
      )}
      {geometry.blade && (
        <mesh geometry={geometry.blade} position={[0, 0.3, 2]} castShadow>
          <meshStandardMaterial color="#696969" metalness={0.6} roughness={0.4} />
        </mesh>
      )}
      {geometry.screed && (
        <mesh geometry={geometry.screed} position={[0, -0.5, 2.5]} castShadow>
          <meshStandardMaterial color="#333333" metalness={0.5} roughness={0.5} />
        </mesh>
      )}

      {/* 车轮 */}
      {geometry.frontWheel && (
        <>
          <mesh geometry={geometry.frontWheel} position={[0, -0.5, 1]} rotation={[0, 0, Math.PI / 2]} castShadow>
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
          <mesh geometry={geometry.rearWheel} position={[0, -0.5, -1]} rotation={[0, 0, Math.PI / 2]} castShadow>
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
        </>
      )}
      {geometry.wheels && (
        <>
          <mesh position={[0.8, -0.5, 1.2]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.4, 0.4, 0.4, 16]} />
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
          <mesh position={[-0.8, -0.5, 1.2]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.4, 0.4, 0.4, 16]} />
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
          <mesh position={[0.8, -0.5, -1.2]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.4, 0.4, 0.4, 16]} />
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
          <mesh position={[-0.8, -0.5, -1.2]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.4, 0.4, 0.4, 16]} />
            <meshStandardMaterial color="#1a1a1a" metalness={0.3} roughness={0.8} />
          </mesh>
        </>
      )}

      {/* 动臂（挖掘机） */}
      {type === 'excavator' && (
        <group position={[0.5, 1, 0]}>
          <mesh position={[0, 1, 0.5]} rotation={[0.5, 0, 0]}>
            <boxGeometry args={[0.3, 2, 0.3]} />
            <meshStandardMaterial color={color} metalness={0.4} roughness={0.6} />
          </mesh>
        </group>
      )}

      {/* 摊铺机熨平板 */}
      {type === 'paver' && geometry.screed && (
        <mesh geometry={geometry.screed} position={[0, 0.3, 2.5]} castShadow>
          <meshStandardMaterial color="#333333" metalness={0.5} roughness={0.5} />
        </mesh>
      )}
    </group>
  );
}

// 设备标签组件
function EquipmentLabel({ 
  equipment, 
  isSelected 
}: { 
  equipment: Equipment;
  isSelected?: boolean;
}) {
  const statusColor = statusColors[equipment.status] || statusColors.idle;
  
  return (
    <Html
      position={[0, 4, 0]}
      center
      distanceFactor={20}
      style={{
        pointerEvents: 'none',
        userSelect: 'none',
      }}
    >
      <div
        style={{
          background: isSelected ? 'rgba(59, 130, 246, 0.9)' : 'rgba(0, 0, 0, 0.75)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'nowrap',
          border: isSelected ? '2px solid #3B82F6' : '1px solid rgba(255,255,255,0.3)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ fontWeight: 'bold' }}>{equipment.name}</div>
        <div style={{ fontSize: '10px', opacity: 0.8 }}>
          {equipmentNames[equipment.type]}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            marginTop: '2px',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: statusColor,
              display: 'inline-block',
            }}
          />
          <span style={{ fontSize: '10px' }}>
            {equipment.status === 'working' ? '工作中' :
             equipment.status === 'idle' ? '闲置' :
             equipment.status === 'maintenance' ? '维护' : '离线'}
          </span>
        </div>
      </div>
    </Html>
  );
}

// 主组件
export function EquipmentModel({
  equipment,
  isSelected = false,
  showLabel = true,
  onClick,
  highlightColor,
}: EquipmentModelProps) {
  const groupRef = useRef<THREE.Group>(null);
  const modelRef = useRef<THREE.Group>(null);
  
  // 尝试加载GLTF模型
  const gltfModel = useEquipmentModel(equipment.model || equipmentModelPaths[equipment.type]);
  
  const baseColor = equipmentColors[equipment.type];
  const displayColor = highlightColor || baseColor;
  
  // 设备位置和旋转
  const position: [number, number, number] = [
    equipment.position.x,
    equipment.position.y,
    equipment.position.z,
  ];
  
  const rotation: [number, number, number] = [
    equipment.rotation?.x || 0,
    equipment.rotation?.y || 0,
    equipment.rotation?.z || 0,
  ];

  // 动画效果：选中时轻微浮动
  useFrame((state) => {
    if (isSelected && modelRef.current) {
      modelRef.current.position.y = Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  // 处理点击事件
  const handleClick = (e: THREE.Event) => {
    e.stopPropagation();
    onClick?.(equipment);
  };

  return (
    <group
      ref={groupRef}
      position={position}
      rotation={rotation}
      onClick={handleClick}
    >
      <group ref={modelRef}>
        {gltfModel ? (
          // 使用GLTF模型
          <primitive
            object={gltfModel.scene.clone()}
            scale={1}
            castShadow
            receiveShadow
          />
        ) : (
          // 使用占位符模型
          <PlaceholderModel
            type={equipment.type}
            color={displayColor}
            isSelected={isSelected}
          />
        )}
      </group>

      {/* 选中高亮光环 */}
      {isSelected && (
        <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[2.5, 3, 32]} />
          <meshBasicMaterial
            color="#3B82F6"
            transparent
            opacity={0.5}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* 状态指示灯 */}
      <pointLight
        position={[0, 2, 0]}
        color={statusColors[equipment.status] || statusColors.idle}
        intensity={isSelected ? 2 : 0.5}
        distance={5}
      />

      {/* 设备标签 */}
      {showLabel && (
        <EquipmentLabel equipment={equipment} isSelected={isSelected} />
      )}
    </group>
  );
}

// 设备阴影
export function EquipmentShadow({ equipment }: { equipment: Equipment }) {
  return (
    <mesh
      position={[equipment.position.x, 0.01, equipment.position.z]}
      rotation={[-Math.PI / 2, 0, 0]}
      receiveShadow
    >
      <circleGeometry args={[2, 32]} />
      <meshBasicMaterial
        color="#000000"
        transparent
        opacity={0.3}
      />
    </mesh>
  );
}

export default EquipmentModel;
