
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from backend.app.schemas import BehaviourRecordCreate
from psycopg2.errors import UniqueViolation

import json
import joblib
import numpy as np
import pandas as pd
import shap
import hashlib
import secrets

from backend.app.database import get_connection

# --------------------------------------------------
# Load ML model and feature information
# --------------------------------------------------

RF_MODEL_PATH = "models/random_forest_v2.pkl"
FEATURE_COLUMNS_PATH = "models/feature_columns.json"

ISOLATION_MODEL_PATH = "models/isolation_forest.pkl"
ANOMALY_SCALER_PATH = "models/anomaly_scaler.pkl"

rf_model = joblib.load(RF_MODEL_PATH)

isolation_forest = joblib.load(ISOLATION_MODEL_PATH)
anomaly_scaler = joblib.load(ANOMALY_SCALER_PATH)

with open(FEATURE_COLUMNS_PATH, "r") as f:
    feature_columns = json.load(f)

shap_explainer = shap.TreeExplainer(rf_model)

# --------------------------------------------------
# Authentication models
# --------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --------------------------------------------------
# Password hashing utilities
# --------------------------------------------------

PBKDF2_ITERATIONS = 310000


def hash_password(password: str) -> str:

    salt = secrets.token_hex(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    )

    password_hash = derived_key.hex()

    return (
        f"pbkdf2_sha256$"
        f"{PBKDF2_ITERATIONS}$"
        f"{salt}$"
        f"{password_hash}"
    )


def verify_password(
    password: str,
    stored_hash: str
) -> bool:

    try:

        algorithm, iterations, salt, stored_key = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations)
        )

        return secrets.compare_digest(
            derived_key.hex(),
            stored_key
        )

    except (ValueError, TypeError):
        return False

    
# --------------------------------------------------
# New-user prediction request models
# --------------------------------------------------

class BehaviourPeriod(BaseModel):
    freq_course_view: float
    freq_forum_consume: float
    freq_forum_contribute: float
    freq_lecture_view: float

    regularity_course_view: float
    regularity_lecture_view: float
    regularity_forum_consume: float
    regularity_forum_contribute: float

    session_count: float
    total_duration: float
    active_days: float


class PredictionRequest(BaseModel):
    periods: List[BehaviourPeriod]

# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Behavioural Change Monitoring API",
    description="Backend API for the PRJ_221 Behavioural Change Monitoring Software",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Behavioural Change Monitoring API is running"
    }


# --------------------------------------------------
# Get user details
# --------------------------------------------------

@app.get("/users/{user_id}")
def get_user(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                role
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3]
    }


# --------------------------------------------------
# Get behavioural records for a user
# --------------------------------------------------

@app.get("/behavior/{user_id}")
def get_behavior(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                record_id,
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
            FROM behaviour_records
            WHERE user_id = %s
            ORDER BY sequence;
            """,
            (user_id,)
        )

        records = cursor.fetchall()

        cursor.close()

    finally:
        conn.close()

    if not records:
        return []

    return [
        {
            "record_id": row[0],
            "course_id": row[1],
            "sequence": row[2],
            "freq_course_view": row[3],
            "freq_forum_consume": row[4],
            "freq_forum_contribute": row[5],
            "freq_lecture_view": row[6],
            "regularity_course_view": row[7],
            "regularity_lecture_view": row[8],
            "regularity_forum_consume": row[9],
            "regularity_forum_contribute": row[10],
            "session_count": row[11],
            "total_duration": row[12],
            "active_days": row[13],
            "final_grade": row[14]
        }
        for row in records
    ]



# --------------------------------------------------
# Dashboard data for a user
# --------------------------------------------------

@app.get("/dashboard/{user_id}")
def get_dashboard(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # -----------------------------
        # User details
        # -----------------------------

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                role
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # -----------------------------
        # Latest prediction
        # -----------------------------

        cursor.execute(
            """
            SELECT
                bci,
                behavior_state,
                predicted_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        prediction = cursor.fetchone()

        # -----------------------------
        # Latest anomaly
        # -----------------------------

        cursor.execute(
            """
            SELECT
                anomaly_flag,
                anomaly_score,
                detected_at
            FROM anomalies
            WHERE user_id = %s
            ORDER BY detected_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        anomaly = cursor.fetchone()

        # -----------------------------
        # Latest recommendation
        # -----------------------------

        cursor.execute(
            """
            SELECT
                recommendation,
                created_at
            FROM recommendations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        recommendation = cursor.fetchone()

        # -----------------------------
        # Latest alert
        # -----------------------------

        cursor.execute(
            """
            SELECT
                priority,
                created_at
            FROM alerts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        alert = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    return {
        "user": {
            "user_id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3]
        },

        "prediction": (
            {
                "bci": prediction[0],
                "behavior_state": prediction[1],
                "predicted_at": prediction[2]
            }
            if prediction
            else None
        ),

        "anomaly": (
            {
                "anomaly_flag": anomaly[0],
                "anomaly_score": anomaly[1],
                "detected_at": anomaly[2]
            }
            if anomaly
            else None
        ),

        "recommendation": (
            {
                "recommendation": recommendation[0],
                "created_at": recommendation[1]
            }
            if recommendation
            else None
        ),

        "alert": (
            {
                "priority": alert[0],
                "created_at": alert[1]
            }
            if alert
            else None
        )
    }

    # --------------------------------------------------
# Behaviour trend for a user
# --------------------------------------------------

@app.get("/trend/{user_id}")
def get_trend(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
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
            FROM behaviour_records
            WHERE user_id = %s
            ORDER BY sequence;
            """,
            (user_id,)
        )

        records = cursor.fetchall()

        cursor.close()

    finally:
        conn.close()

    if not records:
        return []

    return [
        {
            "sequence": row[0],
            "freq_course_view": row[1],
            "freq_forum_consume": row[2],
            "freq_forum_contribute": row[3],
            "freq_lecture_view": row[4],
            "regularity_course_view": row[5],
            "regularity_lecture_view": row[6],
            "regularity_forum_consume": row[7],
            "regularity_forum_contribute": row[8],
            "session_count": row[9],
            "total_duration": row[10],
            "active_days": row[11],
            "final_grade": row[12]
        }
        for row in records
    ]

# --------------------------------------------------
# Anomaly information for a user
# --------------------------------------------------

@app.get("/anomaly/{user_id}")
def get_anomaly(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                anomaly_flag,
                anomaly_score,
                detected_at
            FROM anomalies
            WHERE user_id = %s
            ORDER BY detected_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        anomaly = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if anomaly is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly information not found"
        )

    return {
        "user_id": user_id,
        "anomaly_flag": anomaly[0],
        "anomaly_score": anomaly[1],
        "detected_at": anomaly[2]
    }

# --------------------------------------------------
# Behaviour prediction for a user
# --------------------------------------------------

@app.get("/predict/{user_id}")
def get_prediction(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                bci,
                behavior_state,
                predicted_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        prediction = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    return {
        "user_id": user_id,
        "bci": prediction[0],
        "behavior_state": prediction[1],
        "predicted_at": prediction[2]
    }

# --------------------------------------------------
# SHAP explanation for a user
# --------------------------------------------------

@app.get("/explanation/{user_id}")
def get_explanation(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
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
                sequence
            FROM behaviour_records
            WHERE user_id = %s
            ORDER BY sequence;
            """,
            (user_id,)
        )

        records = cursor.fetchall()

        cursor.close()

    finally:
        conn.close()

    if len(records) < 7:
        return {
            "user_id": user_id,
            "behavior_state": None,
            "explanations": []
        }

    # ----------------------------------------------
    # Convert database records to DataFrame
    # ----------------------------------------------

    columns = [
        "Freq_Course_View",
        "Freq_Forum_Consume",
        "Freq_Forum_Contribute",
        "Freq_Lecture_View",
        "Regularity_Course_View",
        "Regularity_Lecture_View",
        "Regularity_Forum_Consume",
        "Regularity_Forum_Contribute",
        "Session_Count",
        "Total_Duration",
        "Active_Days",
        "Sequence"
    ]

    df = pd.DataFrame(records, columns=columns)

    # Use only historical sequences 1–7
    historical = df[df["Sequence"] <= 7].copy()

    if len(historical) != 7:
        raise HTTPException(
            status_code=404,
            detail="Sequences 1 to 7 are required for explanation"
        )

    behaviour_columns = [
        "Freq_Course_View",
        "Freq_Forum_Consume",
        "Freq_Forum_Contribute",
        "Freq_Lecture_View",
        "Regularity_Course_View",
        "Regularity_Lecture_View",
        "Regularity_Forum_Consume",
        "Regularity_Forum_Contribute",
        "Session_Count",
        "Total_Duration",
        "Active_Days"
    ]

    # ----------------------------------------------
    # Build the same 44 features used by RF
    # ----------------------------------------------

    feature_data = {}

    for column in behaviour_columns:

        values = historical[column].astype(float)

        feature_data[f"{column}_mean"] = values.mean()
        feature_data[f"{column}_std"] = values.std(ddof=1)
        feature_data[f"{column}_recent"] = values.iloc[-1]

        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        feature_data[f"{column}_trend"] = slope

    X_user = pd.DataFrame([feature_data])

    # Make absolutely sure the feature order matches training
    X_user = X_user[feature_columns]

    # ----------------------------------------------
    # Prediction
    # ----------------------------------------------

    prediction = rf_model.predict(X_user)[0]

    # ----------------------------------------------
    # SHAP values
    # ----------------------------------------------

    shap_values = shap_explainer.shap_values(X_user)

    class_index = list(rf_model.classes_).index(prediction)

    shap_array = np.asarray(shap_values)

    if shap_array.ndim == 3:
        values_for_class = shap_array[0, :, class_index]
    else:
        values_for_class = shap_array[:, class_index]

    # ----------------------------------------------
    # Select top 5 absolute SHAP values
    # ----------------------------------------------

    explanation_df = pd.DataFrame({
        "feature": feature_columns,
        "shap_value": values_for_class
    })

    explanation_df["absolute_shap"] = explanation_df["shap_value"].abs()

    explanation_df = (
        explanation_df
        .sort_values("absolute_shap", ascending=False)
        .head(5)
    )

    explanations = []

    for _, row in explanation_df.iterrows():

        explanations.append({
            "feature": row["feature"],
            "shap_value": float(row["shap_value"])
        })

    return {
        "user_id": user_id,
        "behavior_state": prediction,
        "explanations": explanations
    }

# --------------------------------------------------
# Recommendation for a user
# --------------------------------------------------

@app.get("/recommendation/{user_id}")
def get_recommendation(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                recommendation,
                created_at
            FROM recommendations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        recommendation = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    return {
        "user_id": user_id,
        "recommendation": recommendation[0],
        "created_at": recommendation[1]
    }


# --------------------------------------------------
# Alert priority for a user
# --------------------------------------------------

@app.get("/alert/{user_id}")
def get_alert(user_id: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                priority,
                created_at
            FROM alerts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,)
        )

        alert = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert information not found"
        )

    return {
        "user_id": user_id,
        "priority": alert[0],
        "created_at": alert[1]
    }


# --------------------------------------------------
# New-user behaviour prediction
# --------------------------------------------------

@app.post("/predict")
def predict_new_user(request: PredictionRequest):

    # --------------------------------------------------
    # Validate number of behavioural periods
    # --------------------------------------------------

    if len(request.periods) != 7:
        raise HTTPException(
            status_code=400,
            detail="Exactly 7 behavioural periods are required."
        )

    # --------------------------------------------------
    # Convert request data into DataFrame
    # --------------------------------------------------

    data = [
        {
            "Freq_Course_View": period.freq_course_view,
            "Freq_Forum_Consume": period.freq_forum_consume,
            "Freq_Forum_Contribute": period.freq_forum_contribute,
            "Freq_Lecture_View": period.freq_lecture_view,

            "Regularity_Course_View": period.regularity_course_view,
            "Regularity_Lecture_View": period.regularity_lecture_view,
            "Regularity_Forum_Consume": period.regularity_forum_consume,
            "Regularity_Forum_Contribute": period.regularity_forum_contribute,

            "Session_Count": period.session_count,
            "Total_Duration": period.total_duration,
            "Active_Days": period.active_days
        }
        for period in request.periods
    ]

    df = pd.DataFrame(data)

    # --------------------------------------------------
    # Behaviour columns used by the ML pipeline
    # --------------------------------------------------

    behaviour_columns = [
        "Freq_Course_View",
        "Freq_Forum_Consume",
        "Freq_Forum_Contribute",
        "Freq_Lecture_View",
        "Regularity_Course_View",
        "Regularity_Lecture_View",
        "Regularity_Forum_Consume",
        "Regularity_Forum_Contribute",
        "Session_Count",
        "Total_Duration",
        "Active_Days"
    ]

    # --------------------------------------------------
    # Build the exact 44 features used during training
    # --------------------------------------------------

    feature_data = {}

    for column in behaviour_columns:

        values = df[column].astype(float)

        # Mean
        feature_data[f"{column}_mean"] = values.mean()

        # Standard deviation
        feature_data[f"{column}_std"] = values.std(ddof=1)

        # Most recent value
        feature_data[f"{column}_recent"] = values.iloc[-1]

        # Linear trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        feature_data[f"{column}_trend"] = slope

    # --------------------------------------------------
    # Create model input
    # --------------------------------------------------

    X_new_user = pd.DataFrame([feature_data])

    # Preserve exact training feature order
    X_new_user = X_new_user[feature_columns]

    # --------------------------------------------------
    # Random Forest prediction
    # --------------------------------------------------

    prediction = rf_model.predict(X_new_user)[0]
    behavior_state = str(prediction)

    # --------------------------------------------------
    # Isolation Forest anomaly detection
    # --------------------------------------------------

    X_anomaly = anomaly_scaler.transform(X_new_user)

    anomaly_flag = int(
        isolation_forest.predict(X_anomaly)[0]
    )

    anomaly_score = float(
    abs(isolation_forest.decision_function(X_anomaly)[0])
)
    # Isolation Forest:
    #  1  = normal
    # -1  = anomalous

    anomaly_status = (
        "Normal"
        if anomaly_flag == 1
        else "Anomalous"
    )

    # --------------------------------------------------
    # Alert priority
    # --------------------------------------------------

    if behavior_state == "Declining" and anomaly_flag == -1:
        priority = "High"

    elif behavior_state == "Declining" and anomaly_flag == 1:
        priority = "Medium"

    elif anomaly_flag == -1:
        priority = "Medium"

    else:
        priority = "Low"

    # --------------------------------------------------
    # Recommendation
    # --------------------------------------------------

    if behavior_state == "Improving" and anomaly_flag == 1:

        recommendation = (
            "Behaviour is improving. "
            "Continue the current positive pattern."
        )

    elif behavior_state == "Stable" and anomaly_flag == 1:

        recommendation = (
            "Behaviour is stable. "
            "Maintain the current pattern and continue monitoring."
        )

    elif behavior_state == "Stable" and anomaly_flag == -1:

        recommendation = (
            "Behaviour is stable but unusual. "
            "Review recent activity."
        )

    elif behavior_state == "Declining" and anomaly_flag == 1:

        recommendation = (
            "Behaviour is declining. "
            "Monitor recent activity and consider appropriate support."
        )

    elif behavior_state == "Declining" and anomaly_flag == -1:

        recommendation = (
            "Behaviour is declining and unusual. "
            "Timely review and support may be appropriate."
        )

    else:

        recommendation = (
            "Behaviour pattern has been detected. "
            "Continue monitoring recent activity."
        )

    # --------------------------------------------------
    # BCI
    # --------------------------------------------------
    # The project's original BCI requires the change
    # from Sequence 1 to Sequence 8.
    #
    # The current prediction uses Sequences 1–7,
    # so we do not calculate a substitute BCI here.

    bci = None

    # --------------------------------------------------
    # Return complete prediction result
    # --------------------------------------------------

    return {
        "behavior_state": behavior_state,

        "bci": bci,
        "bci_status": (
            "BCI becomes available when Sequence 8 "
            "is available."
        ),

        "anomaly_flag": anomaly_flag,
        "anomaly_status": anomaly_status,
        "anomaly_score": anomaly_score,

        "alert_priority": priority,

        "recommendation": recommendation
    }




# --------------------------------------------------
# Faculty - student monitoring list
# --------------------------------------------------

@app.get("/faculty/students")
def get_faculty_students():

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.user_id,
                u.name,
                u.email,
                u.role,

                p.bci,
                p.behavior_state,

                a.anomaly_flag,
                a.anomaly_score,

                al.priority

            FROM users u

            LEFT JOIN LATERAL (
                SELECT
                    bci,
                    behavior_state,
                    predicted_at
                FROM predictions
                WHERE user_id = u.user_id
                ORDER BY predicted_at DESC
                LIMIT 1
            ) p ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    anomaly_flag,
                    anomaly_score,
                    detected_at
                FROM anomalies
                WHERE user_id = u.user_id
                ORDER BY detected_at DESC
                LIMIT 1
            ) a ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    priority,
                    created_at
                FROM alerts
                WHERE user_id = u.user_id
                ORDER BY created_at DESC
                LIMIT 1
            ) al ON TRUE

            WHERE LOWER(u.role) IN ('user', 'student')

            ORDER BY u.name;
            """
        )

        students = cursor.fetchall()

        cursor.close()

    finally:
        conn.close()

    return [
        {
            "user_id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[3],
            "bci": row[4],
            "behavior_state": row[5],
            "anomaly_flag": row[6],
            "anomaly_score": row[7],
            "priority": row[8]
        }
        for row in students
    ]


# --------------------------------------------------
# Student registration
# --------------------------------------------------

@app.post("/register")
def register_student(request: RegisterRequest):

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters."
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Check whether email already exists
        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (request.email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists."
            )

        # Generate unique 8-character user ID
        while True:

            user_id = secrets.token_hex(4).upper()

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE user_id = %s;
                """,
                (user_id,)
            )

            if cursor.fetchone() is None:
                break

        password_hash = hash_password(
            request.password
        )

        cursor.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                email,
                password_hash,
                role
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                user_id,
                request.name.strip(),
                request.email,
                password_hash,
                "Student"
            )
        )

        conn.commit()

        cursor.close()

    finally:
        conn.close()

    return {
        "message": "Student account created successfully.",
        "user_id": user_id,
        "name": request.name.strip(),
        "email": request.email,
        "role": "Student"
    }

# --------------------------------------------------
# User login
# --------------------------------------------------

@app.post("/login")
def login_user(request: LoginRequest):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                password_hash,
                role
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (request.email,)
        )

        user = cursor.fetchone()

        cursor.close()

    finally:
        conn.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    user_id = user[0]
    name = user[1]
    email = user[2]
    password_hash = user[3]
    role = user[4]

    if not verify_password(
        request.password,
        password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # Treat the old imported "User" role as a student
    if role.lower() == "user":
        role = "Student"

    return {
        "message": "Login successful.",
        "user": {
            "user_id": user_id,
            "name": name,
            "email": email,
            "role": role
        }
    }


@app.post("/behavior")
def create_behavior(record: BehaviourRecordCreate):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Check that the user exists
        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = %s
            """,
            (record.user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Insert behaviour record
        cursor.execute(
            """
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
            RETURNING record_id
            """,
            (
                record.user_id,
                record.course_id,
                record.sequence,
                record.freq_course_view,
                record.freq_forum_consume,
                record.freq_forum_contribute,
                record.freq_lecture_view,
                record.regularity_course_view,
                record.regularity_lecture_view,
                record.regularity_forum_consume,
                record.regularity_forum_contribute,
                record.session_count,
                record.total_duration,
                record.active_days,
                record.final_grade,
            )
        )

        record_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Behaviour record created successfully",
            "record_id": record_id,
            "user_id": record.user_id,
            "sequence": record.sequence
        }

    except HTTPException:
        raise

    except UniqueViolation:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="Behaviour record already exists for this user and sequence."
        )

    except Exception as e:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create behaviour record."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()