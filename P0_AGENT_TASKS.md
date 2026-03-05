# NeuralSite P0 建设 - Agent任务分配方案

> 创建时间: 2026-03-05
> 负责人: Chen Leiyang
> 项目: NeuralSite P0 基础数据层建设

---

## 📋 任务概览

| Agent | 任务领域 | 优先级 | 状态 |
|-------|----------|--------|------|
| **Database-Agent** | PostgreSQL配置 + 迁移 | P0 | 待启动 |
| **API-Agent** | FastAPI接口实现 | P0 | 待启动 |
| **Mobile-Agent** | Flutter离线同步 | P0 | 待启动 |
| **Infra-Agent** | Docker + 部署配置 | P1 | 待启动 |
| **QA-Agent** | 单元测试 + 集成测试 | P2 | 待启动 |

---

## 🎯 Agent详细任务分配

### 1. Database-Agent (数据库工程)

**任务目标**: 完成PostgreSQL数据库配置和初始化

**工作内容**:
```
1. 创建 docker-compose.yml (PostgreSQL + Redis)
2. 创建 .env.example 配置模板
3. 验证迁移脚本可执行性
4. 创建数据库连接配置 (config.py)
5. 初始化测试数据
```

**交付物**:
- `docker-compose.yml`
- `.env.example`
- `packages/core/config.py`

**工作目录**: `C:\Users\Administrator\.openclaw\workspace\neuralsite\`

---

### 2. API-Agent (后端接口)

**任务目标**: 实现完整的P0 API接口

**工作内容**:
```
1. 实现数据库依赖注入 (database.py)
2. 实现用户认证 (JWT)
3. 实现照片上传/存储
4. 实现问题CRUD接口
5. 实现离线同步接口
6. 添加基本的错误处理
```

**交付物**:
- `packages/core/api/deps.py` - 数据库依赖
- `packages/core/api/auth.py` - 认证模块
- `packages/core/services/photo_service.py` - 照片服务
- `packages/core/services/issue_service.py` - 问题服务
- `packages/core/services/sync_service.py` - 同步服务

**工作目录**: `C:\Users\Administrator\.openclaw\workspace\neuralsite\packages\core\`

---

### 3. Mobile-Agent (移动端)

**任务目标**: 完成Flutter离线同步模块

**工作内容**:
```
1. 集成 offline_sync.dart 到Flutter项目
2. 实现照片拍摄+上传流程
3. 实现问题上报流程
4. 实现GPS自动桩号关联
5. 添加网络状态监听
```

**交付物**:
- `packages/mobile/lib/services/sync_service.dart`
- `packages/mobile/lib/screens/photo_capture_screen.dart`
- `packages/mobile/lib/screens/issue_report_screen.dart`
- `packages/mobile/lib/models/`

**工作目录**: `C:\Users\Administrator\.openclaw\workspace\neuralsite\packages\mobile\`

---

### 4. Infra-Agent (基础设施)

**任务目标**: 完成部署和运维配置

**工作内容**:
```
1. 创建 Dockerfile (后端)
2. 创建 Dockerfile (前端)
3. 创建 nginx.conf
4. 创建部署文档
5. 配置CI/CD (GitHub Actions)
```

**交付物**:
- `Dockerfile`
- `docker-compose.yml` (完整版)
- `.github/workflows/ci.yml`
- `DEPLOY.md`

**工作目录**: `C:\Users\Administrator\.openclaw\workspace\neuralsite\`

---

### 5. QA-Agent (质量保证)

**任务目标**: 确保代码质量和功能正确

**工作内容**:
```
1. 编写数据库迁移测试
2. 编写API单元测试
3. 编写API集成测试
4. 编写Flutter同步测试
5. 生成测试覆盖率报告
```

**交付物**:
- `packages/core/tests/test_p0_api.py`
- `packages/core/tests/test_database.py`
- `packages/mobile/test/sync_test.dart`
- `TEST_REPORT.md`

**工作目录**: `C:\Users\Administrator\.openclaw\workspace\neuralsite\`

---

## 🚀 执行顺序

```
第1轮 (并行):
├── Database-Agent    → PostgreSQL配置
├── API-Agent         → 骨架代码
└── Mobile-Agent      → Flutter集成

第2轮 (串行):
└── API-Agent         → 实现完整接口

第3轮 (并行):
├── Infra-Agent       → Docker部署
└── QA-Agent         → 测试编写

第4轮:
└── 集成测试 + 修复
```

---

## 📊 验收标准

| Agent | 验收条件 |
|-------|----------|
| Database-Agent | docker-compose up -d 成功启动 |
| API-Agent | 所有P0接口返回正确响应 |
| Mobile-Agent | 离线数据可正常同步 |
| Infra-Agent | docker-compose up 成功部署 |
| QA-Agent | 测试覆盖率 > 70% |

---

## 🔗 依赖关系

```
Database-Agent ──┐
                 ├──→ API-Agent ──┐
                                 ├──→ Integration
Mobile-Agent  ──┘                 │
                                 ←┘
                 Infra-Agent  ←┘
                      │
                      ↓
                 QA-Agent
```

---

*创建时间: 2026-03-05*
