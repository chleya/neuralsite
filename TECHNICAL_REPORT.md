# NeuralSite 技术及产品说明文档

> 编制时间: 2026-03-05
> 版本: V1.0

---

## 一、项目概览

### 1.1 项目定位
**NeuralSite（神经站点）** - 公路工程智能施工平台

- **目标**: 为公路施工提供智能化管理、数据分析、三维可视化的一体化平台
- **用户**: 施工管理人员、工程师、测量员
- **技术栈**:
  - 后端: Python FastAPI
  - 前端: React 18 + TypeScript + Vite
  - 3D: React Three Fiber (Three.js)
  - 数据库: SQLite (开发) / PostgreSQL (生产)
  - 移动端: Flutter

### 1.2 项目结构

```
neuralsite/
├── packages/
│   ├── core/           # 后端API (FastAPI)
│   │   ├── api/v1/     # API路由
│   │   │   └── routes/ # 业务路由
│   │   ├── models/     # 数据模型
│   │   ├── services/   # 业务服务
│   │   └── database/  # 数据库
│   │
│   ├── studio/         # 前端Web (React)
│   │   ├── src/
│   │   │   ├── pages/      # 页面组件
│   │   │   ├── components/ # UI组件
│   │   │   ├── three/     # 3D组件
│   │   │   ├── api/       # API客户端
│   │   │   └── stores/   # 状态管理
│   │   └── public/
│   │
│   └── mobile/        # 移动端 (Flutter)
│
└── GitHub: https://github.com/chleya/neuralsite
```

---

## 二、数据模型

### 2.1 核心实体

| 实体 | 说明 | 关键字段 |
|------|------|----------|
| **Project (项目)** | 工程项目 | name, description, location, status |
| **Route (路线)** | 公路路线 | project_id, name, length, start_station, end_station |
| **Station (桩号)** | 里程桩点 | route_id, station_number, elevation, coordinates |
| **CrossSection (横断面)** | 道路截面 | route_id, station, section_data |
| **Photo (照片)** | 施工照片 | station_id, file_path, tags, capture_date |
| **Issue (问题)** | 安全/质量问题 | project_id, type, severity, status, description |

### 2.2 数据关系

```
Project (项目)
├── Route (路线) 1:N
│   ├── Station (桩号) 1:N
│   │   └── Photo (照片) 1:N
│   └── CrossSection (横断面) 1:N
└── Issue (问题) 1:N
```

---

## 三、后端API

### 3.1 API端点统计

| 模块 | 路由数 | 状态 |
|------|--------|------|
| 认证 (auth) | 4 | ✅ |
| 项目 (projects) | 8 | ✅ |
| 路线 (routes) | 6 | ✅ |
| 桩号 (stations) | 8 | ✅ |
| 照片 (photos) | 8 | ✅ |
| 横断面 (cross_sections) | 6 | ✅ |
| 碰撞检测 (collisions) | 6 | ✅ |
| 知识库 (knowledge) | 4 | ✅ |
| 仪表盘 (dashboard) | 6 | ✅ |
| **总计** | **~56** | ✅ |

### 3.2 认证方式
- JWT Token认证
- Token过期时间: 30分钟
- 刷新Token机制: 未实现

---

## 四、前端功能

### 4.1 页面模块

| 页面 | 功能 | 状态 |
|------|------|------|
| 登录 | 用户认证 | ⚠️ 需后端 |
| 仪表盘 | 统计概览 | ✅ 简化版 |
| 项目列表 | 项目CRUD | ⚠️ 需API |
| 项目详情 | 项目管理 | ⚠️ 需API |
| 路线列表 | 路线CRUD | ⚠️ 需API |
| 桩号录入 | 桩号数据录入 | ⚠️ 需API |
| 桩号查询 | 桩号检索 | ⚠️ 需API |
| 照片管理 | 照片上传/浏览 | ⚠️ 需API |
| 横断面 | 截面数据 | ⚠️ 需API |
| 数据导入 | Excel导入 | ⚠️ 需API |
| 知识库 | AI问答 | ⚠️ 需API |

### 4.2 状态管理
- **用户状态**: Zustand (useUserStore)
- **应用状态**: Zustand (useAppStore)
- **API调用**: 原生fetch (简化版)

---

## 五、三维功能（当前实现）

### 5.1 已实现的3D组件

| 组件 | 文件 | 功能 | 状态 |
|------|------|------|------|
| **三维模型** | ModelPreviewSimple.tsx | 基础3D场景展示 | ✅ 可用 |
| **碰撞检测** | CollisionViewerSimple.tsx | 碰撞物体可视化 | ✅ 可用 |
| **施工调度** | Scheduler3DSimple.tsx | 时间轴施工进度 | ✅ 可用 |
| **路线三维** | Route3DSimple.tsx | 公路路线3D展示 | ✅ 可用 |

### 5.2 路线三维功能详情

**Route3DSimple.tsx 功能**:
- ✅ 25km高速公路路线可视化
- ✅ 桩点标记（起点/终点/桥梁/隧道/里程碑）
- ✅ 地形截面填充显示
- ✅ 标注显示/隐藏
- ✅ 高程缩放控制
- ✅ 桩点列表与详情
- ✅ 统计面板（总长、桥梁、隧道、高差）

### 5.3 技术实现

```typescript
// 技术栈
- React Three Fiber (@react-three/fiber)
- Drei (@react-three/drei) - 辅助组件
- Three.js - 3D引擎

// 核心组件
- Canvas - 3D画布
- OrbitControls - 轨道控制（旋转/缩放/平移）
- Line - 路线曲线
- Text - 3D文字标注
- Html - HTML覆盖层
```

---

## 六、问题与差距分析

### 6.1 严重问题 (阻断性)

| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| 1 | **前后端未连接** | 所有功能无法真正使用 | 启动后端API服务 |
| 2 | **数据库未初始化** | 无数据可展示 | 运行数据库迁移 |
| 3 | **演示数据缺失** | 3D展示为空 | 添加示例数据 |

### 6.2 功能缺失

| # | 模块 | 缺失内容 |
|---|------|----------|
| 1 | 项目管理 | 完整的CRUD逻辑 |
| 2 | 桩号管理 | Excel批量导入 |
| 3 | 照片管理 | 文件上传/存储 |
| 4 | 碰撞检测 | 真实碰撞算法 |
| 5 | 路线三维 | 与后端数据联动 |

### 6.3 技术债务

| # | 问题 | 文件 |
|---|------|------|
| 1 | 旧页面组件有TS错误 | pages/*.tsx (大量) |
| 2 | 旧3D组件编译失败 | components/three/*.tsx |
| 3 | API导入路径错误 | 多处 |
| 4 | 未使用的导入 | 大量文件 |

---

## 七、数据流分析

### 7.1 当前数据流

```
用户操作 → App.tsx (简化版)
         ↓
   本地状态 (useState)
         ↓
   不调用API (演示模式)
```

### 7.2 目标数据流

```
用户操作 → App.tsx
         ↓
   API调用 (stationsApi, routesApi...)
         ↓
   后端FastAPI
         ↓
   SQLAlchemy模型
         ↓
   PostgreSQL数据库
```

---

## 八、3D功能与数据结合方案

### 8.1 路线三维数据流

```python
# 后端返回的数据结构
Route {
    id: str
    name: str
    total_length: float
    points: List[Station]
}

Station {
    id: str
    station_number: float  # 桩号 km
    elevation: float       # 海拔 m
    coordinates: dict      # 经纬度
    type: str             # normal/bridge/tunnel
}
```

### 8.2 前端需要做的

1. **数据获取**: 调用 `routesApi.getRoutes()` 获取路线列表
2. **详情加载**: 调用 `routesApi.getRouteDetail(id)` 获取路线详情和桩点
3. **3D渲染**: 将桩点数据转换为3D坐标并渲染
4. **交互**: 点击桩点 → 显示详情面板

### 8.3 需要后端支持

| API | 用途 |
|-----|------|
| GET /api/v1/projects | 获取项目列表 |
| GET /api/v1/routes | 获取路线列表 |
| GET /api/v1/routes/{id} | 获取路线详情+桩点 |
| GET /api/v1/stations | 获取桩点列表 |
| GET /api/v1/cross-sections | 获取横断面数据 |

---

## 九、部署状态

### 9.1 当前运行状态

| 服务 | 状态 | 地址 |
|------|------|------|
| 前端开发服务器 | ⏹ 已停止 | localhost:3001 |
| 后端API | ⏹ 未运行 | - |
| PostgreSQL | ⏹ Docker中 | localhost:5432 |

### 9.2 启动步骤

```bash
# 1. 启动数据库 (Docker)
docker run -d --name neuralsite-postgres -e POSTGRES_PASSWORD=xxx postgres:15

# 2. 启动后端
cd packages/core
python main.py

# 3. 启动前端
cd packages/studio
npm run dev
```

---

## 十、总结与建议

### 10.1 当前状态
- ✅ 基础框架完整
- ✅ 前端3D可视化可用
- ⚠️ 前后端未连接
- ⚠️ 数据模型未填充

### 10.2 建议工作顺序

1. **第一阶段**: 连接后端API
   - 修复后端路由注册
   - 初始化数据库
   - 添加示例数据

2. **第二阶段**: 完善数据管理
   - 项目CRUD
   - 桩号管理
   - 照片上传

3. **第三阶段**: 3D功能增强
   - 路线三维数据联动
   - 横断面3D展示
   - 碰撞检测算法

### 10.3 优先级

| 优先级 | 内容 | 预计工作量 |
|--------|------|----------|
| P0 | 启动后端+数据库 | 2小时 |
| P0 | 连接前端API | 4小时 |
| P1 | 路线三维数据联动 | 4小时 |
| P1 | 桩号管理功能 | 8小时 |
| P2 | 碰撞检测算法 | 8小时 |
| P2 | 横断面3D | 8小时 |

---

*文档版本: 1.0*
*最后更新: 2026-03-05*
