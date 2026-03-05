# -*- coding: utf-8 -*-
"""
Three.js 适配器

将 BIM 数据转换为 Three.js 兼容格式
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum
import json


class MaterialType(str, Enum):
    """材质类型"""
    BASIC = "basic"
    STANDARD = "standard"
    PHONG = "phong"
    PHYSICAL = "physical"


class MeshData(BaseModel):
    """网格数据"""
    id: str
    name: str
    
    # 几何类型
    geometry_type: str  # "box", "extruded", "triangulated", "buffer"
    
    # 边界盒
    position: Optional[Dict[str, float]] = None
    size: Optional[Dict[str, float]] = None
    rotation: Optional[Dict[str, float]] = None
    
    # 三角网格数据
    vertices: Optional[List[float]] = None
    normals: Optional[List[float]] = None
    indices: Optional[List[int]] = None
    uvs: Optional[List[float]] = None
    
    # 材质
    material_type: MaterialType = MaterialType.STANDARD
    color: str = "#CCCCCC"
    opacity: float = 1.0
    metalness: float = 0.0
    roughness: float = 0.5
    
    # 元数据
    metadata: Dict[str, Any] = {}


class SceneConfig(BaseModel):
    """场景配置"""
    # 相机
    camera_type: str = "perspective"
    camera_fov: float = 60.0
    camera_position: Dict[str, float] = {"x": 0, "y": 10, "z": 20}
    camera_target: Dict[str, float] = {"x": 0, "y": 0, "z": 0}
    
    # 灯光
    ambient_light: Dict[str, Any] = {"color": "#ffffff", "intensity": 0.6}
    directional_light: Dict[str, Any] = {
        "color": "#ffffff",
        "intensity": 0.8,
        "position": {"x": 10, "y": 20, "z": 10}
    }
    
    # 环境
    background_color: str = "#1a1a2e"
    enable_shadows: bool = True
    enable_grid: bool = True
    
    # 性能
    max_vertices: int = 100000
    LOD_enabled: bool = True


class ThreeJSAdapter:
    """Three.js 适配器
    
    将 BIM 数据转换为可被 Three.js 渲染的格式
    """
    
    # BIM 元素类型到颜色映射
    ELEMENT_COLORS = {
        "beam": "#FF6B6B",
        "column": "#4ECDC4",
        "wall": "#45B7D1",
        "slab": "#96CEB4",
        "foundation": "#D4A574",
        "door": "#FFEAA7",
        "window": "#74B9FF",
        "stairs": "#A29BFE",
        "railing": "#FD79A8",
        "duct": "#FDCB6E",
        "pipe": "#E17055",
        "equipment": "#00CEC9",
        "space": "#DFE6E9",
        "unknown": "#B2BEC3"
    }
    
    def __init__(self, config: Optional[SceneConfig] = None):
        self.config = config or SceneConfig()
        self.meshes: List[MeshData] = []
    
    def convert_bim_project(
        self,
        bim_project: Any,
        sample_limit: int = 5000
    ) -> Dict[str, Any]:
        """转换 BIM 项目到 Three.js 场景数据"""
        
        meshes = []
        
        # 转换构件为网格
        elements = list(bim_project.elements.values())
        
        # 限制数量以保证性能
        if len(elements) > sample_limit:
            elements = elements[:sample_limit]
        
        for element in elements:
            mesh = self.convert_element(element)
            if mesh:
                meshes.append(mesh)
        
        self.meshes = meshes
        
        return self._build_scene_data(bim_project)
    
    def convert_element(self, element: Any) -> Optional[MeshData]:
        """转换单个构件"""
        
        # 获取颜色
        color = self.ELEMENT_COLORS.get(
            element.element_type.value,
            self.ELEMENT_COLORS["unknown"]
        )
        
        # 解析几何
        if element.geometry:
            geometry_type = element.geometry.type
            
            if geometry_type == "box":
                return self._convert_box(element, color)
            elif geometry_type == "extruded":
                return self._convert_extruded(element, color)
            elif geometry_type == "triangulated":
                return self._convert_triangulated(element, color)
        
        # 默认使用边界盒
        return self._convert_default(element, color)
    
    def _convert_box(self, element: Any, color: str) -> MeshData:
        """转换盒体几何"""
        bbox = element.geometry.bounding_box or {}
        
        size = {
            "x": bbox.get("max_x", 1) - bbox.get("min_x", 0),
            "y": bbox.get("max_y", 1) - bbox.get("min_y", 0),
            "z": bbox.get("max_z", 1) - bbox.get("min_z", 0)
        }
        
        position = element.position or {}
        
        return MeshData(
            id=element.id,
            name=element.name or element.element_type.value,
            geometry_type="box",
            position={"x": position.get("x", 0), "y": position.get("y", 0), "z": position.get("z", 0)},
            size=size,
            color=color,
            metadata={
                "ifc_type": element.ifc_type,
                "element_type": element.element_type.value
            }
        )
    
    def _convert_extruded(self, element: Any, color: str) -> MeshData:
        """转换拉伸体"""
        extrusion = element.geometry.extrusion or {}
        depth = extrusion.get("depth", 1)
        
        position = element.position or {}
        
        return MeshData(
            id=element.id,
            name=element.name or element.element_type.value,
            geometry_type="extruded",
            position={"x": position.get("x", 0), "y": position.get("y", 0), "z": position.get("z", 0)},
            size={"x": 1, "y": 1, "z": depth},
            color=color,
            metadata={
                "ifc_type": element.ifc_type,
                "extrusion_depth": depth
            }
        )
    
    def _convert_triangulated(self, element: Any, color: str) -> MeshData:
        """转换三角网格"""
        triangulated = element.geometry.triangulated or {}
        
        # 简化：只传递顶点数量信息
        return MeshData(
            id=element.id,
            name=element.name or element.element_type.value,
            geometry_type="triangulated",
            color=color,
            metadata={
                "ifc_type": element.ifc_type,
                "vertex_count": triangulated.get("vertex_count", 0),
                "face_count": triangulated.get("face_count", 0)
            }
        )
    
    def _convert_default(self, element: Any, color: str) -> MeshData:
        """默认转换 (使用位置)"""
        position = element.position or {}
        
        return MeshData(
            id=element.id,
            name=element.name or element.element_type.value,
            geometry_type="box",
            position={"x": position.get("x", 0), "y": position.get("y", 0), "z": position.get("z", 0)},
            size={"x": 1, "y": 1, "z": 1},
            color=color,
            metadata={
                "ifc_type": element.ifc_type,
                "element_type": element.element_type.value
            }
        )
    
    def _build_scene_data(self, bim_project: Any) -> Dict[str, Any]:
        """构建场景数据"""
        
        return {
            "config": self.config.dict(),
            "project": {
                "id": bim_project.id,
                "name": bim_project.name,
                "ifc_version": bim_project.ifc_version.value
            },
            "meshes": [m.dict() for m in self.meshes],
            "statistics": {
                "total_meshes": len(self.meshes),
                "by_type": self._count_by_type()
            }
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for mesh in self.meshes:
            mesh_type = mesh.metadata.get("element_type", "unknown")
            counts[mesh_type] = counts.get(mesh_type, 0) + 1
        return counts
    
    def get_threejs_code(self) -> str:
        """生成 Three.js 代码 (用于调试/独立查看器)"""
        
        code = f"""
// NeuralSite BIM Three.js Viewer
// Auto-generated code

import * as THREE from 'three';
import {{ OrbitControls }} from 'orbit-controls';

// Scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color('{self.config.background_color}');

// Camera
const camera = new THREE.PerspectiveCamera(
    {self.config.camera_fov},
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(
    {self.config.camera_position['x']},
    {self.config.camera_position['y']},
    {self.config.camera_position['z']}
);

// Renderer
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = {str(self.config.enable_shadows).lower()};
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set({self.config.camera_target['x']}, {self.config.camera_target['y']}, {self.config.camera_target['z']});

// Lighting
const ambientLight = new THREE.AmbientLight(
    '{self.config.ambient_light["color"]}',
    {self.config.ambient_light["intensity"]}
);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(
    '{self.config.directional_light["color"]}',
    {self.config.directional_light["intensity"]}
);
directionalLight.position.set(
    {self.config.directional_light["position"]["x"]},
    {self.config.directional_light["position"]["y"]},
    {self.config.directional_light["position"]["z"]}
);
scene.add(directionalLight);

// Grid
{(f"const gridHelper = new THREE.GridHelper(100, 100); scene.add(gridHelper);" if self.config.enable_grid else "")}

// BIM Elements
const meshes = [];
"""
        
        # 添加每个构件
        for mesh in self.meshes[:100]:  # 限制数量
            if mesh.geometry_type == "box":
                code += f"""
// {mesh.name}
const box_{mesh.id[:8]} = new THREE.BoxGeometry({mesh.size['x']}, {mesh.size['y']}, {mesh.size['z']});
const material_{mesh.id[:8]} = new THREE.MeshStandardMaterial({{ color: '{mesh.color}', opacity: {mesh.opacity}, transparent: {mesh.opacity < 1} }});
const mesh_{mesh.id[:8]} = new THREE.Mesh(box_{mesh.id[:8]}, material_{mesh.id[:8]});
mesh_{mesh.id[:8]}.position.set({mesh.position['x']}, {mesh.position['y']}, {mesh.position['z']});
mesh_{mesh.id[:8]}.userData = {{ id: '{mesh.id}', name: '{mesh.name}' }};
scene.add(mesh_{mesh.id[:8]});
meshes.push(mesh_{mesh.id[:8]});
"""
        
        code += """
// Raycaster for selection
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('click', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(meshes);
    
    if (intersects.length > 0) {
        const selected = intersects[0].object;
        console.log('Selected:', selected.userData);
        // Emit event or call callback
    }
});

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

// Handle resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
"""
        
        return code
    
    def export_json(self) -> str:
        """导出为 JSON"""
        return json.dumps({
            "config": self.config.dict(),
            "meshes": [m.dict() for m in self.meshes]
        }, indent=2)


def create_viewer_data(bim_project: Any, config: Optional[SceneConfig] = None) -> Dict[str, Any]:
    """便捷函数：创建查看器数据"""
    adapter = ThreeJSAdapter(config)
    return adapter.convert_bim_project(bim_project)
