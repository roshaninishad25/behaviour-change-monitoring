import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import get_connection

# 1. Load ML decision results
csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "decision_results.csv")
df = pd.read_csv(csv_path)
print(f"ML result records found: {len(df)}")

# 2. Connect to database
conn = get_connection()
cursor = conn.cursor()

# 3. Insert queries
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
    uid = str(row["UserID"])
    bci = None if pd.isna(row["BCI"]) else float(row["BCI"])
    b_state = str(row["Behavior_State"])
    a_flag = int(row["Anomaly_Flag"])
    a_score = float(row["Anomaly_Score"])
    rec = str(row["Recommendation"])
    prio = str(row["Priority"])

    cursor.execute(prediction_query, (uid, bci, b_state))
    cursor.execute(anomaly_query, (uid, a_flag, a_score))
    cursor.execute(recommendation_query, (uid, rec))
    cursor.execute(alert_query, (uid, prio))

conn.commit()
cursor.close()
conn.close()

print("ML decision results inserted successfully into database.")
