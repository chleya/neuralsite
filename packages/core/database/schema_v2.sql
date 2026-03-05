-- NeuralSite V2.0 数据库完整表结构
-- 基于技术规格说明书

-- 1. 坐标参考系统表
CREATE TABLE IF NOT EXISTS coordinate_reference_system (
    crs_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crs_code VARCHAR(50) NOT NULL UNIQUE,
    crs_name VARCHAR(200) NOT NULL,
    crs_type VARCHAR(20) NOT NULL CHECK (crs_type IN ('geographic', 'projected', 'local')),
    projection_method VARCHAR(50),
    central_meridian DECIMAL(12, 6),
    false_easting DECIMAL(18, 6),
    false_northing DECIMAL(18, 6),
    scale_factor DECIMAL(18, 10),
    vertical_datum VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. 里程桩号系统表
CREATE TABLE IF NOT EXISTS station_system (
    system_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name VARCHAR(200) NOT NULL,
    start_station VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('forward', 'backward')),
    interval_length INTEGER DEFAULT 100,
    coordinate_system_id UUID REFERENCES coordinate_reference_system(crs_id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. 里程-坐标映射表
CREATE TABLE IF NOT EXISTS station_coordinate_mapping (
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(station_system_id, station)
);

CREATE INDEX IF NOT EXISTS idx_station_mapping_station ON station_coordinate_mapping(station);
CREATE INDEX IF NOT EXISTS idx_station_mapping_spatial ON station_coordinate_mapping USING GIST(ST_MakePoint(easting, northing));

-- 4. 道路段落表
CREATE TABLE IF NOT EXISTS road_section (
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_road_section_project ON road_section(project_id);
CREATE INDEX IF NOT EXISTS idx_road_section_station ON road_section(start_station, end_station);

-- 5. 工程实体表
CREATE TABLE IF NOT EXISTS engineering_entity (
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entity_project ON engineering_entity(project_id);
CREATE INDEX IF NOT EXISTS idx_entity_type ON engineering_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_station ON engineering_entity(start_station, end_station);

-- 6. 路面结构层表
CREATE TABLE IF NOT EXISTS pavement_layer (
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. 桥梁表
CREATE TABLE IF NOT EXISTS bridge (
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. 桥梁构件表
CREATE TABLE IF NOT EXISTS bridge_component (
    component_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bridge_id UUID REFERENCES bridge(bridge_id),
    component_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(200) NOT NULL,
    component_code VARCHAR(100),
    quantity INTEGER,
    dimensions JSONB,
    material JSONB,
    reinforcement JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 9. 照片记录表 (更新 - 已存在)
ALTER TABLE photo_record ADD COLUMN IF NOT EXISTS ai_detection JSONB;
ALTER TABLE photo_record ADD COLUMN IF NOT EXISTS entity_id UUID REFERENCES engineering_entity(entity_id);
ALTER TABLE photo_record ADD COLUMN IF NOT EXISTS photo_type VARCHAR(50) NOT NULL DEFAULT 'construction';

-- 10. 照片问题记录表
CREATE TABLE IF NOT EXISTS photo_issue (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID REFERENCES photo_record(photo_id),
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    location_in_photo JSONB,
    ai_confidence DECIMAL(5, 4),
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmed_by UUID,
    confirmed_at TIMESTAMPTZ,
    resolution_status VARCHAR(20) DEFAULT 'open',
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. 数据版本表
CREATE TABLE IF NOT EXISTS data_version (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    version_type VARCHAR(20) NOT NULL CHECK (version_type IN ('initial', 'revision', 'amendment')),
    change_summary TEXT,
    change_detail JSONB,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    UNIQUE(project_id, version_number)
);

-- 12. 数据血缘表
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_id UUID NOT NULL,
    data_field VARCHAR(100),
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(200),
    source_detail JSONB,
    extracted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    extracted_by VARCHAR(100),
    confidence DECIMAL(5, 4) DEFAULT 1.0,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID,
    verified_at TIMESTAMPTZ
);

-- 13. 数据校验错误日志表
CREATE TABLE IF NOT EXISTS validation_error_log (
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
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT
);

-- 14. 角色表 (更新)
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100);

CREATE TABLE IF NOT EXISTS user_role (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 15. 操作日志表
CREATE TABLE IF NOT EXISTS operation_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    user_id UUID,
    operation_type VARCHAR(30) NOT NULL,
    data_type VARCHAR(50),
    data_id UUID,
    ip_address INET,
    operation_detail JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_operation_log_user ON operation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_log_created_at ON operation_log(created_at);

-- 16. 同步队列表 (更新 - 已存在 sync_queue)
ALTER TABLE sync_queue ADD COLUMN IF NOT EXISTS device_id VARCHAR(100);
ALTER TABLE sync_queue ADD COLUMN IF NOT EXISTS app_version VARCHAR(20);

-- 17. 隧道表
CREATE TABLE IF NOT EXISTS tunnel (
    tunnel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entity(entity_id),
    tunnel_name VARCHAR(200) NOT NULL,
    location VARCHAR(50),
    total_length DECIMAL(12, 4),
    tunnel_type VARCHAR(100),
    cross_section_area DECIMAL(10, 4),
    construction_method VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 18. 涵洞表
CREATE TABLE IF NOT EXISTS culvert (
    culvert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES engineering_entity(entity_id),
    culvert_name VARCHAR(200) NOT NULL,
    location VARCHAR(50),
    culvert_type VARCHAR(50),
    span DECIMAL(8, 2),
    height DECIMAL(8, 2),
    length DECIMAL(12, 4),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认角色
INSERT INTO user_role (role_name, role_code, permissions) VALUES 
('管理员', 'admin', '{"all": true}'),
('项目经理', 'manager', '{"projects": ["read", "write"], "reports": ["read"]}'),
('工程师', 'engineer', '{"data": ["read", "write"], "photos": ["read", "write"]}'),
('施工员', 'worker', '{"photos": ["read", "write"], "stations": ["read"]}')
ON CONFLICT (role_code) DO NOTHING;

-- 插入默认坐标系统
INSERT INTO coordinate_reference_system (crs_code, crs_name, crs_type, projection_method, central_meridian, is_active) VALUES
('CGCS2000/3-GK-117E', '国家2000坐标系 3度带中央子午线117度', 'projected', 'Gauss-Kruger', 117, true),
('WGS84', 'WGS84地理坐标系', 'geographic', 'LL', 0, true),
('LOCAL', '本地坐标系', 'local', 'NONE', 0, true)
ON CONFLICT (crs_code) DO NOTHING;

-- 插入默认桩号系统
INSERT INTO station_system (system_name, start_station, direction, interval_length) VALUES
('K系列桩号', 'K0+000', 'forward', 100),
('里程桩号', 'K0+000', 'forward', 100)
ON CONFLICT DO NOTHING;
