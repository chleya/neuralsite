-- NeuralSite P0 数据库迁移脚本
-- 版本: 001_p0_baseline
-- 创建时间: 2026-03-05
-- 优先级: P0 (照片管理 + 问题跟踪 + 用户权限)

BEGIN;

-- ============================================
-- 用户与权限相关表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    real_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'worker', -- admin/manager/engineer/worker
    project_id UUID,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_project ON users(project_id);
CREATE INDEX idx_users_role ON users(role);

-- ============================================
-- 照片记录表 (P0)
-- ============================================
CREATE TABLE IF NOT EXISTS photo_records (
    photo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),
    file_size INTEGER,
    mime_type VARCHAR(50),
    captured_at TIMESTAMP NOT NULL,
    captured_by UUID REFERENCES users(user_id),
    
    -- GPS位置
    latitude DECIMAL(11, 8),
    longitude DECIMAL(12, 8),
    gps_accuracy DECIMAL(8, 2),
    
    -- 桩号定位
    station DECIMAL(18, 4),
    station_display VARCHAR(20),
    
    -- AI分类
    ai_classification JSONB, -- {"type": "quality", "value": "crack", "confidence": 0.85}
    
    -- 人工确认
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(user_id),
    verified_at TIMESTAMP,
    
    -- 关联实体
    entity_id UUID,
    entity_type VARCHAR(50), -- route/bridge/tunnel/etc
    
    description TEXT,
    tags JSONB, -- ["摊铺", "沥青", "施工中"]
    
    -- 同步状态
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending/synced/conflict
    local_id VARCHAR(100), -- 离线端本地ID
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_photo_project ON photo_records(project_id);
CREATE INDEX idx_photo_station ON photo_records(station);
CREATE INDEX idx_photo_captured_by ON photo_records(captured_by);
CREATE INDEX idx_photo_captured_at ON photo_records(captured_at);
CREATE INDEX idx_photo_sync_status ON photo_records(sync_status);

-- ============================================
-- 问题记录表 (P0)
-- ============================================
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
    location_description VARCHAR(500),
    
    -- 关联照片
    photo_ids JSONB, -- [photo_id1, photo_id2]
    
    -- 状态流转
    status VARCHAR(20) DEFAULT 'open', -- open/in_progress/resolved/closed
    reported_by UUID REFERENCES users(user_id),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID REFERENCES users(user_id),
    assigned_at TIMESTAMP,
    resolved_by UUID,
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    
    -- 整改期限
    deadline TIMESTAMP,
    
    -- AI初筛结果
    ai_screening JSONB, -- {"category": "裂缝", "risk_level": "high", "suggestion": "立即处理"}
    
    -- 同步状态
    sync_status VARCHAR(20) DEFAULT 'pending',
    local_id VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_issue_project ON issues(project_id);
CREATE INDEX idx_issue_status ON issues(status);
CREATE INDEX idx_issue_station ON issues(station);
CREATE INDEX idx_issue_reported_by ON issues(reported_by);
CREATE INDEX idx_issue_assigned_to ON issues(assigned_to);
CREATE INDEX idx_issue_type ON issues(issue_type);
CREATE INDEX idx_issue_severity ON issues(severity);
CREATE INDEX idx_issue_sync_status ON issues(sync_status);

-- ============================================
-- 同步队列表 (P0 离线同步核心)
-- ============================================
CREATE TABLE IF NOT EXISTS sync_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- photo/issue/progress
    entity_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- create/update/delete
    payload JSONB NOT NULL,
    
    -- 设备信息
    device_id VARCHAR(100),
    app_version VARCHAR(20),
    
    -- 同步状态
    status VARCHAR(20) DEFAULT 'pending', -- pending/processing/synced/failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_sync_queue_status ON sync_queue(status);
CREATE INDEX idx_sync_queue_entity ON sync_queue(entity_type, entity_id);
CREATE INDEX idx_sync_queue_created ON sync_queue(created_at);

-- ============================================
-- 项目表扩展 (已有Project表，添加字段)
-- ============================================
-- 注意: 假设已有 projects 表，这里添加字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'planning';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS start_date DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS end_date DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS location VARCHAR(200);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(user_id);

-- ============================================
-- 初始管理员用户 (密码: admin123, 需要在首次登录后修改)
-- ============================================
-- 密码使用bcrypt哈希，这里是明文密码的占位符
INSERT INTO users (username, password_hash, real_name, role, is_active)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIBx5Q5Z8W', '系统管理员', 'admin', true)
ON CONFLICT (username) DO NOTHING;

COMMIT;

-- 验证表创建
SELECT 'Users table rows:' AS info, COUNT(*) FROM users;
SELECT 'Photo records table rows:' AS info, COUNT(*) FROM photo_records;
SELECT 'Issues table rows:' AS info, COUNT(*) FROM issues;
SELECT 'Sync queue table rows:' AS info, COUNT(*) FROM sync_queue;
