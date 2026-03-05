# NeuralSite 数据录入与修改功能分析报告

生成时间: 2026-03-05
分析范围: 后端API、前端页面、数据库模型

---

## 1. 实体功能矩阵

### 1.1 后端API覆盖情况

| 实体 | Create | Read | Update | Delete | 备注 |
|------|--------|------|--------|--------|------|
| **User (用户)** | ✅ POST /auth/register | ✅ GET /users, /users/{id} | - | - | 仅注册和列表，无编辑/删除 |
| **Photo (照片)** | ✅ POST /photos/upload | ✅ GET /photos, /photos/{id} | ✅ PUT /photos/{id} | ❌ 缺失 | 有上传、查询、更新，无删除 |
| **Issue (问题)** | ✅ POST /issues | ✅ GET /issues, /issues/{id} | ✅ PUT /issues/{id} | ❌ 缺失 | 有CRUD+分配+解决，无删除 |
| **Project (项目)** | ❌ 缺失 | ❌ 缺失 | ❌ 缺失 | ❌ 缺失 | **严重缺失** - 无API |
| **Route (路线)** | ❌ 缺失 | ⚠️ GET /routes | ❌ 缺失 | ❌ 缺失 | 仅列出缓存中的路线 |
| **Station (桩号)** | ❌ 缺失 | ⚠️ GET /chainage/{station} | ❌ 缺失 | ❌ 缺失 | 仅查询，无录入 |
| **CrossSection (横断面)** | ❌ 缺失 | ❌ 缺失 | ❌ 缺失 | ❌ 缺失 | **严重缺失** |
| **Coordinate (坐标)** | ❌ 缺失 | ✅ GET /query/range, /lod/{level} | ❌ 缺失 | ❌ 缺失 | 仅查询，无录入 |

### 1.2 前端页面覆盖情况

| 页面 | 功能 | 状态 |
|------|------|------|
| LoginPage | 用户登录 | ✅ 完成 |
| DashboardPage | 统计概览 | ✅ 完成 |
| IssueListPage | 问题列表+筛选 | ✅ 完成 |
| PhotoListPage | 照片列表 | ✅ 完成 |
| CapturePage | 拍照采集 | ✅ 完成 |
| IssueCreatePage | 创建问题表单 | ❌ **缺失** |
| ProjectListPage | 项目列表 | ❌ **缺失** |
| ProjectEditPage | 项目编辑 | ❌ **缺失** |
| RouteListPage | 路线列表 | ❌ **缺失** |
| RouteEditPage | 路线编辑 | ❌ **缺失** |
| StationEntryPage | 桩号录入 | ❌ **缺失** |
| CrossSectionPage | 横断面录入 | ❌ **缺失** |

---

## 2. 数据录入功能缺失清单

### 2.1 核心功能缺失（按优先级）

| 优先级 | 功能模块 | 缺失项 | 影响 |
|--------|----------|--------|------|
| **P0** | 项目管理 | Project CRUD API + 前端页面 | 无法创建/管理项目 |
| **P0** | 路线管理 | Route CRUD API + 前端页面 | 无法创建/管理路线 |
| **P1** | 桩号数据录入 | Station 录入API + 前端表单 | 无法手动录入桩号数据 |
| **P1** | 横断面数据 | CrossSection 录入API + 前端表单 | 无法录入横断面数据 |
| **P1** | 坐标数据录入 | Coordinate 录入API + 前端表单 | 无法手动录入坐标 |
| **P2** | 照片删除 | DELETE /photos/{id} API | 无法删除照片记录 |
| **P2** | 问题删除 | DELETE /issues/{id} API | 无法删除问题记录 |
| **P2** | 问题创建表单 | IssueCreatePage | 只能列表查看，无法新建 |

### 2.2 数据模型现状

**已有模型 (packages/core/models/p0_models.py):**
- User, PhotoRecord, Issue, SyncQueue

**已有模型 (packages/core/storage/db/models.py):**
- Project, Route, RouteParameter, CalculationResult

**缺失模型:**
- Station (桩号)
- CrossSection (横断面)
- Coordinate (坐标) - 仅有计算结果缓存

---

## 3. 数据库模型对比

| 实体 | p0_models.py | storage/db/models.py | 差异 |
|------|---------------|---------------------|------|
| User | ✅ 完整 | - | PostgreSQL版本 |
| Photo | ✅ 完整 | - | PostgreSQL版本 |
| Issue | ✅ 完整 | - | PostgreSQL版本 |
| Project | - | ⚠️ 简化版 | SQLite版本，缺少P0扩展字段 |
| Route | - | ⚠️ 简化版 | SQLite版本 |
| Station | ❌ 缺失 | ❌ 缺失 | 无独立表 |
| CrossSection | ❌ 缺失 | ❌ 缺失 | 无独立表 |

**数据库迁移脚本 (001_p0_baseline.sql):**
- 创建了 users, photo_records, issues, sync_queue 表
- 尝试添加 projects 字段但表可能不存在

---

## 4. 改进方案优先级

### 第一阶段：项目管理（P0）

1. **创建 Project API**
   - POST /api/v1/projects - 创建项目
   - GET /api/v1/projects - 列表查询
   - GET /api/v1/projects/{id} - 详情
   - PUT /api/v1/projects/{id} - 编辑
   - DELETE /api/v1/projects/{id} - 删除

2. **创建 Project 前端页面**
   - ProjectListPage - 项目列表
   - ProjectFormPage - 项目创建/编辑表单

### 第二阶段：路线管理（P0）

3. **创建 Route API**
   - POST /api/v1/routes - 创建路线
   - GET /api/v1/routes - 列表查询
   - GET /apiid} - /v1/routes/{详情
   - PUT /api/v1/routes/{id} - 编辑
   - DELETE /api/v1/routes/{id} - 删除

4. **创建 Route 前端页面**
   - RouteListPage - 路线列表
   - RouteFormPage - 路线创建/编辑表单

### 第三阶段：数据录入（P1）

5. **桩号数据录入**
   - Station 数据模型
   - Station 录入/查询 API
   - StationEntryPage 前端表单

6. **横断面数据录入**
   - CrossSection 数据模型
   - CrossSection 录入/查询 API
   - CrossSectionPage 前端表单

7. **坐标数据录入**
   - Coordinate 录入 API
   - CoordinateEntryPage 前端表单

### 第四阶段：功能完善（P2）

8. **删除功能**
   - DELETE /photos/{id}
   - DELETE /issues/{id}

9. **问题创建表单**
   - IssueCreatePage

---

## 5. 总结

| 分类 | 完成度 | 缺失严重性 |
|------|--------|-----------|
| 用户管理 | 80% | 低 |
| 照片管理 | 75% | 中 |
| 问题管理 | 70% | 中 |
| **项目管理** | **0%** | **严重** |
| **路线管理** | **10%** | **严重** |
| **桩号数据** | **5%** | **严重** |
| **横断面数据** | **0%** | **严重** |
| 坐标数据 | 30% | 高 |

**核心结论：** 项目最核心的"数据录入"功能中，**项目管理**和**路线管理**完全缺失API和前端页面，**桩号数据**和**横断面数据**录入功能也严重缺失。这些是必须优先实现的基础功能。
