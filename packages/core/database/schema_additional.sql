-- NeuralSite 数据库补充 - 按整改建议书
-- 添加缺失的核心表

-- =====================
-- P0: 照片记录表
-- =====================
CREATE TABLE IF NOT EXISTS photo_records (
    photo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),
    file_size BIGINT,
    captured_at TIMESTAMPTZ NOT NULL,
    captured_by UUID,
    -- GPS位置
    latitude DECIMAL(11, 8),
    longitude DECIMAL(12, 8),
    gps_accuracy DECIMAL(8, 2),
    -- 桩号定位
    station DECIMAL(18, 4),
    station_display VARCHAR(20),
    -- AI分类
    ai_classification JSONB,
    ai_detection JSONB,
    -- 人工确认
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID,
    verified_at TIMESTAMPTZ,
    -- 关联
    entity_id UUID,
    entity_type VARCHAR(50),
    description TEXT,
    -- 元数据
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_photo_project ON photo_records(project_id);
CREATE INDEX IF NOT EXISTS idx_photo_station ON photo_records(station);
CREATE INDEX IF NOT EXISTS idx_photo_captured_by ON photo_records(captured_by);
CREATE INDEX IF NOT EXISTS idx_photo_captured_at ON photo_records(captured_at);

-- =====================
-- P0: 问题记录表
-- =====================
CREATE TABLE IF NOT EXISTS issues (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    issue_type VARCHAR(50) NOT NULL, -- quality/safety/progress
    severity VARCHAR(20) DEFAULT 'medium', -- critical/major/minor
    title VARCHAR(200) NOT NULL,
    description TEXT,
    -- 位置信息
    station DECIMAL(18, 4),
    station_display VARCHAR(20),
    latitude DECIMAL(11, 8),
    longitude DECIMAL(12, 8),
    -- 关联照片
    photo_ids JSONB,
    -- 状态流转
    status VARCHAR(20) DEFAULT 'open', -- open/in_progress/resolved/closed
    reported_by UUID,
    reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    -- 整改期限
    deadline TIMESTAMPTZ,
    -- 元数据
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_issue_project ON issues(project_id);
CREATE INDEX IF NOT EXISTS idx_issue_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issue_station ON issues(station);
CREATE INDEX IF NOT EXISTS idx_issue_reported_by ON issues(reported_by);
CREATE INDEX IF NOT EXISTS idx_issue_assigned_to ON issues(assigned_to);

-- =====================
-- P1: 用户表
-- =====================
CREATE TABLE IF NOT EXISTS users (
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
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_project ON users(project_id);

-- =====================
-- P2: 施工进度表
-- =====================
CREATE TABLE IF NOT EXISTS construction_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- road_section/bridge/tunnel等
    station_start DECIMAL(18, 4),
    station_end DECIMAL(18, 4),
    -- 计划
    planned_start_date DATE,
    planned_end_date DATE,
    planned_quantity DECIMAL(18, 4),
    -- 实际
    actual_start_date DATE,
    actual_end_date DATE,
    actual_quantity DECIMAL(18, 4),
    -- 完成百分比
    completion_rate DECIMAL(5, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'not_started', -- not_started/in_progress/completed
    notes TEXT,
    updated_by UUID,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_progress_project ON construction_progress(project_id);
CREATE INDEX IF NOT EXISTS idx_progress_entity ON construction_progress(entity_id);

-- =====================
-- P2: 材料进场表
-- =====================
CREATE TABLE IF NOT EXISTS material_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    material_type VARCHAR(50) NOT NULL,
    material_name VARCHAR(100),
    supplier VARCHAR(200),
    quantity DECIMAL(18, 4),
    unit VARCHAR(20),
    arrival_date DATE,
    quality_certified BOOLEAN DEFAULT FALSE,
    inspected_by UUID,
    inspected_at TIMESTAMPTZ,
    remark TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_material_project ON material_records(project_id);
CREATE INDEX IF NOT EXISTS idx_material_type ON material_records(material_type);

-- =====================
-- P2: 设备进场表
-- =====================
CREATE TABLE IF NOT EXISTS equipment_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    equipment_name VARCHAR(100),
    plate_number VARCHAR(50),
    operator VARCHAR(100),
    arrival_date DATE,
    departure_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- active/inactive
    remark TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_equipment_project ON equipment_records(project_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment_records(status);

-- =====================
-- 插入默认管理员用户
-- =====================
INSERT INTO users (username, password_hash, real_name, role_id, is_active) 
SELECT 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ePLF0.Q.gFyu', '系统管理员', role_id, TRUE
FROM user_role WHERE role_code = 'admin'
ON CONFLICT (username) DO NOTHING;

INSERT INTO users (username, password_hash, real_name, role_id, is_active) 
SELECT 'demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ePLF0.Q.gFyu', '演示用户', role_id, TRUE
FROM user_role WHERE role_code = 'manager'
ON CONFLICT (username) DO NOTHING;
