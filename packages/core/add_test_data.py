# Add test data for spatial API
from api.deps import SessionLocal
from sqlalchemy import text
import uuid

db = SessionLocal()

# Use a fixed test project ID
project_id = uuid.uuid4()

# Insert test engineering entities (without requiring projects table)
entities = [
    ('bridge', 'Test Bridge 1', 'B001', 200, 400, 'K0+200', 'in_progress'),
    ('bridge', 'Test Bridge 2', 'B002', 800, 1000, 'K0+800', 'not_started'),
    ('tunnel', 'Test Tunnel 1', 'T001', 500, 800, 'K0+500', 'in_progress'),
    ('culvert', 'Test Culvert 1', 'C001', 300, 300, 'K0+300', 'completed'),
]

for entity_type, name, code, start_station, end_station, display, status in entities:
    db.execute(text("""
        INSERT INTO engineering_entity 
        (entity_id, project_id, entity_type, entity_name, entity_code,
         start_station, end_station, station_display, construction_status)
        VALUES (:id, :project_id, :type, :name, :code, :start, :end, :display, :status)
    """), {
        'id': str(uuid.uuid4()),
        'project_id': str(project_id),
        'type': entity_type,
        'name': name,
        'code': code,
        'start': start_station,
        'end': end_station,
        'display': display,
        'status': status
    })

db.commit()
print('Added', len(entities), 'engineering entity records')

db.close()
