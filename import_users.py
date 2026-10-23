import os
import sys
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import get_connection
from backend.app.main import hash_password

# 1. Load dataset
csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "LongitudinalEngagement.csv")
df = pd.read_csv(csv_path)

users = df["UserID"].drop_duplicates()
print(f"Unique students in dataset: {len(users)}")

# 2. Connect to database
conn = get_connection()
cursor = conn.cursor()

# 3. Insert or update users
insert_query = """
INSERT INTO users (
    user_id,
    name,
    email,
    password_hash,
    role
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role;
"""

student_password_hash = hash_password("Student123!")
print("Generated PBKDF2 hash for student accounts.")

# Insert all 142 students from dataset
for user_id in users:
    user_id = str(user_id)
    name = f"Student {user_id}"
    email = f"{user_id.lower()}@example.com"
    role = "Student"

    cursor.execute(
        insert_query,
        (user_id, name, email, student_password_hash, role)
    )

# 4. Insert Default Faculty Account
faculty_password_hash = hash_password("Faculty123!")
cursor.execute(
    """
    INSERT INTO users (
        user_id,
        name,
        email,
        password_hash,
        role
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (user_id) DO UPDATE SET
        email = EXCLUDED.email,
        password_hash = EXCLUDED.password_hash,
        role = EXCLUDED.role;
    """,
    ("FACULTY01", "Faculty Administrator", "testfaculty@example.com", faculty_password_hash, "Faculty")
)

conn.commit()
cursor.close()
conn.close()

print("[OK] Successfully seeded 142 student accounts and 1 faculty account.")
