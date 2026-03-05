# NeuralSite 项目修复计划

## 问题概述

| 问题 | 现状 | 影响 |
|------|------|------|
| 全局状态 | `api/v1/routes/calculate.py` 存在 `_engines = {}` | 多实例部署失败、状态不可预测 |
| 硬编码 | 样本数据直接写在代码中 | 无法配置、难以测试 |
| 无依赖注入 | API层未使用 FastAPI Depends | 难以mock、单元测试困难 |
| 无Feature Flag | 缺少特性开关系统 | 新功能无法灰度发布 |

---

## P0 阶段：架构修复（1-2周）

### Week 1：基础设施重构

#### Day 1-2：消除全局状态
**任务**: 重构 `api/v1/routes/calculate.py`
- [ ] 移除 `_engines = {}` 全局变量
- [ ] 创建 EngineManager 类，使用单例模式或工厂模式
- [ ] 实现 Engine 生命周期管理（init/shutdown）

**验收标准**:
```python
# 正确示例
@app.get("/calculate")
async def calculate(
    engine: Engine = Depends(get_engine),
    params: CalculateParams = Depends(get_params)
):
    return await engine.compute(params)
```

#### Day 3-4：依赖注入改造
**任务**: 全面使用 FastAPI Depends
- [ ] 创建 `api/dependencies.py`
  - `get_db()` - 数据库连接
  - `get_redis()` - Redis 缓存
  - `get_engine_manager()` - 引擎管理器
  - `get_feature_flags()` - 特性开关
- [ ] 重构所有 API 路由使用 Depends

**代码示例**:
```python
# api/dependencies.py
from functools import lru_cache

@lru_cache()
def get_settings():
    return Settings()

async def get_engine_manager():
    settings = get_settings()
    return EngineManager(settings.engine_config)

# api/v1/routes/calculate.py
@router.post("/calculate")
async def calculate(
    params: CalculateParams,
    engine: Engine = Depends(get_engine_manager)
):
    return await engine.compute(params)
```

#### Day 5：Feature Flag 系统
**任务**: 实现特性开关系统
- [ ] 创建 `core/feature_flags.py`
- [ ] 支持存储：Redis / 数据库 / 环境变量
- [ ] 实现分层开关（global → user → session）

**实现方案**:
```python
# core/feature_flags.py
class FeatureFlags:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def is_enabled(self, flag: str, context: dict = None) -> bool:
        # 支持百分比灰度、用户分组、开关状态
        ...
    
    @property
    def spatial_v2(self) -> bool:
        return self.is_enabled("spatial_engine_v2")
    
    @property
    def knowledge_graph_enhanced(self) -> bool:
        return self.is_enabled("kg_enhanced")
```

---

### Week 2：数据层与配置重构

#### Day 6-7：消除硬编码
**任务**: 外化所有配置和样本数据
- [ ] 创建 `config/` 目录结构
  ```
  config/
  ├── defaults.yaml      # 默认配置
  ├── sample_data/       # 样本数据
  │   ├── routes.yaml    # 路线样本
  │   ├── points.yaml    # 桩号样本
  │   └── materials.yaml # 材料样本
  └── environments/      # 环境配置
      ├── dev.yaml
      ├── staging.yaml
      └── prod.yaml
  ```
- [ ] 创建配置加载器 `core/config.py`
- [ ] 迁移所有硬编码数据到配置文件

#### Day 8-9：测试基础设施
**任务**: 建立单元测试和集成测试
- [ ] 配置 pytest + pytest-asyncio
- [ ] 创建 `tests/conftest.py` 定义 fixtures
- [ ] 为 EngineManager 编写 Mock 测试

**测试示例**:
```python
# tests/test_engine.py
@pytest.fixture
def mock_engine():
    with patch('api.dependencies.get_engine_manager') as mock:
        yield mock.return_value

def test_calculate_with_injection(engine, mock_engine):
    # 测试依赖注入工作正常
    ...
```

#### Day 10：文档与验收
- [ ] 更新 ARCHITECTURE.md 纳入新规范
- [ ] 编写 P0 阶段技术债务清单
- [ ] 全员代码审查

---

## P1 阶段：核心模块完善（2-4周）

### core/spatial 完善

| 任务 | 工期 | 依赖 |
|------|------|------|
| 桩号范围查询 API | 3天 | P0完成 |
| 最近桩号查询 | 2天 | P0完成 |
| 空间索引优化 (R-Tree) | 3天 | PostGIS |
| LOD 批量计算 | 2天 | Redis |

### core/knowledge_graph 开发

| 任务 | 工期 | 依赖 |
|------|------|------|
| Neo4j 实体定义 | 2天 | Neo4j |
| 关系构建 API | 3天 | 实体定义 |
| 图查询 DSL | 3天 | 关系API |
| 路径推理引擎 | 4天 | 图查询 |

---

## MVP 阶段：空间数据引擎（4-8周）

### 里程碑 1：空间数据引擎 v1.0（Week 5-6）

#### 核心功能
```
spatial_engine/
├── core/
│   ├── route.py          # 路线模型（平竖横曲线）
│   ├── station.py        # 桩号系统
│   └── geometry.py       # 几何计算（继承 core/geometry）
├── engine/
│   ├── query_engine.py   # 查询引擎
│   ├── spatial_index.py  # 空间索引
│   └── cache.py          # 缓存层
└── api/
    ├── routes.py         # FastAPI 路由
    └── schemas.py        # Pydantic 模型
```

#### API 设计
```python
# 路线查询
POST /api/v1/spatial/route/query
{
    "route_name": "G4京港澳高速",
    "start_station": "K100+000",
    "end_station": "K150+000"
}

# 最近桩号查询
POST /api/v1/spatial/nearest
{
    "latitude": 39.9042,
    "longitude": 116.4074,
    "route_ids": ["route_001", "route_002"]
}

# 批量坐标转换
POST /api/v1/spatial/batch-transform
{
    "transformations": [
        {"from": "wgs84", "to": "cgcs2000", "points": [...]}
    ]
}
```

### 里程碑 2：知识图谱集成（Week 7-8）

#### 图谱增强
```
knowledge_graph/
├── models/
│   ├── entities.py       # 实体定义（路线、桥梁、隧道）
│   └── relations.py      # 关系定义
├── queries/
│   ├── cypher_builder.py # 查询构建器
│   └── path_finder.py    # 路径推理
└── services/
    ├── kg_service.py     # 图谱服务
    └── reasoning.py      # 推理引擎
```

#### 智能问答 API
```python
# 基于图的智能查询
POST /api/v1/kg/query
{
    "question": "K100+000 到 K150+000 之间有哪些桥梁？",
    "include_reasoning": true
}
```

---

## 人力资源需求

### 核心团队（3-5人）

| 角色 | 人数 | 职责 |
|------|------|------|
| 后端工程师 | 2人 | API重构、引擎开发 |
| 架构师 | 1人 | 技术方案设计、代码审查 |
| 前端工程师 | 1人 | 可视化对接 |
| 全栈/测试 | 1人 | 测试、CI/CD |

### 外部依赖

| 依赖 | 用途 | 获取方式 |
|------|------|----------|
| Neo4j 专家 | 图谱优化 | 咨询 |
| GIS 专家 | 坐标转换验证 | 咨询 |
| DevOps | 容器化部署 | 内部/外包 |

---

## 依赖关系图

```
P0 阶段（1-2周）
├── 消除全局状态
│   └── 依赖：无
├── 依赖注入改造
│   └── 依赖：消除全局状态
├── Feature Flag系统
│   └── 依赖：依赖注入
└── 消除硬编码
    └── 依赖：无

P1 阶段（2-4周）
├── core/spatial 完善
│   └── 依赖：P0完成
└── core/knowledge_graph 开发
    └── 依赖：P0完成

MVP阶段（4-8周）
├── 空间数据引擎 v1.0
│   └── 依赖：P1完成
└── 知识图谱集成
    └── 依赖：P1完成
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 依赖注入改造破坏现有功能 | 高 | 充分单元测试 + 灰度发布 |
| 性能回退 | 中 | 建立性能基准测试 |
| Neo4j 查询性能 | 中 | 提前进行数据量级评估 |
| 人力不足 | 高 | 优先P0，确保基础设施稳固 |

---

## 验收标准

### P0 完成条件
- [ ] 所有 API 使用依赖注入，无全局状态
- [ ] Feature Flag 可动态控制新功能
- [ ] 所有配置外化到配置文件
- [ ] 单元测试覆盖 > 80%

### MVP 完成条件
- [ ] 空间查询 API 响应时间 < 100ms
- [ ] 支持百万级桩号数据查询
- [ ] 知识图谱支持基本推理
- [ ] 端到端集成测试通过
