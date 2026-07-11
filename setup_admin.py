"""
Run this once to create your admin user
python setup_admin.py
"""

import psycopg2
from werkzeug.security import generate_password_hash

# === CONFIGURATION ===
# ⚠️ YOUR HARDCODED DATABASE URL (URL-encoded password: ? becomes %3F)
DATABASE_URL = 'postgresql://postgres.jslpmooinxnuwyfptrgn:shidow2024%3F@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'

ADMIN_USERNAME = 'shidow'
ADMIN_EMAIL = 'admin@shidowtours.com'
ADMIN_PASSWORD = 'shidowshadow?'

print("🔐 Connecting to database...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ Connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Create admins table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(200) NOT NULL,
        role VARCHAR(20) DEFAULT 'admin',
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT NOW(),
        last_login TIMESTAMP
    )
""")

# Hash the password
hashed_password = generate_password_hash(ADMIN_PASSWORD)
print(f"✅ Password hashed successfully")

# Insert admin user
cursor.execute("""
    INSERT INTO admins (username, email, password_hash, role, status)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
""", (ADMIN_USERNAME, ADMIN_EMAIL, hashed_password, 'admin', 'active'))

conn.commit()

# Check if created
cursor.execute("SELECT username, email, role FROM admins WHERE username = %s", (ADMIN_USERNAME,))
admin = cursor.fetchone()

if admin:
    print(f"\n✅ Admin user created successfully!")
    print(f"   Username: {admin[0]}")
    print(f"   Email: {admin[1]}")
    print(f"   Role: {admin[2]}")
    print(f"\n🔐 Password: {ADMIN_PASSWORD}")
else:
    print("\n⚠️  Admin user already exists or creation failed.")

cursor.close()
conn.close()