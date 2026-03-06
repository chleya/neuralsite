-- ============================================================
-- NeuralSite 时空状态管理系统 - 数据库脚本
-- 版本: V1.0
-- 日期: 2026-03-06
-- ============================================================

-- 启用PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. 项目表
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 2. 空间层 - 控制点（连续体）
-- ============================================================
CREATE TABLE IF NOT EXISTS spatial_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    station DECIMAL(12,3) NOT NULL,      -- K5+800.123 → 5800.123
    lateral DECIMAL(8,3) DEFAULT 0,      -- 横距
    elevation DECIMAL(10,3),             -- 高程
    geom GEOMETRY(PointZ, 4326),        -- PostGIS 3D点
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, station, lateral)
);

-- 空间控制点索引
CREATE INDEX idx_spatial_project_station ON spatial_controls(project_id, station);
CREATE INDEX idx_spatial_geom ON spatial_controls USING gist(geom);

-- ============================================================
-- 3. 实体层 - 工程实体（贴纸）
-- ============================================================
CREATE TABLE IF NOT EXISTS engineering_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    type TEXT NOT NULL,                  -- subgrade/pavement/bridge/culvert/tunnel
    code TEXT UNIQUE NOT NULL,           -- PAV-K5600-K6200
    station_start DECIMAL(12,3) NOT NULL,
    station_end DECIMAL(12,3) NOT NULL,
    lateral_min DECIMAL(8,3) DEFAULT 0,
    lateral_max DECIMAL(8,3) DEFAULT 0,
    elev_min DECIMAL(10,3) DEFAULT 0,
    elev_max DECIMAL(10,3) DEFAULT 0,
    geom GEOMETRY(POLYHEDRALSURFACEZ, 4326),  -- 可选3D边界
    attributes JSONB DEFAULT '{}',       -- {"material":"C30","design_thickness":0.36,...}
    lod_level INT DEFAULT 1,            -- 0/1/2 LOD层级
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 实体空间索引（关键性能）
CREATE INDEX idx_entities_station_range ON engineering_entities USING gist(station_start, station_end);
CREATE INDEX idx_entities_project ON engineering_entities(project_id);
CREATE INDEX idx_entities_type ON engineering_entities(type);

-- ============================================================
-- 4. 状态层 - 快照（核心表）
-- ============================================================
CREATE TABLE IF NOT EXISTS entity_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entities(id) ON DELETE CASCADE,
    snapshot_time TIMESTAMPTZ DEFAULT now(),
    version_type TEXT NOT NULL,         -- initial/designed/actual/as_built/simulated
    progress DECIMAL(5,2) DEFAULT 0,   -- 0-100
    spatial_snapshot JSONB DEFAULT '{}',     -- {"coverage":0.85,...}
    attribute_snapshot JSONB DEFAULT '{}',  -- {"layers":[{name:"基层",status:"completed",thickness:0.36},...]}
    delta JSONB DEFAULT '{}',               -- 与上一条的差异（增量）
    photos UUID[] DEFAULT '{}',             -- 关联照片
    issues UUID[] DEFAULT '{}',             -- 关联问题
    hash TEXT,                              -- SHA-256 用于区块链存证
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 状态查询索引（关键性能）
CREATE INDEX idx_states_entity_time ON entity_states(entity_id, snapshot_time DESC);
CREATE INDEX idx_states_hash ON entity_states(hash);
CREATE INDEX idx_states_version ON entity_states(version_type);

-- ============================================================
-- 5. 事件层 - 扰动
-- ============================================================
CREATE TABLE IF NOT EXISTS state_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,           -- weather/blockage/disaster/change_order
    station_start DECIMAL(12,3),
    station_end DECIMAL(12,3),
    data JSONB DEFAULT '{}',             -- {"rainfall_mm":120,"delay_days":3,...}
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    affected_entities UUID[] DEFAULT '{}',
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 事件空间索引
CREATE INDEX idx_events_station ON state_events USING gist(station_start, station_end);
CREATE INDEX idx_events_project_time ON state_events(project_id, start_time DESC);
CREATE INDEX idx_events_type ON state_events(event_type);

-- ============================================================
-- 6. 过程数据 - 照片/日志（移动端主力）
-- ============================================================
CREATE TABLE IF NOT EXISTS process_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entities(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    photo_url TEXT,
    station DECIMAL(12,3),
    spatial_ref UUID REFERENCES spatial_controls(id),
    ai_tags JSONB DEFAULT '{}',         -- AI自动标签
    ai_confidence DECIMAL(5,4),         -- AI置信度
    offline_synced BOOLEAN DEFAULT false,
    station_name TEXT,                  -- 桩号名称如 K5+800
    description TEXT,
    created_by TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- 过程数据索引
CREATE INDEX idx_process_entity ON process_data(entity_id, uploaded_at DESC);
CREATE INDEX idx_process_station ON process_data(station);
CREATE INDEX idx_process_offline ON process_data(offline_synced) WHERE offline_synced = false;

-- ============================================================
-- 7. 问题记录
-- ============================================================
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES engineering_entities(id) ON DELETE SET NULL,
    process_data_id UUID REFERENCES process_data(id) ON DELETE SET NULL,
    
    issue_type TEXT NOT NULL,          -- crack/damage/rebar_exposed/...
    severity TEXT NOT NULL,            -- light/medium/heavy
    description TEXT,
    status TEXT DEFAULT 'pending',     -- pending/assigned/fixed/confirmed
    assigned_to TEXT,
    fixed_at TIMESTAMPTZ,
    confirmed_by TEXT,
    confirmed_at TIMESTAMPTZ,
    hash TEXT,                         -- 区块链存证
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 问题索引
CREATE INDEX idx_issues_entity ON issues(entity_id, status);
CREATE INDEX idx_issues_project ON issues(project_id, created_at DESC);

-- ============================================================
-- 视图：实体当前状态
-- ============================================================
CREATE OR REPLACE VIEW v_entity_current_state AS
SELECT 
    e.id as entity_id,
    e.code,
    e.type,
    e.station_start,
    e.station_end,
    s.snapshot_time,
    s.version_type,
    s.progress,
    s.hash as state_hash,
    s.created_by
FROM engineering_entities e
LEFT JOIN LATERAL (
    SELECT * FROM entity_states 
    WHERE entity_id = e.id 
    ORDER BY snapshot_time DESC 
    LIMIT 1
) s ON true;

-- ============================================================
-- 函数：计算状态哈希
-- ============================================================
CREATE OR REPLACE FUNCTION compute_state_hash(state_id UUID)
RETURNS TEXT AS $$
DECLARE
    rec entity_states%ROWTYPE;
    json_data TEXT;
    hash_value TEXT;
BEGIN
    SELECT * INTO rec FROM entity_states WHERE id = state_id;
    
    json_data := json_build_object(
        'entity_id', rec.entity_id,
        'snapshot_time', rec.snapshot_time,
        'version_type', rec.version_type,
        'progress', rec.progress,
        'spatial_snapshot', rec.spatial_snapshot,
        'attribute_snapshot', rec.attribute_snapshot
    )::text;
    
    hash_value := encode(sha256(json_data::bytea), 'hex');
    
    UPDATE entity_states SET hash = hash_value WHERE id = state_id;
    
    RETURN hash_value;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 模拟数据
-- ============================================================
INSERT INTO projects (name, description) VALUES 
('京沪高速拓宽工程', '北京至上海高速公路拓宽工程'),
('雄安新区市政道路', '雄安新区起步区市政道路工程');

-- 添加示例实体
INSERT INTO engineering_entities (project_id, type, code, station_start, station_end, attributes)
SELECT 
    id, 
    'pavement',
    'PAV-K5000-K5500',
    5000, 
    5500,
    '{"material":"C30","design_thickness":0.36,"layers":["基层","面层"]}'
FROM projects WHERE name = '京沪高速拓宽工程';

-- 添加示例状态
INSERT INTO entity_states (entity_id, version_type, progress, spatial_snapshot, attribute_snapshot, created_by)
SELECT 
    id,
    'designed',
    100,
    '{"coverage":1.0}',
    '{"layers":[{"name":"基层","status":"completed","thickness":0.36}]}',
    'system'
FROM engineering_entities
WHERE code = 'PAV-K5000-K5500';

-- 添加实际状态
INSERT INTO entity_states (entity_id, version_type, progress, spatial_snapshot, attribute_snapshot, created_by)
SELECT 
    id,
    'actual',
    85,
    '{"coverage":0.85}',
    '{"layers":[{"name":"基层","status":"completed","thickness":0.36}]}',
    'worker_zhang'
FROM engineering_entities
WHERE code = 'PAV-K5000-K5500';

-- 更新哈希
UPDATE entity_states SET hash = compute_state_hash(id);

SELECT 'Database schema created successfully!' as result;
