-- NeuralSite 4D 事件数据
-- 施工事件表示例数据

-- K0+000-K1+000 路基
INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K0+000-K1+000', 'roadbed', 'start', '{"task": "路基填筑", "duration_days": 30}', '2026-03-01');

INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K0+000-K1+000', 'roadbed', 'complete', '{"progress": 100}', '2026-03-15');

-- K1+000-K2+000 路基
INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K1+000-K2+000', 'roadbed', 'start', '{"task": "路基填筑", "duration_days": 30}', '2026-03-10');

INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K1+000-K2+000', 'roadbed', 'complete', '{"progress": 100}', '2026-03-25');

-- K2+000-K3+000 基层
INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K2+000-K3+000', 'pavement', 'start', '{"task": "基层摊铺", "duration_days": 20}', '2026-03-20');

INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K2+000-K3+000', 'pavement', 'complete', '{"progress": 100}', '2026-04-10');

-- K3+000-K4+000 面层
INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K3+000-K4+000', 'surface', 'start', '{"task": "面层施工", "duration_days": 15}', '2026-04-01');

INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('K3+000-K4+000', 'surface', 'delay', '{"reason": "雨天", "days": 3}', '2026-04-05');

-- 天气事件
INSERT INTO construction_events (entity_id, entity_type, event_type, event_data, occurred_at) 
VALUES ('WEATHER', 'environment', 'issue', '{"type": "rain", "severity": "medium"}', '2026-04-05');
