# Test database connection
from api.deps import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check tables
    result = db.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name IN ('station_coordinate_mapping', 'engineering_entity')
    """)).fetchall()
    print('Tables:', [r[0] for r in result])
    
    # Check station data
    result = db.execute(text('SELECT COUNT(*) FROM station_coordinate_mapping')).fetchone()
    print('Station mapping count:', result[0])
    
    # Check entity data
    result = db.execute(text('SELECT COUNT(*) FROM engineering_entity')).fetchone()
    print('Entity count:', result[0])
    
    # Sample data
    result = db.execute(text('SELECT station, station_display, easting, northing FROM station_coordinate_mapping LIMIT 3')).fetchall()
    print('Sample stations:', result)
finally:
    db.close()
