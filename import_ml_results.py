import pandas as pd
import psycopg2

# -----------------------------
# 1. Load ML decision results
# -----------------------------
csv_path = r"D:\PRJ_221\data\processed\decision_results.csv"

df = pd.read_csv(csv_path)

print(f"ML result records found: {len(df)}")

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
# 3. Insert results
# -----------------------------
prediction_query = """
INSERT INTO predictions (
    user_id,
    bci,
    behavior_state
)
VALUES (%s, %s, %s);
"""

anomaly_query = """
INSERT INTO anomalies (
    user_id,
    anomaly_flag,
    anomaly_score
)
VALUES (%s, %s, %s);
"""

recommendation_query = """
INSERT INTO recommendations (
    user_id,
    recommendation
)
VALUES (%s, %s);
"""

alert_query = """
INSERT INTO alerts (
    user_id,
    priority
)
VALUES (%s, %s);
"""

for _, row in df.iterrows():

    user_id = str(row["UserID"])
    bci = float(row["BCI"])
    behavior_state = str(row["Behavior_State"])
    anomaly_flag = int(row["Anomaly_Flag"])
    anomaly_score = float(row["Anomaly_Score"])
    recommendation = str(row["Recommendation"])
    priority = str(row["Alert_Priority"])

    cursor.execute(
        prediction_query,
        (user_id, bci, behavior_state)
    )

    cursor.execute(
        anomaly_query,
        (user_id, anomaly_flag, anomaly_score)
    )

    cursor.execute(
        recommendation_query,
        (user_id, recommendation)
    )

    cursor.execute(
        alert_query,
        (user_id, priority)
    )

# -----------------------------
# 4. Save changes
# -----------------------------
conn.commit()

print("ML results imported successfully.")

# -----------------------------
# 5. Verify counts
# -----------------------------
for table in [
    "predictions",
    "anomalies",
    "recommendations",
    "alerts"
]:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"{table}: {count}")

cursor.close()
conn.close()