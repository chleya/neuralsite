# Initialize database tables
from api.deps import init_db

print("Creating database tables...")
init_db()
print("Done!")
