# NeuralSite 开发计划

## 当前状态 (2026-03-04)

### ✅ 已完成

| 模块 | 功能 | 状态 |
|------|------|------|
| **Docker** | Neo4j + API + Web | ✅ 可用 |
| **Core** | 几何计算引擎 (平竖横曲线) | ✅ 可用 |
| **Core** | 知识图谱 API (Neo4j) | ✅ 可用 |
| **Core** | 工程智能 API (施工推荐/碰撞检测/BIM导出) | ✅ 可用 |
| **Studio** | Three.js 三维可视化 | ✅ 可用 |
| **Mobile** | Flutter 基础 + 离线同步 | ✅ 可用 |

### 🔄 本次完善

- [x] Docker 添加 PostgreSQL + PostGIS + Redis
- [x] 添加 .env.example 配置模板
- [x] 添加 connectivity_plus 依赖

---

## 后续开发任务

### P0 - 基础设施

- [ ] 创建 PostgreSQL 数据库初始化脚本
- [ ] 配置 Redis 缓存层
- [ ] 添加环境变量加载逻辑

### P1 - 核心功能

- [ ] 完善空间数据 API (桩号范围查询、最近桩号查询)
- [ ] 完善照片数据 API (上传、分类、AI检测)
- [ ] 实现 LOD 批量计算优化

### P2 - 前端

- [ ] 完善参数面板 (路线参数输入)
- [ ] 添加数据导入功能 (Excel)
- [ ] 完善三维交互 (点击查看详情)

### P3 - 移动端

- [ ] 完善拍照上报功能
- [ ] 实现 GPS 自动桩号关联
- [ ] 添加问题跟踪列表

### P4 - AI 能力 (可选)

- [ ] 集成图像分类模型 (施工状态)
- [ ] 集成目标检测模型 (裂缝、破损)
- [ ] 实现反馈优化闭环

---

## 快速开始

### 本地开发

```bash
# 1. 启动基础设施
docker-compose up -d postgres redis neo4j

# 2. 启动后端
cd packages/core
pip install -r requirements.txt
python -m uvicorn api.main:app --reload

# 3. 启动前端
cd packages/studio
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

---

## 技术栈版本

- Python: 3.10+
- Node.js: 18+
- Flutter: 3.0+
- PostgreSQL: 15 + PostGIS 3.3
- Neo4j: 5
- Redis: 7
