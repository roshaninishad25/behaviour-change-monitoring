import os
import sys
import pandas as pd
from psycopg2.extras import execute_values

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import get_connection

csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "LongitudinalEngagement.csv")
df = pd.read_csv(csv_path)
print(f"Records to insert: {len(df)}")

conn = get_connection()
cursor = conn.cursor()

records = []
for _, row in df.iterrows():
    records.append((
        str(row["UserID"]),
        str(row["CourseID"]),
        int(row["Sequence"]),
        int(row["Freq_Course_View"]),
        int(row["Freq_Forum_Consume"]),
        int(row["Freq_Forum_Contribute"]),
        int(row["Freq_Lecture_View"]),
        float(row["Regularity_Course_View"]),
        float(row["Regularity_Lecture_View"]),
        float(row["Regularity_Forum_Consume"]),
        float(row["Regularity_Forum_Contribute"]),
        int(row["Session_Count"]),
        int(row["Total_Duration"]),
        int(row["Active_Days"]),
        float(row["Final_Grade"]),
    ))

insert_query = """
INSERT INTO behaviour_records (
    user_id, course_id, sequence,
    freq_course_view, freq_forum_consume, freq_forum_contribute, freq_lecture_view,
    regularity_course_view, regularity_lecture_view, regularity_forum_consume, regularity_forum_contribute,
    session_count, total_duration, active_days, final_grade
)
VALUES %s
ON CONFLICT (user_id, sequence) DO UPDATE SET
    course_id = EXCLUDED.course_id,
    freq_course_view = EXCLUDED.freq_course_view,
    freq_forum_consume = EXCLUDED.freq_forum_consume,
    freq_forum_contribute = EXCLUDED.freq_forum_contribute,
    freq_lecture_view = EXCLUDED.freq_lecture_view,
    regularity_course_view = EXCLUDED.regularity_course_view,
    regularity_lecture_view = EXCLUDED.regularity_lecture_view,
    regularity_forum_consume = EXCLUDED.regularity_forum_consume,
    regularity_forum_contribute = EXCLUDED.regularity_forum_contribute,
    session_count = EXCLUDED.session_count,
    total_duration = EXCLUDED.total_duration,
    active_days = EXCLUDED.active_days,
    final_grade = EXCLUDED.final_grade;
"""

execute_values(cursor, insert_query, records, page_size=500)
conn.commit()
cursor.close()
conn.close()

print(f"[OK] Successfully inserted {len(records)} behaviour records.")
