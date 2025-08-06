import os
from app import app
from models import db, create_sample_data, upgrade_all_users_to_full_access

# Ensure the database file is deleted before initialization
db_path = os.path.join(app.root_path, 'site.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted existing database file: {db_path}")
else:
    print(f"No existing database file found at: {db_path}")

with app.app_context():
    # Explicitly drop and create all tables to ensure schema is up-to-date
    db.drop_all()
    db.create_all()
    print("Database tables dropped and recreated.")
    
    create_sample_data()
    upgrade_all_users_to_full_access()
    print("Database initialized and sample data created successfully.")