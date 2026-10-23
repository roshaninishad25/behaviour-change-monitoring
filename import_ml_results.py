import os
import sys
import pandas as pd
from psycopg2.extras import execute_values

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import get_connection

csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "decision_results.csv")
df = pd.read_csv(csv_path)
print(f"ML result records to insert: {len(df)}")

conn = get_connection()
cursor = conn.cursor()

predictions = []
anomalies = []
recommendations = []
alerts = []

for _, row in df.iterrows():
    uid = str(row["UserID"])
    bci = None if pd.isna(row["BCI"]) else float(row["BCI"])
    b_state = str(row["Behavior_State"])
    a_flag = int(row["Anomaly_Flag"])
    a_score = float(row["Anomaly_Score"])
    rec = str(row["Recommendation"])
    prio = str(row["Alert_Priority"])

    predictions.append((uid, bci, b_state))
    anomalies.append((uid, a_flag, a_score))
    recommendations.append((uid, rec))
    alerts.append((uid, prio))

# Clear old results if re-seeding to keep clean 1 latest record per student
cursor.execute("TRUNCATE TABLE predictions, anomalies, recommendations, alerts RESTART IDENTITY CASCADE;")

execute_values(cursor, "INSERT INTO predictions (user_id, bci, behavior_state) VALUES %s", predictions)
execute_values(cursor, "INSERT INTO anomalies (user_id, anomaly_flag, anomaly_score) VALUES %s", anomalies)
execute_values(cursor, "INSERT INTO recommendations (user_id, recommendation) VALUES %s", recommendations)
execute_values(cursor, "INSERT INTO alerts (user_id, priority) VALUES %s", alerts)

conn.commit()
cursor.close()
conn.close()

print(f"[OK] Successfully inserted {len(df)} predictions, anomalies, recommendations, and alerts.")
