# NeuralSite P0 基础数据层 - 实施进度

> 创建时间: 2026-03-05
> 优先级: P0 (照片管理 + 问题跟踪 + 离线同步)
> 对应整改建议书版本: V1.0

---

## 📁 目录结构

```
neuralsite/
├── packages/
│   ├── core/
│   │   ├── api/v1/
│   │   │   └── p0_routes.py          # ✅ P0 API路由
│   │   ├── database/
│   │   │   └── migrations/
│   │   │       └── 001_p0_baseline.sql  # ✅ 数据库迁移脚本
│   │   └── models/
│   │       └── p0_models.py         # ✅ 数据模型
│   │
│   └── mobile/
│       └── sync/
│           └── offline_sync.dart    # ✅ 离线同步模块
│
├── docker-compose.yml                # 待添加
├── .env.example                      # 待添加
└── README.md
```

---

## ✅ 已完成

### 1. 数据库层 (PostgreSQL)

**迁移脚本**: `packages/core/database/migrations/001_p0_baseline.sql`

| 表名 | 功能 | 状态 |
|------|------|------|
| users | 用户与权限 | ✅ |
| photo_records | 照片记录 | ✅ |
| issues | 问题跟踪 | ✅ |
| sync_queue | 同步队列 | ✅ |

### 2. API层 (FastAPI)

**路由文件**: `packages/core/api/v1/p0_routes.py`

| 接口组 | 状态 |
|--------|------|
| `/api/v1/auth/*` - 认证 | ✅ 骨架 |
| `/api/v1/users/*` - 用户管理 | ✅ 骨架 |
| `/api/v1/photos/*` - 照片管理 | ✅ 骨架 |
| `/api/v1/issues/*` - 问题跟踪 | ✅ 骨架 |
| `/api/v1/sync/*` - 离线同步 | ✅ 骨架 |
| `/api/v1/dashboard/*` - 仪表盘 | ✅ 骨架 |

### 3. 移动端 (Flutter)

**同步模块**: `packages/core/mobile/sync/offline_sync.dart`

| 模块 | 功能 | 状态 |
|------|------|------|
| LocalDatabase | SQLite本地存储 | ✅ |
| PhotoRecord | 照片数据模型 | ✅ |
| IssueRecord | 问题数据模型 | ✅ |
| OfflineSyncManager | 同步管理器 | ✅ |

---

## ⏳ 待完成

### 4. 数据库配置

- [ ] 创建 `docker-compose.yml` (PostgreSQL + Redis)
- [ ] 创建 `.env.example` 配置模板
- [ ] 创建 `config.py` 配置加载逻辑

### 5. API实现

- [ ] 实现 `database.py` 依赖注入
- [ ] 实现用户认证 (JWT)
- [ ] 实现文件上传到本地存储/MinIO
- [ ] 实现照片的GPS信息提取
- [ ] 集成AI分类模型

### 6. 测试

- [ ] 单元测试 (pytest)
- [ ] API集成测试
- [ ] 离线同步测试

### 7. 部署

- [ ] Docker镜像构建
- [ ] CI/CD配置

---

## 🚀 快速开始

### 启动PostgreSQL

```bash
docker-compose up -d postgres
```

### 运行迁移

```bash
psql -h localhost -U neuralsite -d neuralsite -f packages/core/database/migrations/001_p0_baseline.sql
```

### 启动API

```bash
cd packages/core
pip install -r requirements.txt
uvicorn api.main:app --reload
```

---

## 📋 数据库字段说明

### photo_records (照片记录)

| 字段 | 类型 | 说明 |
|------|------|------|
| photo_id | UUID | 主键 |
| project_id | UUID | 项目ID |
| file_path | VARCHAR(500) | 文件路径 |
| latitude/longitude | DECIMAL | GPS坐标 |
| station | DECIMAL(18,4) | 桩号 |
| ai_classification | JSONB | AI分类结果 |
| is_verified | BOOLEAN | 人工确认 |
| sync_status | VARCHAR(20) | 同步状态 |

### issues (问题记录)

| 字段 | 类型 | 说明 |
|------|------|------|
| issue_id | UUID | 主键 |
| issue_type | VARCHAR(50) | 问题类型 |
| severity | VARCHAR(20) | 严重程度 |
| status | VARCHAR(20) | 状态流转 |
| ai_screening | JSONB | AI初筛结果 |
| photo_ids | JSONB | 关联照片 |

---

## 🔄 离线同步流程

```
移动端                              服务器
  │                                   │
  │  1. 采集数据 (照片/问题)           │
  │  2. 保存到本地SQLite              │
  │  3. 加入同步队列                  │
  │                                   │
  │  ─────── 检测到网络可用 ───────   │
  │                                   │
  │  POST /api/v1/sync/push          │
  │  ──────── 处理响应 ────────       │
  │     │                             │
  │     ├── synced: 更新本地状态       │
  │     ├── conflicts: 冲突处理        │
  │     └── failed: 重试队列           │
  │                                   │
  │  GET /api/v1/sync/pull            │
  │  ──────── 拉取最新 ────────       │
  │     │                             │
  │     └── 保存到本地                │
```

---

## ⚠️ 注意事项

1. **密码存储**: 使用bcrypt哈希，不存储明文
2. **文件存储**: 生产环境建议使用MinIO或云OSS
3. **离线优先**: 所有数据操作先写本地，联网后同步
4. **冲突策略**: 当前实现为"服务器优先"，可配置
5. **AI分类**: 需要集成图像分类/目标检测模型

---

*最后更新: 2026-03-05*
