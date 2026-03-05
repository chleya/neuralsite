---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: 93f1a3419d1cb2c97b56cd84145862d2
    PropagateID: 93f1a3419d1cb2c97b56cd84145862d2
    ReservedCode1: 3046022100ad3df4b0734e3d76b4f60507904af18696b7c1b288f05cc9c8985a27b3fc6eaf022100f5aef788982766a605bbb5e121adb0a5651da0452a0d0f86d1bf771a8385f3a0
    ReservedCode2: 3045022100c15fbffd66a436d983aca73dc25e3f9c0b6599142af6b5fb478074877fcf38f802200e6f3438b5d8a65a46356e4400512140fcd47c65cce9938565c0259ad41fb6f2
---

# NeuralSite智网六维时空系统技术详细规格说明书

## 一、技术架构总览

### 1.1 系统分层架构

NeuralSite智网系统采用清晰的分层架构设计，遵循“core（纯几何+业务逻辑）→studio（可视化）→mobile（移动端桥接）”的核心原则。这一架构源自GitHub项目的最佳实践，经过真实项目验证，能够有效分离关注点，降低模块间的耦合度，提高系统的可维护性和可扩展性。

**核心层（core）**。核心层封装了系统的所有业务逻辑，是系统的“心脏”。核心层包含以下模块：空间计算引擎，负责桩号与坐标的相互转换、平竖横曲线计算、三维坐标变换；数据处理引擎，负责图纸解析、数据清洗、数据校验；AI推理引擎，负责图像分类、目标检测、语义理解；知识图谱引擎，负责知识存储、知识查询、知识推理。核心层完全使用Python开发，利用其丰富的科学计算和机器学习生态。核心层不包含任何UI代码，可以完全脱离前端和移动端独立运行。

**可视层（studio）**。可视层负责数据的图形化展示，是系统的“面子”。可视层包含以下组件：Web管理后台，采用React框架开发，提供完整的管理功能；三维可视化组件，采用Three.js开发，在浏览器中渲染工程三维模型；图表统计组件，采用ECharts开发，绘制各类数据可视化图表。可视层通过API与核心层通信，不直接访问数据库。

**移动层（mobile）**。移动层面向工地现场的移动端用户，是系统的“手脚”。移动层采用Flutter开发，一套代码同时支持iOS和Android。移动层的设计原则是“离线优先”——在无网络环境下依然可以使用核心功能，联网后自动同步数据。移动端通过RESTful API与核心层通信，同时内置本地数据库用于离线存储。

**集成层（infrastructure）**。集成层负责系统的部署和运维。采用Docker容器化部署，简化环境配置；采用Nginx作为反向代理和静态资源服务；采用Celery作为任务队列，处理耗时异步任务；采用Redis作为缓存层，提升系统性能。

### 1.2 技术栈选型

| 层级 | 技术选型 | 选型理由 |
|------|----------|----------|
| 后端核心 | Python 3.10+ | 丰富的科学计算和机器学习生态 |
| Web框架 | FastAPI | 高性能、支持异步、自动生成API文档 |
| 空间数据库 | PostGIS | 最成熟的开源空间数据库 |
| 知识图谱 | Neo4j | 强大的图查询能力、适合复杂关系 |
| 业务数据库 | PostgreSQL | 可靠的关系型数据库 |
| 缓存 | Redis | 高性能、支持多种数据结构 |
| 任务队列 | Celery | Python生态最成熟的异步任务框架 |
| 前端框架 | React 18 | 组件化、生态丰富 |
| 三维渲染 | Three.js | WebGL事实标准 |
| 图表库 | ECharts | 功能强大、性能好 |
| 移动开发 | Flutter | 跨平台、性能好 |
| 状态管理 | Riverpod | Flutter官方推荐 |
| 容器化 | Docker + docker-compose | 简化部署、环境一致 |

### 1.3 部署架构

系统采用分布式部署架构，根据不同规模的业务需求，可以灵活扩展。基础部署采用单机模式，所有服务部署在一台服务器上，适合中小型项目。标准部署采用主从模式，数据库单独部署，Web服务和AI服务分开部署，适合大型项目。高可用部署采用集群模式，多个Web服务实例负载均衡，数据库主从复制，适合省级重点示范项目。

所有服务通过Docker容器化部署，docker-compose编排文件定义了服务启动顺序和依赖关系。部署包包含完整的运行环境，开发人员 clone 代码后只需执行docker-compose up即可启动系统。

## 二、数据库设计

### 2.1 数据库整体架构

系统采用多数据库混合存储架构，不同类型的数据存储在最适合的数据库中。PostGIS存储空间数据，包括桩号、坐标、里程等；Neo4j存储知识图谱数据，包括实体、关系、属性；PostgreSQL存储业务数据，包括用户、权限、配置等；Redis存储缓存数据和会话数据。

数据库设计遵循以下原则：所有表必须有主键，禁止使用物理删除（使用软删除标志位）；所有时间字段使用UTC时间存储，显示时转换为本地时间；所有数值型字段根据精度要求选择合适的类型；所有外键必须建立索引。

### 2.2 核心表结构设计

**空间数据相关表**

```sql
-- 坐标参考系统表
CREATE TABLE coordinate_reference_system (
    crs_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crs_code VARCHAR(50) NOT NULL UNIQUE,
    crs_name VARCHAR(200) NOT NULL,
    crs_type VARCHAR(20) NOT NULL CHECK (crs_type IN ('geographic', 'projected', 'local')),
    projection_method VARCHAR(50),
    central_meridian DECIMAL(12, 6),
    false_easting DECIMAL(18, 6),
    false_northing DECIMAL(18, 6),
    scale_factor DECIMAL(18, 10),
    datum_id UUID REFERENCES coordinate_reference_system(crs_id),
    vertical_datum VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 里程桩号系统表
CREATE TABLE station_system (
    system_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name VARCHAR(200) NOT NULL,
    start_station VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('forward', 'backward')),
    interval INTEGER DEFAULT 100,
    coordinate_system_id UUID REFERENCES coordinate_reference_system(crs_id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 里程-坐标映射表
CREATE TABLE station_coordinate_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_system_id UUID REFERENCES station_system(system_id),
    station DECIMAL(18, 4) NOT NULL,
    station_display VARCHAR(20) NOT NULL,
    coordinate_system_id UUID REFERENCES coordinate_reference_system(crs_id),
    easting DECIMAL(18, 6) NOT NULL,
    northing DECIMAL(18, 6) NOT NULL,
    elevation DECIMAL(12, 4),
    design_elevation DECIMAL(12, 4),
    latitude DECIMAL(12, 8),
    longitude DECIMAL(13, 8),
    azimuth DECIMAL(12, 6),
    curve_type VARCHAR(20),
    curve_parameter JSONB,
    remark TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(station_system_id, station)
);

CREATE INDEX idx_station_coordinate_station ON station_coordinate_mapping(station);
CREATE INDEX idx_station_coordinate_spatial ON station_coordinate_mapping USING GIST(
    ST_MakePoint(easting, northing)
);

-- 道路段落表
CREATE TABLE road_section (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    section_name VARCHAR(200) NOT NULL,
    start_station DECIMAL(18, 4) NOT NULL,
    end_station DECIMAL(18, 4) NOT NULL,
    start_station_display VARCHAR(20) NOT NULL,
    end_station_display VARCHAR(20) NOT NULL,
    length DECIMAL(12, 4) NOT NULL,
    road_type VARCHAR(50),
    lane_count INTEGER,
    width DECIMAL(8, 2),
    speed_limit INTEGER,
    construction_status VARCHAR(20) DEFAULT 'not_started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_road_section_project ON road_section(project_id);
CREATE INDEX idx_road_section_station ON road_section USING BTREE(start_station, end_station);
```

**工程实体相关表**

```sql
-- 工程实体表
CREATE TABLE engineering_entity (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(200) NOT NULL,
    entity_code VARCHAR(100),
    start_station DECIMAL(18, 4),
    end_station DECIMAL(18, 4),
    station_display VARCHAR(50),
    geometry_data JSONB,
    design_parameters JSONB,
    construction_status VARCHAR(20) DEFAULT 'not_started',
    parent_entity_id UUID REFERENCES engineering_entity(entity_id),
    source_drawing_id UUID,
    source_drawing_page INTEGER,
    version_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_project ON engineering_entity(project_id);
CREATE INDEX idx_entity_type ON engineering_entity(entity_type);
CREATE INDEX idx_entity_station ON engineering_entity USING BTREE(start_station, end_station);
CREATE INDEX idx_entity_location ON engineering_entity USING GIST(
    ST_MakePoint(
        (geometry_data->>'easting')::DECIMAL,
        (geometry_data->>'northing')::DECIMAL
    )
);

-- 路面结构层表
CREATE TABLE pavement_layer (
    layer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entity(entity_id),
    layer_name VARCHAR(100) NOT NULL,
    layer_type VARCHAR(50) NOT NULL,
    layer_order INTEGER NOT NULL,
    thickness DECIMAL(8, 4) NOT NULL,
    material_code VARCHAR(50),
    material_name VARCHAR(200),
    construction_standard VARCHAR(200),
    mix_ratio JSONB,
    remark TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 桥梁表
CREATE TABLE bridge (
    bridge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entity(entity_id),
    bridge_name VARCHAR(200) NOT NULL,
    location VARCHAR(50),
    total_length DECIMAL(12, 4),
    total_width DECIMAL(8, 2),
    span_configuration VARCHAR(50),
    span_count INTEGER,
    single_span_length DECIMAL(8, 2),
    bridge_type VARCHAR(100),
    design_load VARCHAR(50),
    construction_method VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 桥梁构件表
CREATE TABLE bridge_component (
    component_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bridge_id UUID REFERENCES bridge(bridge_id),
    component_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(200) NOT NULL,
    component_code VARCHAR(100),
    quantity INTEGER,
    dimensions JSONB,
    material JSONB,
    reinforcement JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**照片数据相关表**

```sql
-- 照片记录表
CREATE TABLE photo_record (
    photo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    captured_by UUID REFERENCES users(user_id),
    latitude DECIMAL(12, 8),
    longitude DECIMAL(13, 8),
    altitude DECIMAL(12, 4),
    gps_accuracy DECIMAL(8, 2),
    station DECIMAL(18, 4),
    station_display VARCHAR(20),
    entity_id UUID REFERENCES engineering_entity(entity_id),
    photo_type VARCHAR(50) NOT NULL,
    ai_classification JSONB,
    ai_detection JSONB,
    tags JSONB,
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_photo_project ON photo_record(project_id);
CREATE INDEX idx_photo_station ON photo_record(station);
CREATE INDEX idx_photo_entity ON photo_record(entity_id);
CREATE INDEX idx_photo_type ON photo_record(photo_type);
CREATE INDEX idx_photo_captured_at ON photo_record(captured_at);
CREATE INDEX idx_photo_location ON photo_record USING GIST(
    ST_MakePoint(longitude, latitude)
);

-- 照片问题记录表
CREATE TABLE photo_issue (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID REFERENCES photo_record(photo_id),
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    location_in_photo JSONB,
    ai_confidence DECIMAL(5, 4),
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmed_by UUID,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    resolution_status VARCHAR(20) DEFAULT 'open',
    resolved_by UUID,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**数据版本相关表**

```sql
-- 数据版本表
CREATE TABLE data_version (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    version_type VARCHAR(20) NOT NULL CHECK (version_type IN ('initial', 'revision', 'amendment')),
    change_summary TEXT,
    change_detail JSONB,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    UNIQUE(project_id, version_number)
);

-- 数据血缘表
CREATE TABLE data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_id UUID NOT NULL,
    data_field VARCHAR(100),
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(200),
    source_detail JSONB,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    extracted_by VARCHAR(100),
    confidence DECIMAL(5, 4) DEFAULT 1.0,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- 数据校验错误日志表
CREATE TABLE validation_error_log (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    drawing_id UUID,
    entity_id UUID,
    entity_type VARCHAR(50),
    error_level VARCHAR(20) NOT NULL CHECK (error_level IN ('fatal', 'error', 'warning', 'info')),
    error_code VARCHAR(20) NOT NULL,
    error_type VARCHAR(30) NOT NULL,
    error_message TEXT NOT NULL,
    field_name VARCHAR(100),
    field_value TEXT,
    expected_value TEXT,
    validation_rule_id UUID,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT
);
```

**用户权限相关表**

```sql
-- 用户表
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    real_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    role_id UUID REFERENCES user_role(role_id),
    project_id UUID,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 角色表
CREATE TABLE user_role (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE operation_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    user_id UUID REFERENCES users(user_id),
    operation_type VARCHAR(30) NOT NULL,
    data_type VARCHAR(50),
    data_id UUID,
    ip_address INET,
    operation_detail JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operation_log_user ON operation_log(user_id);
CREATE INDEX idx_operation_log_created_at ON operation_log(created_at);
```

### 2.3 知识图谱模型

Neo4j知识图谱存储道路工程领域的专业知识，采用“实体-关系-实体”的三元组模型。

**节点类型**

```cypher
// 规范条款节点
CREATE (n:Standard {
    code: 'JTG F40-2004',
    name: '公路沥青路面施工技术规范',
    category: '路面施工',
    content: '...'
})

// 施工工艺节点
CREATE (n:Process {
    code: 'PRC-STRETCH',
    name: '摊铺',
    category: '路面施工',
    key_points: '...',
    quality_requirements: '...'
})

// 材料节点
CREATE (n:Material {
    code: 'MAT-AC13',
    name: 'AC-13细粒式沥青混凝土',
    category: '沥青混合料',
    properties: '...'
})

// 质量标准节点
CREATE (n:QualityStandard {
    name: '压实度',
    unit: '%',
    requirement: '≥96',
    test_method: '核子密度仪法'
})
```

**关系类型**

```cypher
// 规范约束工艺
MATCH (s:Standard {code: 'JTG F40-2004'})
MATCH (p:Process {code: 'PRC-STRETCH'})
CREATE (s)-[:CONSTRAINS]->(p)

// 工艺需要材料
MATCH (p:Process {code: 'PRC-STRETCH'})
MATCH (m:Material {code: 'MAT-AC13'})
CREATE (p)-[:REQUIRES {specification: '...'}]->(m)

// 工艺达到质量标准
MATCH (p:Process {code: 'PRC-COMPACT'})
MATCH (q:QualityStandard {name: '压实度'})
CREATE (p)-[:ACHIEVES {target: '≥96'}]->(q)
```

## 三、API接口设计

### 3.1 API设计规范

系统所有API遵循RESTful设计规范，使用JSON格式进行数据交换。URL采用名词复数形式，如/photos、/entities、/stations；HTTP方法表示操作类型，GET表示查询、POST表示创建、PUT表示更新、DELETE表示删除；响应格式统一，包含code、message、data、meta四个字段。

分页查询采用标准分页参数：page表示页码（从1开始）、page_size表示每页数量；排序采用sort参数，格式为field:desc或field:asc；过滤采用filter参数，JSON格式。认证采用Bearer Token方式，在请求头中携带Authorization: Bearer {token}。

### 3.2 核心API接口

**空间数据接口**

```yaml
# 获取指定桩号的坐标信息
GET /api/v1/stations/{station}/coordinates
Parameters:
  - station: 桩号（支持K5+800或5600.000格式）
  - station_system_id: 桩号系统ID（可选）
Response:
{
  "code": 200,
  "data": {
    "station": "K5+800",
    "station_numeric": 5800.0,
    "coordinate_system": "CGCS2000 / 3-degree Gauss-Kruger CM 117E",
    "coordinates": {
      "easting": 39567834.567,
      "northing": 3456789.012,
      "elevation": 123.456
    },
    "design_parameters": {
      "direction": "NE",
      "azimuth": 45.6789,
      "curve_type": "circular",
      "radius": 1500.0
    }
  }
}

# 按桩号范围查询坐标序列
GET /api/v1/stations/range/coordinates
Parameters:
  - start_station: 起始桩号
  - end_station: 终止桩号
  - interval: 插值间隔（米），默认20
Response:
{
  "code": 200,
  "data": {
    "station_system": "K系列桩号",
    "start_station": "K5+600",
    "end_station": "K6+200",
    "total_points": 31,
    "coordinates": [
      {
        "station": "K5+600",
        "easting": 39567500.123,
        "northing": 3456500.456,
        "elevation": 120.234
      },
      ...
    ]
  }
}

# 查询指定位置的最近桩号
GET /api/v1/stations/nearest
Parameters:
  - easting: 东坐标
  - northing: 北坐标
  - max_distance: 最大搜索距离（米），默认100
Response:
{
  "code": 200,
  "data": {
    "station": "K5+800",
    "distance": 2.5,
    "lateral_distance": 1.2,
    "easting": 39567834.567,
    "northing": 3456789.012
  }
}
```

**工程实体接口**

```yaml
# 查询指定桩号范围的实体
GET /api/v1/entities
Parameters:
  - project_id: 项目ID
  - entity_type: 实体类型（如pavement、bridge）
  - start_station: 起始桩号
  - end_station: 终止桩号
  - page: 页码
  - page_size: 每页数量
Response:
{
  "code": 200,
  "data": {
    "items": [
      {
        "entity_id": "uuid",
        "entity_type": "pavement",
        "entity_name": "K5+600-K6+200路面结构",
        "station_range": "K5+600 - K6+200",
        "layers": [
          {
            "layer_name": "上面层",
            "thickness": 0.04,
            "material": "SMA-13"
          },
          ...
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 15,
      "total_pages": 1
    }
  }
}

# 获取实体详情
GET /api/v1/entities/{entity_id}
Response:
{
  "code": 200,
  "data": {
    "entity_id": "uuid",
    "entity_type": "bridge",
    "entity_name": "3号跨线桥",
    "location": "K8+500",
    "design_parameters": {
      "total_length": 126.0,
      "span_configuration": "3×40",
      "bridge_type": "装配式预应力混凝土箱梁"
    },
    "components": [...],
    "photos": [...],
    "issues": [...]
  }
}
```

**照片数据接口**

```yaml
# 上传照片
POST /api/v1/photos
Content-Type: multipart/form-data
Parameters:
  - file: 照片文件
  - photo_type: 照片类型
  - description: 描述（可选）
  - entity_id: 关联实体ID（可选）
Headers:
  - Authorization: Bearer {token}
Response:
{
  "code": 200,
  "data": {
    "photo_id": "uuid",
    "file_path": "/uploads/2026/03/04/photo_xxx.jpg",
    "station": "K5+800",
    "station_display": "K5+800",
    "ai_classification": {
      "type": "construction_status",
      "value": "in_progress",
      "confidence": 0.92
    }
  }
}

# 查询照片列表
GET /api/v1/photos
Parameters:
  - project_id: 项目ID
  - station: 桩号（可选）
  - entity_id: 实体ID（可选）
  - photo_type: 照片类型（可选）
  - start_date: 开始日期（可选）
  - end_date: 结束日期（可选）
  - page: 页码
  - page_size: 每页数量
Response:
{
  "code": 200,
  "data": {
    "items": [
      {
        "photo_id": "uuid",
        "file_path": "/uploads/2026/03/04/photo_xxx.jpg",
        "station": "K5+800",
        "photo_type": "quality_issue",
        "captured_at": "2026-03-04T10:30:00Z",
        "captured_by": "张三"
      }
    ],
    "pagination": {...}
  }
}

# 获取照片详情（包括AI检测结果）
GET /api/v1/photos/{photo_id}
Response:
{
  "code": 200,
  "data": {
    "photo_id": "uuid",
    "file_path": "/uploads/2026/03/04/photo_xxx.jpg",
    "station": "K5+800",
    "location": {
      "latitude": 31.234567,
      "longitude": 117.890123,
      "accuracy": 5.0
    },
    "ai_classification": {
      "type": "quality_issue",
      "value": "crack",
      "confidence": 0.85
    },
    "ai_detection": [
      {
        "type": "crack",
        "location": {"x": 100, "y": 200, "width": 50, "height": 10},
        "confidence": 0.85
      }
    ],
    "issues": [
      {
        "issue_id": "uuid",
        "issue_type": "crack",
        "severity": "medium",
        "is_confirmed": true
      }
    ]
  }
}
```

**AI问答接口**

```yaml
# 知识问答
POST /api/v1/qa/query
Content-Type: application/json
Body:
{
  "question": "沥青路面压实要注意什么",
  "context": {
    "station": "K5+800",
    "entity_type": "pavement"
  }
}
Response:
{
  "code": 200,
  "data": {
    "answer": "沥青路面压实需要注意以下几点：...",
    "sources": [
      {
        "type": "standard",
        "code": "JTG F40-2004",
        "content": "..."
      },
      {
        "type": "process",
        "name": "压实",
        "content": "..."
      }
    ],
    "confidence": 0.92
  }
}

# 图纸语义查询
POST /api/v1/qa/drawing-query
Content-Type: application/json
Body:
{
  "question": "K5+800处路面结构设计是什么"
}
Response:
{
  "code": 200,
  "data": {
    "answer": "K5+800处路面结构为：上面层4cm SMA-13...",
    "entity_id": "uuid",
    "station_range": "K5+600-K6+200",
    "layers": [
      {
        "layer_name": "上面层",
        "thickness": 0.04,
        "material": "SMA-13"
      },
      ...
    ],
    "source_drawing": "路面结构设计图-第3页"
  }
}
```

**数据版本接口**

```yaml
# 获取数据版本列表
GET /api/v1/versions
Parameters:
  - project_id: 项目ID
Response:
{
  "code": 200,
  "data": {
    "items": [
      {
        "version_id": "uuid",
        "version_number": "1.0.0",
        "version_type": "initial",
        "change_summary": "初始版本",
        "created_at": "2026-01-15T10:00:00Z",
        "is_current": true
      }
    ]
  }
}

# 获取版本详情
GET /api/v1/versions/{version_id}
Response:
{
  "code": 200,
  "data": {
    "version_id": "uuid",
    "version_number": "1.1.0",
    "change_detail": {
      "changed_fields": [
        {
          "entity_type": "pavement_layer",
          "field_name": "thickness",
          "old_value": "0.18",
          "new_value": "0.20"
        }
      ]
    }
  }
}

# 对比两个版本差异
GET /api/v1/versions/compare
Parameters:
  - version_from: 起始版本ID
  - version_to: 目标版本ID
Response:
{
  "code": 200,
  "data": {
    "summary": {
      "total_changes": 15,
      "field_changes": 10,
      "entity_additions": 3,
      "entity_deletions": 2
    },
    "details": [...]
  }
}
```

## 四、核心代码实现

### 4.1 空间计算引擎

空间计算引擎是系统的核心模块，负责桩号与坐标的相互转换。

```python
# core/spatial/calculator.py
from decimal import Decimal, getcontext
from dataclasses import dataclass
from typing import Optional, List, Tuple
import math

# 设置高精度计算精度
getcontext().prec = 28


@dataclass
class Point2D:
    x: Decimal
    y: Decimal


@dataclass
class Point3D:
    x: Decimal
    y: Decimal
    z: Decimal


@dataclass
class StationPoint:
    station: Decimal
    lateral_offset: Decimal  # 横距，正数为左，负数为右
    elevation: Decimal
    point: Point3D


class AlignmentCalculator:
    """道路线形计算引擎"""

    def __init__(self, alignment_params: dict):
        self.params = alignment_params
        self.segments = self._parse_segments(alignment_params.get('segments', []))

    def _parse_segments(self, segments: List[dict]) -> List[dict]:
        """解析线形分段参数"""
        parsed = []
        for seg in segments:
            seg_type = seg.get('type')
            if seg_type == 'line':
                parsed.append({
                    'type': 'line',
                    'start_station': Decimal(str(seg['start_station'])),
                    'end_station': Decimal(str(seg['end_station'])),
                    'azimuth': Decimal(str(seg['azimuth'])),
                    'start_point': Point2D(
                        Decimal(str(seg['start_x'])),
                        Decimal(str(seg['start_y']))
                    )
                })
            elif seg_type == 'circle':
                parsed.append({
                    'type': 'circle',
                    'start_station': Decimal(str(seg['start_station'])),
                    'end_station': Decimal(str(seg['end_station'])),
                    'radius': Decimal(str(seg['radius'])),
                    'center': Point2D(
                        Decimal(str(seg['center_x'])),
                        Decimal(str(seg['center_y']))
                    ),
                    'direction': seg.get('direction', 'left')  # left or right
                })
            elif seg_type == 'spiral':
                parsed.append({
                    'type': 'spiral',
                    'start_station': Decimal(str(seg['start_station'])),
                    'end_station': Decimal(str(seg['end_station'])),
                    'radius_start': Decimal(str(seg.get('radius_start', float('inf')))),
                    'radius_end': Decimal(str(seg.get('radius_end', float('inf')))),
                    'spiral_type': seg.get('spiral_type', 'clothoid')
                })
        return parsed

    def station_to_point(self, station: Decimal,
                         lateral_offset: Decimal = Decimal('0'),
                         elevation: Optional[Decimal] = None) -> StationPoint:
        """桩号转坐标"""
        # 找到桩号所在的分段
        segment = self._find_segment(station)

        if segment['type'] == 'line':
            point = self._line_station_to_point(segment, station, lateral_offset)
        elif segment['type'] == 'circle':
            point = self._circle_station_to_point(segment, station, lateral_offset)
        else:
            # 螺旋线近似处理
            point = self._line_station_to_point(segment, station, lateral_offset)

        # 计算设计标高
        if elevation is None:
            elevation = self._calculate_elevation(station)

        return StationPoint(
            station=station,
            lateral_offset=lateral_offset,
            elevation=elevation,
            point=point
        )

    def _find_segment(self, station: Decimal) -> dict:
        """找到桩号所在的分段"""
        for seg in self.segments:
            if seg['start_station'] <= station <= seg['end_station']:
                return seg
        raise ValueError(f"桩号 {station} 不在线形范围内")

    def _line_station_to_point(self, segment: dict, station: Decimal,
                                lateral_offset: Decimal) -> Point3D:
        """直线段桩号转坐标"""
        delta_station = station - segment['start_station']

        # 主点坐标
        azimuth = segment['azimuth']
        main_x = segment['start_point'].x + delta_station * Decimal(str(math.cos(math.radians(float(azimuth)))))
        main_y = segment['start_point'].y + delta_station * Decimal(str(math.sin(math.radians(float(azimuth)))))

        # 横距偏移
        offset_azimuth = azimuth + 90 if lateral_offset > 0 else azimuth - 90
        x = main_x + abs(lateral_offset) * Decimal(str(math.cos(math.radians(float(offset_azimuth)))))
        y = main_y + abs(lateral_offset) * Decimal(str(math.sin(math.radians(float(offset_azimuth)))))

        return Point3D(x=x, y=y, z=Decimal('0'))

    def _circle_station_to_point(self, segment: dict, station: Decimal,
                                  lateral_offset: Decimal) -> Point3D:
        """圆曲线段桩号转坐标"""
        radius = segment['radius']
        center = segment['center']
        direction = segment['direction']

        # 计算圆心角
        delta_station = station - segment['start_station']
        angle = delta_station / radius  # 弧度

        # 主点位置（中心线）
        if direction == 'left':
            azimuth_to_center = 90  # 假设圆心在左侧
        else:
            azimuth_to_center = -90

        # 计算主点坐标
        start_azimuth = math.atan2(
            float(segment['start_point'].y - center.y),
            float(segment['start_point'].x - center.x)
        )
        current_azimuth = start_azimuth + (1 if direction == 'left' else -1) * float(angle)

        main_x = center.x + radius * Decimal(str(math.cos(current_azimuth)))
        main_y = center.y + radius * Decimal(str(math.sin(current_azimuth)))

        # 横距偏移
        offset_direction = 1 if lateral_offset > 0 else -1
        offset_azimuth = math.degrees(current_azimuth) + offset_direction * 90

        # 实际半径需要加上横距偏移
        effective_radius = radius + lateral_offset
        x = main_x + abs(lateral_offset) * Decimal(str(math.cos(math.radians(offset_azimuth))))
        y = main_y + abs(lateral_offset) * Decimal(str(math.sin(math.radians(offset_azimuth))))

        return Point3D(x=x, y=y, z=Decimal('0'))

    def _calculate_elevation(self, station: Decimal) -> Decimal:
        """计算设计标高（简化版，实际需要考虑竖曲线）"""
        # 这里应该调用竖曲线计算模块
        # 简化处理：假设线性插值
        return Decimal('100.0')  # 占位符

    def point_to_station(self, x: Decimal, y: Decimal) -> Tuple[Decimal, Decimal]:
        """坐标转桩号和横距（简化版）"""
        # 实际实现需要反向计算
        # 这里简化处理：找到最近的桩号
        return Decimal('5800'), Decimal('0')


class VerticalCurveCalculator:
    """竖曲线计算引擎"""

    def __init__(self, vertical_params: dict):
        self.params = vertical_params
        self.vertical_curves = self._parse_vertical_curves(
            vertical_params.get('vertical_curves', [])
        )

    def _parse_vertical_curves(self, curves: List[dict]) -> List[dict]:
        """解析竖曲线参数"""
        parsed = []
        for curve in curves:
            parsed.append({
                'station': Decimal(str(curve['station'])),
                'elevation': Decimal(str(curve['elevation'])),
                'curve_type': curve.get('type', '抛物线'),
                'length': Decimal(str(curve.get('length', '0'))),
                'grade_in': Decimal(str(curve.get('grade_in', '0'))),
                'grade_out': Decimal(str(curve.get('grade_out', '0')))
            })
        return parsed

    def calculate_elevation(self, station: Decimal) -> Decimal:
        """计算指定桩号的标高"""
        # 找到前后竖曲线
        prev_curve = None
        next_curve = None

        for curve in self.vertical_curves:
            if curve['station'] <= station:
                prev_curve = curve
            if curve['station'] >= station and next_curve is None:
                next_curve = curve

        if prev_curve is None:
            return Decimal('100.0')  # 默认值
        if next_curve is None or prev_curve == next_curve:
            # 直线段，线性插值
            return prev_curve['elevation']

        # 竖曲线段计算
        length = next_curve['station'] - prev_curve['station']
        if length == 0:
            return prev_curve['elevation']

        ratio = (station - prev_curve['station']) / length

        # 简化抛物线计算
        elevation = prev_curve['elevation'] + ratio * (
            next_curve['elevation'] - prev_curve['elevation']
        )

        return elevation
```

### 4.2 离线数据同步

移动端的离线同步是系统的关键技术点。

```python
# mobile/sync/offline_sync.py
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json


@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str
    table_name: str
    operation: str  # create, update, delete
    data: dict
    local_id: str
    server_id: Optional[str]
    status: str  # pending, synced, conflict
    created_at: datetime
    synced_at: Optional[datetime]


class OfflineSyncManager:
    """离线同步管理器"""

    def __init__(self, local_db, remote_api):
        self.local_db = local_db
        self.remote_api = remote_api
        self.pending_records: List[SyncRecord] = []

    async def initialize(self):
        """初始化同步管理器"""
        await self._load_pending_records()
        await self._setup_change_listeners()

    async def _load_pending_records(self):
        """加载待同步记录"""
        self.pending_records = await self.local_db.query(
            "SELECT * FROM sync_records WHERE status = 'pending' ORDER BY created_at"
        )

    async def _setup_change_listeners(self):
        """设置数据库变更监听"""
        # 监听本地数据库变化
        self.local_db.add_change_listener(self._on_local_change)

    def _on_local_change(self, table_name: str, operation: str,
                         record_id: str, data: dict):
        """本地数据变更回调"""
        # 创建同步记录
        sync_record = SyncRecord(
            record_id=self._generate_record_id(),
            table_name=table_name,
            operation=operation,
            data=data,
            local_id=record_id,
            server_id=None,
            status='pending',
            created_at=datetime.utcnow(),
            synced_at=None
        )

        # 保存到本地同步队列
        self.pending_records.append(sync_record)
        self.local_db.insert('sync_records', asdict(sync_record))

    def _generate_record_id(self) -> str:
        """生成记录ID"""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]

    async def sync(self) -> Dict:
        """执行同步"""
        if not self.pending_records:
            return {'status': 'no_pending', 'synced': 0}

        synced_count = 0
        failed_records = []

        for record in self.pending_records:
            try:
                await self._sync_record(record)
                record.status = 'synced'
                record.synced_at = datetime.utcnow()
                synced_count += 1
            except Exception as e:
                record.status = 'failed'
                failed_records.append({
                    'record_id': record.record_id,
                    'error': str(e)
                })

            # 更新记录状态
            await self.local_db.update(
                'sync_records',
                {'status': record.status, 'synced_at': record.synced_at},
                {'record_id': record.record_id}
            )

        # 清理已同步记录
        self.pending_records = [
            r for r in self.pending_records
            if r.status != 'synced'
        ]

        return {
            'status': 'completed',
            'synced': synced_count,
            'failed': len(failed_records),
            'failed_records': failed_records
        }

    async def _sync_record(self, record: SyncRecord):
        """同步单条记录"""
        if record.operation == 'create':
            # 上传新记录
            server_id = await self.remote_api.create(
                record.table_name,
                record.data
            )
            # 更新本地server_id
            await self.local_db.update(
                record.table_name,
                {'server_id': server_id},
                {'local_id': record.local_id}
            )
            record.server_id = server_id

        elif record.operation == 'update':
            # 更新服务器记录
            await self.remote_api.update(
                record.table_name,
                record.server_id,
                record.data
            )

        elif record.operation == 'delete':
            # 删除服务器记录
            if record.server_id:
                await self.remote_api.delete(
                    record.table_name,
                    record.server_id
                )

    async def resolve_conflicts(self, conflicts: List[Dict]):
        """解决冲突"""
        for conflict in conflicts:
            resolution = conflict.get('resolution', 'server_wins')
            record_id = conflict['record_id']

            if resolution == 'server_wins':
                # 使用服务器数据覆盖本地
                server_data = await self.remote_api.get(
                    conflict['table_name'],
                    conflict['server_id']
                )
                await self.local_db.update(
                    conflict['table_name'],
                    server_data,
                    {'local_id': conflict['local_id']}
                )
            elif resolution == 'local_wins':
                # 强制上传本地数据
                record = next(
                    r for r in self.pending_records
                    if r.local_id == conflict['local_id']
                )
                await self._sync_record(record)

            # 标记冲突已解决
            await self.local_db.update(
                'sync_records',
                {'status': 'resolved'},
                {'record_id': record_id}
            )
```

### 4.3 AI质量检测

AI质量检测模块的核心代码示例。

```python
# core/ai/quality_detector.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from PIL import Image
import torch
from torchvision import transforms


@dataclass
class DetectionResult:
    """检测结果"""
    type: str
    confidence: float
    bbox: Dict  # x, y, width, height
    severity: Optional[str] = None


class QualityDetector:
    """AI质量检测器"""

    def __init__(self, model_path: str, config: dict):
        self.model_path = model_path
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.classifier = None
        self._load_models()

    def _load_models(self):
        """加载模型"""
        # 加载目标检测模型（裂缝、破损等）
        self.model = torch.load(self.model_path, map_location=self.device)
        self.model.eval()

        # 加载分类模型（施工状态、部位等）
        classifier_path = self.config.get('classifier_path')
        self.classifier = torch.load(classifier_path, map_location=self.device)
        self.classifier.eval()

        # 图像预处理变换
        self.transform = transforms.Compose([
            transforms.Resize((640, 640)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def detect(self, image: Image.Image) -> Dict:
        """执行质量检测"""
        # 图像预处理
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 目标检测
        with torch.no_grad():
            detections = self.model(input_tensor)

        # 解析检测结果
        results = self._parse_detections(detections)

        # 图像分类
        classification = self._classify_image(image)

        return {
            'detections': results,
            'classification': classification
        }

    def _parse_detections(self, detections) -> List[DetectionResult]:
        """解析检测结果"""
        results = []

        # 简化的后处理（实际需要根据模型输出格式调整）
        for det in detections:
            if det['score'] > self.config.get('confidence_threshold', 0.5):
                results.append(DetectionResult(
                    type=det['class'],
                    confidence=float(det['score']),
                    bbox=det['bbox'],
                    severity=self._estimate_severity(det)
                ))

        return results

    def _classify_image(self, image: Image.Image) -> Dict:
        """图像分类"""
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.classifier(input_tensor)
            probs = torch.softmax(outputs, dim=1)

        # 获取预测类别
        pred_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_class].item()

        # 映射到类别名称
        class_names = self.config.get('class_names', {})
        class_name = class_names.get(str(pred_class), 'unknown')

        return {
            'class': class_name,
            'confidence': confidence,
            'probabilities': probs[0].cpu().numpy().tolist()
        }

    def _estimate_severity(self, detection: Dict) -> str:
        """估算严重程度"""
        # 基于检测框面积和置信度估算
        bbox = detection['bbox']
        area = bbox.get('width', 0) * bbox.get('height', 0)
        confidence = detection['score']

        if confidence > 0.8 and area > 5000:
            return 'high'
        elif confidence > 0.6 and area > 2000:
            return 'medium'
        else:
            return 'low'

    async def batch_detect(self, images: List[Image.Image]) -> List[Dict]:
        """批量检测"""
        results = []
        for image in images:
            result = self.detect(image)
            results.append(result)
        return results


class HumanInLoopVerifier:
    """人机协作验证器"""

    def __init__(self, detector: QualityDetector):
        self.detector = detector
        self.feedback_history: List[Dict] = []

    async def verify_and_get_feedback(self, photo_id: str,
                                       detection_result: Dict) -> Dict:
        """验证检测结果并收集反馈"""
        # 构建验证请求
        verification_request = {
            'photo_id': photo_id,
            'detections': detection_result.get('detections', []),
            'classification': detection_result.get('classification')
        }

        # 返回验证界面所需数据
        return {
            'request': verification_result,
            'requires_verification': self._needs_verification(detection_result)
        }

    def _needs_verification(self, result: Dict) -> bool:
        """判断是否需要人工验证"""
        # 置信度低于阈值的需要验证
        classification = result.get('classification', {})
        if classification.get('confidence', 1.0) < 0.8:
            return True

        # 检测到高危问题需要验证
        for det in result.get('detections', []):
            if det.get('severity') == 'high':
                return True

        return False

    async def record_feedback(self, photo_id: str,
                              user_id: str,
                              feedback: Dict):
        """记录用户反馈"""
        feedback_record = {
            'photo_id': photo_id,
            'user_id': user_id,
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.feedback_history.append(feedback_record)

        # 存储到数据库
        await self._save_feedback(feedback_record)

    async def _save_feedback(self, feedback: Dict):
        """保存反馈到数据库"""
        # 实现数据库写入逻辑
        pass

    async def retrain_model(self):
        """基于反馈重新训练模型"""
        if len(self.feedback_history) < 100:
            return {'status': 'insufficient_data'}

        # 准备训练数据
        training_data = self._prepare_training_data()

        # 调用训练服务
        # 这里应该调用模型训练API
        training_result = {
            'status': 'training',
            'samples': len(training_data),
            'estimated_time': '2 hours'
        }

        return training_result

    def _prepare_training_data(self) -> List[Dict]:
        """准备训练数据"""
        # 从反馈历史中提取标注数据
        return []
```

## 五、部署与运维

### 5.1 Docker部署配置

系统采用Docker容器化部署，以下是核心的docker-compose配置。

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgis/postgis:15-3.3
    container_name: neuralsite-postgres
    environment:
      POSTGRES_DB: neuralsite
      POSTGRES_USER: neuralsite
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U neuralsite"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j图数据库
  neo4j:
    image: neo4j:5.11-community
    container_name: neuralsite-neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_server_memory_heap_initial__size: 512m
      NEO4J_server_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"
      - "7687:7687"

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: neuralsite-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # FastAPI后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: neuralsite-backend
    environment:
      DATABASE_URL: postgresql://neuralsite:${POSTGRES_PASSWORD}@postgres:5432/neuralsite
      NEO4J_URI: bolt://neo4j:7687
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_started
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # 前端Web服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: neuralsite-frontend
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
    ports:
      - "80:80"
    depends_on:
      - backend

  # Celery任务队列
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: neuralsite-celery
    environment:
      DATABASE_URL: postgresql://neuralsite:${POSTGRES_PASSWORD}@postgres:5432/neuralsite
      NEO4J_URI: bolt://neo4j:7687
      REDIS_URL: redis://redis:6379/0
    command: celery -A tasks worker --loglevel=info
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
  uploads:
```

### 5.2 环境变量配置

```bash
# .env
# 数据库配置
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://neuralsite:${POSTGRES_PASSWORD}@postgres:5432/neuralsite

# Neo4j配置
NEO4J_PASSWORD=your_secure_password
NEO4J_URI=bolt://neo4j:7687

# Redis配置
REDIS_URL=redis://redis:6379/0

# JWT密钥
JWT_SECRET_KEY=your_jwt_secret_key

# 文件上传配置
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=/app/uploads

# AI模型配置
AI_MODEL_PATH=/app/models
AI_CONFIDENCE_THRESHOLD=0.5

# 日志配置
LOG_LEVEL=INFO
```

### 5.3 备份与恢复策略

系统采用以下备份策略确保数据安全：

**数据库备份**。PostgreSQL每日凌晨2点执行全量备份，保留最近7天的全量备份；每小时执行增量备份（WAL归档），保留最近24小时的增量备份；每月执行一次全量备份，保留最近12个月的月度备份；备份文件加密后上传到对象存储。

**图数据库备份**。Neo4j每周执行一次全量备份；备份文件同时保存在本地和远程存储；恢复时停止服务，执行备份恢复脚本。

**文件存储备份**。用户上传的文件采用对象存储（如MinIO或云存储）；对象存储本身具有多副本冗余；关键文件定期下载到本地备份。

## 六、版本兼容性说明

### 6.1 版本演进规划

本技术规格说明书对应NeuralSite智网V2.0版本。未来版本规划如下：

**V2.1版本（预计2026年Q2）**。增加多项目管理支持；优化AI模型推理性能；增加更多质量检测类型。

**V2.2版本（预计2026年Q3）**。增加BIM模型导入功能；支持更多三维数据格式；增强施工模拟功能。

**V3.0版本（预计2026年Q4）**。引入更先进的AI模型；增加AR增强现实功能；支持更多类型的IoT设备对接。

### 6.2 升级注意事项

版本升级时需要注意以下事项：

**数据库迁移**。每次版本升级都会附带数据库迁移脚本；升级前务必备份数据库；升级脚本按版本号顺序执行。

**模型更新**。AI模型可能随版本更新；模型文件单独下载放置到指定目录；模型更新后需要重新训练项目特定模型。

**配置变更**。部分配置项可能随版本调整；升级前对比配置文件差异；保留旧版本配置文件作为参考。

---

**编制单位：MiniMax Agent**

**编制日期：2026年3月4日**

**版本：V2.0**
