# -*- coding: utf-8 -*-
"""
BIM 3D 查看器组件

提供前端的 WebGL 查看器组件
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
from enum import Enum
import json


class ViewerAction(str, Enum):
    """查看器动作"""
    ZOOM_TO_FIT = "zoomToFit"
    ZOOM_TO_ELEMENT = "zoomToElement"
    SELECT = "select"
    HIGHLIGHT = "highlight"
    ISOLATE = "isolate"
    SHOW = "showAll"
    SECTION_ALL_BOX = "sectionBox"
    MEASURE = "measure"


class ViewerComponent(BaseModel):
    """查看器组件配置"""
    id: str
    type: str = "bim-viewer"
    
    # 场景配置
    scene_config: Optional[Dict[str, Any]] = None
    
    # 数据源
    data_url: Optional[str] = None
    embedded_data: Optional[Dict[str, Any]] = None
    
    # 交互配置
    enable_selection: bool = True
    enable_measurement: bool = True
    enable_sections: bool = True
    enable_explode: bool = False
    
    # UI 配置
    show_toolbar: bool = True
    show_tree: bool = True
    show_properties: bool = True
    show_rulers: bool = False
    
    # 回调
    on_selection_changed: Optional[str] = None
    on_hover: Optional[str] = None


class SelectionInfo(BaseModel):
    """选择信息"""
    element_id: str
    element_name: str
    element_type: str
    properties: Dict[str, Any] = {}


class BIMViewer:
    """BIM 查看器管理器
    
    生成前端集成所需的配置和代码
    """
    
    def __init__(self):
        self.components: Dict[str, ViewerComponent] = {}
        self.selection_callbacks: List[Callable] = []
    
    def create_viewer_component(
        self,
        viewer_id: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> ViewerComponent:
        """创建查看器组件"""
        
        options = options or {}
        
        component = ViewerComponent(
            id=viewer_id,
            scene_config=options.get("scene_config"),
            embedded_data=data,
            enable_selection=options.get("enable_selection", True),
            enable_measurement=options.get("enable_measurement", True),
            enable_sections=options.get("enable_sections", True),
            enable_explode=options.get("enable_explode", False),
            show_toolbar=options.get("show_toolbar", True),
            show_tree=options.get("show_tree", True),
            show_properties=options.get("show_properties", True),
            show_rulers=options.get("show_rulers", False)
        )
        
        self.components[viewer_id] = component
        return component
    
    def generate_html_template(
        self,
        viewer_id: str,
        component: ViewerComponent
    ) -> str:
        """生成 HTML 模板"""
        
        # 嵌入数据
        data_json = json.dumps(component.embedded_data or {})
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>NeuralSite BIM Viewer</title>
    <style>
        body {{ margin: 0; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        #viewer-container {{ width: 100vw; height: 100vh; position: relative; }}
        #bim-viewer-{viewer_id} {{ width: 100%; height: 100%; }}
        
        /* Toolbar */
        .toolbar {{
            position: absolute;
            top: 10px;
            left: 10px;
            display: flex;
            gap: 8px;
            z-index: 100;
        }}
        .toolbar button {{
            padding: 8px 12px;
            background: rgba(30, 30, 46, 0.9);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }}
        .toolbar button:hover {{ background: rgba(50, 50, 70, 0.9); }}
        
        /* Properties Panel */
        .properties-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 300px;
            max-height: calc(100% - 20px);
            background: rgba(30, 30, 46, 0.95);
            color: #fff;
            border-radius: 8px;
            overflow: hidden;
            display: none;
            z-index: 100;
        }}
        .properties-panel.visible {{ display: block; }}
        .properties-header {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-weight: 600;
        }}
        .properties-content {{
            padding: 12px 16px;
            overflow-y: auto;
            max-height: calc(100% - 50px);
        }}
        .property-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .property-name {{ color: #888; font-size: 12px; }}
        .property-value {{ color: #fff; font-size: 12px; }}
        
        /* Loading */
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="viewer-container">
        <div id="bim-viewer-{viewer_id}"></div>
        
        {self._generate_toolbar() if component.show_toolbar else ''}
        
        {self._generate_properties_panel() if component.show_properties else ''}
        
        <div class="loading" id="loading">Loading BIM data...</div>
    </div>
    
    <script type="importmap">
    {{
        "imports": {{
            "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
            "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>
    
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        
        // Embedded data
        const VIEWER_DATA = {data_json};
        
        // Scene setup
        const container = document.getElementById('bim-viewer-{viewer_id}');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color('#1a1a2e');
        
        // Camera
        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(20, 20, 20);
        
        // Renderer
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        
        // Lighting
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(10, 20, 10);
        scene.add(dirLight);
        
        // Grid
        const grid = new THREE.GridHelper(100, 100, 0x333333, 0x222222);
        scene.add(grid);
        
        // Meshes storage
        const meshes = new Map();
        let selectedMesh = null;
        
        // Create meshes from data
        function createMeshes() {{
            const meshData = VIEWER_DATA.meshes || [];
            
            meshData.forEach(data => {{
                let geometry;
                
                if (data.geometry_type === 'box') {{
                    geometry = new THREE.BoxGeometry(
                        data.size?.x || 1,
                        data.size?.y || 1,
                        data.size?.z || 1
                    );
                }} else {{
                    // Default box
                    geometry = new THREE.BoxGeometry(1, 1, 1);
                }}
                
                const material = new THREE.MeshStandardMaterial({{
                    color: data.color || '#cccccc',
                    metalness: 0.1,
                    roughness: 0.7
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(
                    data.position?.x || 0,
                    data.position?.y || 0,
                    data.position?.z || 0
                );
                
                mesh.userData = {{
                    id: data.id,
                    name: data.name,
                    type: data.metadata?.element_type || 'unknown',
                    properties: data.metadata || {{}}
                }};
                
                scene.add(mesh);
                meshes.set(data.id, mesh);
            }});
            
            // Hide loading
            document.getElementById('loading').style.display = 'none';
            
            // Fit camera
            fitCamera();
        }}
        
        // Fit camera to content
        function fitCamera() {{
            const box = new THREE.Box3().setFromObject(scene);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            controls.target.copy(center);
            
            const maxDim = Math.max(size.x, size.y, size.z);
            camera.position.set(
                center.x + maxDim,
                center.y + maxDim,
                center.z + maxDim
            );
            camera.lookAt(center);
        }}
        
        // Selection handling
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        renderer.domElement.addEventListener('click', (event) => {{
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects([...meshes.values()]);
            
            // Clear previous selection
            if (selectedMesh) {{
                selectedMesh.material.emissive.setHex(0x000000);
            }}
            
            if (intersects.length > 0) {{
                selectedMesh = intersects[0].object;
                selectedMesh.material.emissive.setHex(0x333333);
                
                showProperties(selectedMesh.userData);
            }} else {{
                selectedMesh = null;
                hideProperties();
            }}
        }});
        
        // Show properties panel
        function showProperties(data) {{
            const panel = document.getElementById('properties-panel');
            const content = document.getElementById('properties-content');
            
            let html = `
                <div class="property-row">
                    <span class="property-name">Name</span>
                    <span class="property-value">${{data.name}}</span>
                </div>
                <div class="property-row">
                    <span class="property-name">Type</span>
                    <span class="property-value">${{data.type}}</span>
                </div>
            `;
            
            Object.entries(data.properties || {{}}).forEach(([key, value]) => {{
                html += `
                    <div class="property-row">
                        <span class="property-name">${{key}}</span>
                        <span class="property-value">${{value}}</span>
                    </div>
                `;
            }});
            
            content.innerHTML = html;
            panel.classList.add('visible');
        }}
        
        function hideProperties() {{
            document.getElementById('properties-panel').classList.remove('visible');
        }}
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        
        // Initialize
        createMeshes();
        animate();
        
        // Handle resize
        window.addEventListener('resize', () => {{
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }});
    </script>
</body>
</html>"""
    
    def _generate_toolbar(self) -> str:
        """生成工具栏 HTML"""
        return """
        <div class="toolbar">
            <button onclick="fitCamera()">Fit</button>
            <button onclick="toggleWireframe()">Wireframe</button>
            <button onclick="resetView()">Reset</button>
        </div>
        """
    
    def _generate_properties_panel(self) -> str:
        """生成属性面板 HTML"""
        return """
        <div class="properties-panel" id="properties-panel">
            <div class="properties-header">Properties</div>
            <div class="properties-content" id="properties-content">
            </div>
        </div>
        """
    
    def get_viewer_html(
        self,
        viewer_id: str,
        bim_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """获取查看器 HTML"""
        
        component = self.create_viewer_component(viewer_id, bim_data, options)
        return self.generate_html_template(viewer_id, component)


def create_bim_viewer(
    bim_project: Any,
    viewer_id: str = "main"
) -> Dict[str, Any]:
    """便捷函数：创建 BIM 查看器数据"""
    
    from .threejs_adapter import ThreeJSAdapter, SceneConfig
    
    adapter = SceneConfig()
    threejs_adapter = ThreeJSAdapter(adapter)
    scene_data = threejs_adapter.convert_bim_project(bim_project)
    
    viewer = BIMViewer()
    component = viewer.create_viewer_component(viewer_id, scene_data)
    
    return {
        "component": component.dict(),
        "html": viewer.generate_html_template(viewer_id, component)
    }
