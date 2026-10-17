import pandas as pd
import psycopg2

# -----------------------------
# 1. Load dataset
# -----------------------------
csv_path = r"D:\PRJ_221\data\raw\LongitudinalEngagement.csv"

df = pd.read_csv(csv_path)

# Get unique users
users = df["UserID"].drop_duplicates()

print(f"Unique users found: {len(users)}")

# -----------------------------
# 2. Connect to PostgreSQL
# -----------------------------
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="prj_221",
    user="postgres"
)

cursor = conn.cursor()

# -----------------------------
# 3. Insert users
# -----------------------------
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

# -----------------------------
# 4. Save changes
# -----------------------------
conn.commit()

print("Users imported successfully.")

# -----------------------------
# 5. Verify count
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM users;")
count = cursor.fetchone()[0]

print(f"Users currently in database: {count}")

cursor.close()
conn.close()