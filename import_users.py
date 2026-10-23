import os
import sys
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import get_connection

# 1. Load dataset
csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "LongitudinalEngagement.csv")
df = pd.read_csv(csv_path)

users = df["UserID"].drop_duplicates()
print(f"Unique users found: {len(users)}")

# 2. Connect to database
conn = get_connection()
cursor = conn.cursor()

# 3. Insert users
insert_query = """
INSERT INTO users (
    user_id,
    name,
    email,
    password_hash,
    role
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (user_id) DO NOTHING;
"""

for user_id in users:
    user_id = str(user_id)
    name = f"User_{user_id}"
    email = f"{user_id.lower()}@example.com"
    password_hash = "TEMPORARY_HASH"
    role = "User"

    cursor.execute(
        insert_query,
        (user_id, name, email, password_hash, role)
    )

conn.commit()
cursor.close()
conn.close()

print("Users inserted successfully into database.")
