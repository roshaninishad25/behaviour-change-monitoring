import pandas as pd
import psycopg2

# -----------------------------
# 1. Load dataset
# -----------------------------
csv_path = r"D:\PRJ_221\data\raw\LongitudinalEngagement.csv"

df = pd.read_csv(csv_path)

print(f"Records found: {len(df)}")

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
# 3. Insert behaviour records
# -----------------------------
insert_query = """
INSERT INTO behaviour_records (
    user_id,
    course_id,
    sequence,
    freq_course_view,
    freq_forum_consume,
    freq_forum_contribute,
    freq_lecture_view,
    regularity_course_view,
    regularity_lecture_view,
    regularity_forum_consume,
    regularity_forum_contribute,
    session_count,
    total_duration,
    active_days,
    final_grade
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s
)
ON CONFLICT (user_id, sequence) DO NOTHING;
"""

for _, row in df.iterrows():

    cursor.execute(
        insert_query,
        (
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
            float(row["Final_Grade"])
        )
    )

# -----------------------------
# 4. Save changes
# -----------------------------
conn.commit()

print("Behaviour records imported successfully.")

# -----------------------------
# 5. Verify count
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM behaviour_records;")
count = cursor.fetchone()[0]

print(f"Behaviour records currently in database: {count}")

cursor.close()
conn.close()