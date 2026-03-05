# NeuralSite 三维预览增强建议书

> 编制时间: 2026-03-05
> 版本: V1.0
> 参考: Google Model Viewer, Online3DViewer, Babylon.js, three.js editor, chili3d

---

## 一、GitHub高星3D项目分析

### 1.1 纯查看器项目 (Viewer)

| 项目 | Stars | 核心技术 | 亮点 | 适合场景 |
|------|-------|----------|------|----------|
| **google/model-viewer** | 7.9k+ | Web Component + Three.js | Google出品，`<model-viewer>`标签一键嵌入，支持glTF/GLB/USD，AR查看，动画，环境光 | 产品展示/电商 |
| **kovacsv/Online3DViewer** | 3.4k+ | Three.js | 支持OBJ/STL/PLY/glTF等多种格式，测量、截图、爆炸视图。3dviewer.net就是它驱动的 | 轻量在线查看 |
| **BabylonJS/Babylon.js** | 23k++ | Babylon.js | 完整3D引擎，内置Viewer组件，支持glTF/GLB/OBJ，动画/物理/PBR | 功能丰富的Viewer |
| **f3d-app/f3d** | 4.2k+ | VTK/OpenGL | 支持STEP/IGES/PLY/Alembic等科学/工业格式，极简主义+高性能 | CAD/工程模型 |

### 1.2 编辑器项目 (Editor)

| 项目 | Stars | 核心技术 | 亮点 |
|------|-------|----------|------|
| **webglstudio.js** | 5.3k+ | WebGL + 自研 | 浏览器内完整3D编辑器：场景编辑、材质编辑、着色器编辑、节点图、虚拟文件系统。功能最全的纯浏览器3D IDE |
| **chili3d** | 4.3k+ | TypeScript + OpenCascade + Three.js | 浏览器端CAD编辑器，支持建模、编辑、渲染。接近原生性能，适合在线3D设计/参数化建模 |
| **three.js editor** | 100k+ | Three.js | 官方Three.js Editor，支持拖拽建模、材质、灯光、动画、导出glTF。最经典的浏览器3D编辑器 |

### 1.3 AI+3D项目

| 项目 | Stars | 核心技术 | 亮点 |
|------|-------|----------|------|
| **sd-webui-3d-editor** | 100-200+ | Three.js + Stable Diffusion | SD WebUI扩展：3D场景编辑→生成ControlNet参考图。AI+3D结合，新兴热门 |

---

## 二、当前NeuralSite三维问题

### 2.1 已识别问题

| 问题 | 现状 |
|------|------|
| **三维预览无差异** | 不同项目显示相同内容 |
| **项目数据无隔离** | 无法按项目加载不同模型 |
| **交互功能弱** | 缺少测量/标注/截面查看 |
| **格式支持少** | 仅支持有限格式 |

### 2.2 差距分析

| 维度 | 当前 | 参考项目 |
|------|------|----------|
| 模型加载 | 静态 | model-viewer动态加载 |
| 项目隔离 | 无 | 需要按项目ID加载 |
| 测量功能 | 无 | Online3DViewer有 |
| 格式支持 | 有限 | Online3DViewer支持20+格式 |
| 编辑能力 | 无 | chili3d有CAD编辑 |

---

## 三、改进方案

### 3.1 三维查看器增强（参考model-viewer + Online3DViewer）

| 功能 | 实现方式 | 参考项目 |
|------|----------|----------|
| 模型动态加载 | 根据project_id/route_id加载不同模型 | model-viewer |
| 多格式支持 | OBJ/STL/PLY/glTF/GLB | Online3DViewer |
| 测量工具 | 距离/高度/角度测量 | Online3DViewer |
| 截图功能 | Canvas导出PNG | Online3DViewer |
| AR查看 | WebXR支持（移动端） | model-viewer |

### 3.2 项目数据隔离

| 功能 | 实现方式 |
|------|----------|
| 项目选择器 | 全局项目下拉框，切换后刷新三维 |
| 数据联动 | 三维组件监听projectStore变化 |
| 路线绑定 | 每个项目关联多条路线 |

### 3.3 交互功能增强

| 功能 | 说明 |
|------|------|
| 视角控制 | OrbitControls增强 |
| 标注功能 | 点击添加文字标注 |
| 截面查看 | 横断面切割查看 |
| 漫游模式 | 沿路线自动漫游 |

### 3.4 进阶编辑能力（参考chili3d）

| 功能 | 说明 |
|------|------|
| 模型导入 | 支持更多工程格式 |
| 简单编辑 | 移动/旋转/缩放 |
| 测量标注 | 距离/角度/面积 |

## 四、碰撞检测与调度功能（核心功能）

### 4.1 碰撞检测3D可视化

| 功能 | 说明 |
|------|------|
| **碰撞标注** | 在3D模型上标注碰撞点（红色高亮） |
| **碰撞列表** | 列出所有碰撞位置，支持跳转查看 |
| **碰撞类型** | 管道碰撞、设备碰撞、结构碰撞 |
| **碰撞详情** | 点击显示碰撞位置、严重程度、建议解决方案 |

**技术实现：**
- 碰撞数据API返回位置坐标
- 在3D场景中用红色Sphere标注碰撞点
- 支持点击跳转和详情弹窗

### 4.2 施工调度3D可视化

| 功能 | 说明 |
|------|------|
| **机械模型** | 挖掘机、摊铺机、压路机等3D模型 |
| **实时位置** | GPS坐标映射到3D场景 |
| **轨迹回放** | 施工轨迹时间轴回放 |
| **调度指令** | 在3D中显示调度指令（箭头/路径） |
| **进度叠加** | 施工进度热力图显示 |

**技术实现：**
- 使用GLTF模型加载机械设备
- WebSocket实时更新位置
- 时间轴组件控制轨迹回放

### 4.3 统一架构

```
src/components/three/
├── CollisionViewer.tsx     # 碰撞检测3D显示
├── Scheduler3D.tsx       # 调度3D显示
├── EquipmentModel.tsx    # 设备模型
├── TrajectoryPlayer.tsx  # 轨迹回放
├── ProgressHeatmap.tsx   # 进度热力图
└── DispatchOverlay.tsx   # 调度指令层
```

---

## 五、技术选型

### 4.1 推荐方案

| 层级 | 技术 | 参考 |
|------|------|------|
| **主框架** | React Three Fiber | react-three-fiber (30k) |
| **辅助库** | @react-three/drei | drei (9.5k) |
| **UI组件** | @react-three/uikit | 布局 |
| **编辑器** | 自研或fork chili3d | chili3d (4.3k) |

### 4.2 组件架构

```
src/
├── components/
│   ├── three/                 # Three.js组件
│   │   ├── ModelViewer.tsx   # 主查看器
│   │   ├── ModelLoader.tsx   # 模型加载器
│   │   ├── Measurement.tsx  # 测量工具
│   │   ├── Annotations.tsx   # 标注
│   │   ├── CrossSection.tsx  # 截面查看
│   │   └── Route3D.tsx       # 路线3D可视化
│   │
│   ├── ui/                   # UI组件
│   │   ├── ViewerControls.tsx  # 查看器控制面板
│   │   ├── MeasurementPanel.tsx # 测量面板
│   │   └── LayerPanel.tsx       # 图层面板
│   │
│   └── layout/                # 布局
│
├── hooks/
│   ├── useModelLoader.ts     # 模型加载Hook
│   ├── useMeasurement.ts     # 测量Hook
│   └── useProject3D.ts      # 项目3D数据Hook
│
└── stores/
    └── project3DStore.ts    # 3D状态管理
```

---

## 五、实施计划

### 阶段1：基础增强（1周）

- [ ] 项目隔离的三维加载
- [ ] 基本视角控制
- [ ] 多格式模型支持

### 阶段2：交互增强（1周）

- [ ] 测量工具（距离/高度）
- [ ] 标注功能
- [ ] 截图导出

### 阶段3：工程功能（2周）

- [ ] 路线3D可视化
- [ ] 桩号标注
- [ ] 横断面预览
- [ ] 截面切割
- [ ] **碰撞检测可视化** - 管道/设备碰撞检测结果3D标注
- [ ] **调度可视化** - 施工机械/车辆实时位置3D显示

### 阶段4：进阶功能（可选）

- [ ] 简单模型编辑
- [ ] AI辅助分析

---

## 六、总结

| 维度 | 当前 | 目标 |
|------|------|------|
| 模型加载 | 静态 | 动态按项目 |
| 测量功能 | 无 | 距离/高度/角度 |
| 格式支持 | 有限 | 20+格式 |
| 项目隔离 | 无 | 完整隔离 |
| 编辑能力 | 无 | 基础编辑 |

**推荐参考项目**：
- **查看器**: model-viewer (简单), Online3DViewer (功能全)
- **编辑器**: chili3d (CAD), three.js editor (经典)

---

*编制单位: MiniMax Agent*
*日期: 2026-03-05*
