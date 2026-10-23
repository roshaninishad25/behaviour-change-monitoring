import os
import tempfile
# Ensure Matplotlib uses a writable cache directory
os.environ.setdefault('MPLCONFIGDIR', os.path.join(tempfile.gettempdir(), 'mpl_cache'))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
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
from datetime import datetime, timedelta, timezone
import os
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'

# B1 — Faculty invite code. Set FACULTY_INVITE_CODE in .env to a strong secret.
# Anyone who knows this code can register a faculty account.
# An empty string disables faculty self-registration.
FACULTY_INVITE_CODE = os.getenv('FACULTY_INVITE_CODE', '')

security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# B2 — Token creation
# --------------------------------------------------

def create_access_token(user_id: str, role: str) -> str:
    """Issue a signed JWT containing user_id (sub) and role. Expires in 8 hours."""
    if not JWT_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail='Authentication is not configured on the server.',
        )
    payload = {
        'sub': str(user_id),
        'role': str(role),
        'exp': datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# --------------------------------------------------
# B4 — Derive identity from the verified JWT
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates the Bearer token and returns the authenticated user dict.
    The user_id and role come exclusively from the signed JWT — the frontend
    cannot influence them by changing a URL parameter.

    Returns 401 when:
    - No token is supplied.
    - The token signature is invalid.
    - The token has expired.
    """
    if credentials is None or not JWT_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail='Authentication required.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = payload.get('sub')
        role = payload.get('role')
        if not user_id or not role:
            raise jwt.InvalidTokenError('Missing claims')
        return {'user_id': str(user_id), 'role': str(role)}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail='Your session has expired. Please log in again.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail='Invalid or expired token.',
            headers={'WWW-Authenticate': 'Bearer'},
        )


# --------------------------------------------------
# B5/B6 — Ownership and role checks
# --------------------------------------------------

def authorize_user_path(
    user_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    B5/B6 — Authorisation gate for per-student routes.

    Rules:
    - Faculty can read or write any student's data.
    - Students may only access their own data (JWT sub must match the URL param).
    - Returns 403 (not 401 or 404) so we do not reveal whether another user ID
      exists in the system.

    Changing the user_id in the URL will be rejected for students because
    the comparison is always against the JWT sub claim, not a user-supplied value.
    """
    role = current_user['role'].lower()
    if role == 'faculty':
        return current_user
    if role in ('student', 'user') and current_user['user_id'] == str(user_id):
        return current_user
    raise HTTPException(
        status_code=403,
        detail='You are not authorised to access this student record.',
    )


def require_faculty(current_user: dict = Depends(get_current_user)) -> dict:
    """B5 — Restricts an endpoint to faculty accounts only."""
    if current_user['role'].lower() != 'faculty':
        raise HTTPException(
            status_code=403,
            detail='Faculty access required.',
        )
    return current_user


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
# Authentication request models
# --------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class FacultyRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    invite_code: str  # B1 — Faculty registration requires a secure invite code


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --------------------------------------------------
# B3 — Password hashing utilities (PBKDF2-SHA256)
# --------------------------------------------------

PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a random salt.
    The stored format is: pbkdf2_sha256$<iterations>$<salt>$<hex_hash>
    Plaintext passwords are never logged or returned.
    """
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Re-derives the PBKDF2 key from the submitted password and compares it
    to the stored hash using a constant-time comparison to prevent timing attacks.
    Returns False (never raises) for any malformed hash.
    """
    try:
        algorithm, iterations, salt, stored_key = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return secrets.compare_digest(derived_key.hex(), stored_key)
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
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {"message": "Behavioural Change Monitoring API is running"}


# ==================================================
# B1/B2 — Authentication endpoints
# ==================================================

# --------------------------------------------------
# Student registration  (B1)
# --------------------------------------------------

@app.post("/auth/signup")
@app.post("/register")   # keep old path for backwards compatibility
def register_student(request: RegisterRequest):
    """
    B1 — Student self-registration.
    - Validates that the password is at least 8 characters.
    - Rejects duplicate email addresses.
    - Hashes the password before storing (B3).
    - Always assigns the role 'Student'; role cannot be chosen by the client.
    """
    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long.",
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Reject duplicate emails (case-insensitive)
        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (request.email,),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

        # Generate a unique 8-character user ID
        while True:
            user_id = secrets.token_hex(4).upper()
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s;",
                (user_id,),
            )
            if cursor.fetchone() is None:
                break

        password_hash = hash_password(request.password)

        cursor.execute(
            """
            INSERT INTO users (user_id, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                user_id,
                request.name.strip(),
                request.email,
                password_hash,
                "Student",   # Role is ALWAYS Student for self-registration
            ),
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
        "role": "Student",
    }


# --------------------------------------------------
# Faculty registration (B1) — invite-code protected
# --------------------------------------------------

@app.post("/auth/signup/faculty")
def register_faculty(request: FacultyRegisterRequest):
    """
    B1 — Faculty registration, gated by a server-side invite code.
    The invite code is stored in the FACULTY_INVITE_CODE environment variable.
    If FACULTY_INVITE_CODE is not set or is empty, faculty self-registration
    is disabled entirely.
    """
    if not FACULTY_INVITE_CODE:
        raise HTTPException(
            status_code=403,
            detail="Faculty self-registration is not enabled. Contact an administrator.",
        )

    # Constant-time comparison to prevent timing attacks on the invite code
    if not secrets.compare_digest(
        request.invite_code.encode(),
        FACULTY_INVITE_CODE.encode(),
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid invite code.",
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long.",
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (request.email,),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

        while True:
            user_id = secrets.token_hex(4).upper()
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s;",
                (user_id,),
            )
            if cursor.fetchone() is None:
                break

        password_hash = hash_password(request.password)

        cursor.execute(
            """
            INSERT INTO users (user_id, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                user_id,
                request.name.strip(),
                request.email,
                password_hash,
                "Faculty",
            ),
        )
        conn.commit()
        cursor.close()

    finally:
        conn.close()

    return {
        "message": "Faculty account created successfully.",
        "user_id": user_id,
        "name": request.name.strip(),
        "email": request.email,
        "role": "Faculty",
    }


# --------------------------------------------------
# Login  (B2)
# --------------------------------------------------

@app.post("/auth/login")
@app.post("/login")   # keep old path for backwards compatibility
def login_user(request: LoginRequest):
    """
    B2 — Verifies email + password and issues a signed JWT.
    - Uses a constant-error message for wrong email or password to prevent
      user-enumeration attacks.
    - The old 'User' role (imported data) is normalised to 'Student'.
    - Plaintext passwords are never logged or returned.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, password_hash, role
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (request.email,),
        )
        user = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    # B7 — Use the same error for unknown accounts and wrong passwords
    # to prevent user enumeration.
    if user is None or not verify_password(request.password, user[3]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    user_id = user[0]
    name = user[1]
    email = user[2]
    role = user[4]

    # Normalise legacy 'User' role to 'Student'
    if role.lower() == "user":
        role = "Student"

    return {
        "message": "Login successful.",
        "access_token": create_access_token(str(user_id), role),
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "name": name,
            "email": email,
            "role": role,
        },
    }


# --------------------------------------------------
# Current-user identity (B4)
# --------------------------------------------------

@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    B4 — Returns the identity derived from the verified JWT.
    The frontend can call this to restore session state without trusting
    a locally cached user object.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, role
            FROM users
            WHERE user_id = %s;
            """,
            (current_user["user_id"],),
        )
        user = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    role = user[3]
    if role.lower() == "user":
        role = "Student"

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": role,
    }


# ==================================================
# B5/B6 — Protected data endpoints
# ==================================================

# --------------------------------------------------
# Get user details
# --------------------------------------------------

@app.get("/users/{user_id}")
def get_user(user_id: str, current_user: dict = Depends(authorize_user_path)):
    """
    B5/B6 — Returns public profile fields for the requested user.
    Students can only retrieve their own profile.
    Faculty can retrieve any student's profile.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, role
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3],
    }


# --------------------------------------------------
# Get behavioural records for a user
# --------------------------------------------------

@app.get("/behavior/{user_id}")
def get_behavior(user_id: str, current_user: dict = Depends(authorize_user_path)):
    """
    B5/B6 — Returns behaviour records owned by user_id.
    The authorize_user_path dependency enforces that a student can only
    request their own records. Changing the URL param returns 403.
    """
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
            (user_id,),
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
            "final_grade": row[14],
        }
        for row in records
    ]


# --------------------------------------------------
# Dashboard data for a user
# --------------------------------------------------

@app.get("/dashboard/{user_id}")
def get_dashboard(user_id: str, current_user: dict = Depends(authorize_user_path)):
    """
    B4/B5/B6 — Returns the dashboard for user_id.

    The authorize_user_path dependency verifies the JWT and checks that:
    - A student's JWT sub matches user_id exactly (prevents IDOR).
    - Faculty can view any student's dashboard.

    The database query uses the validated user_id from the URL parameter,
    which was already confirmed to match the JWT claim (or is a faculty request).
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # User details
        cursor.execute(
            """
            SELECT user_id, name, email, role
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,),
        )
        user = cursor.fetchone()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Latest prediction
        cursor.execute(
            """
            SELECT bci, behavior_state, predicted_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        prediction = cursor.fetchone()

        # Latest anomaly
        cursor.execute(
            """
            SELECT anomaly_flag, anomaly_score, detected_at
            FROM anomalies
            WHERE user_id = %s
            ORDER BY detected_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        anomaly = cursor.fetchone()

        # Latest recommendation
        cursor.execute(
            """
            SELECT recommendation, created_at
            FROM recommendations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        recommendation = cursor.fetchone()

        # Latest alert
        cursor.execute(
            """
            SELECT priority, created_at
            FROM alerts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,),
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
            "role": user[3],
        },
        "prediction": (
            {
                "bci": prediction[0],
                "behavior_state": prediction[1],
                "predicted_at": prediction[2],
            }
            if prediction
            else None
        ),
        "anomaly": (
            {
                "anomaly_flag": anomaly[0],
                "anomaly_score": anomaly[1],
                "detected_at": anomaly[2],
            }
            if anomaly
            else None
        ),
        "recommendation": (
            {
                "recommendation": recommendation[0],
                "created_at": recommendation[1],
            }
            if recommendation
            else None
        ),
        "alert": (
            {
                "priority": alert[0],
                "created_at": alert[1],
            }
            if alert
            else None
        ),
    }


# --------------------------------------------------
# Behaviour trend for a user
# --------------------------------------------------

@app.get("/trend/{user_id}")
def get_trend(user_id: str, current_user: dict = Depends(authorize_user_path)):
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
            (user_id,),
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
            "final_grade": row[12],
        }
        for row in records
    ]


# --------------------------------------------------
# Anomaly information for a user
# --------------------------------------------------

@app.get("/anomaly/{user_id}")
def get_anomaly(user_id: str, current_user: dict = Depends(authorize_user_path)):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT anomaly_flag, anomaly_score, detected_at
            FROM anomalies
            WHERE user_id = %s
            ORDER BY detected_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        anomaly = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    if anomaly is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly information not found",
        )

    return {
        "user_id": user_id,
        "anomaly_flag": anomaly[0],
        "anomaly_score": anomaly[1],
        "detected_at": anomaly[2],
    }


# --------------------------------------------------
# Behaviour prediction for a user
# --------------------------------------------------

@app.get("/predict/{user_id}")
def get_prediction(user_id: str, current_user: dict = Depends(authorize_user_path)):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bci, behavior_state, predicted_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        prediction = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "user_id": user_id,
        "bci": prediction[0],
        "behavior_state": prediction[1],
        "predicted_at": prediction[2],
    }


# --------------------------------------------------
# SHAP explanation for a user
# --------------------------------------------------

@app.get("/explanation/{user_id}")
def get_explanation(user_id: str, current_user: dict = Depends(authorize_user_path)):
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
            (user_id,),
        )
        records = cursor.fetchall()
        cursor.close()

    finally:
        conn.close()

    if len(records) < 7:
        return {
            "user_id": user_id,
            "behavior_state": None,
            "explanations": [],
        }

    # Convert database records to DataFrame
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
        "Sequence",
    ]

    df = pd.DataFrame(records, columns=columns)

    # Use only historical sequences 1–7
    historical = df[df["Sequence"] <= 7].copy()

    if len(historical) != 7:
        raise HTTPException(
            status_code=404,
            detail="Sequences 1 to 7 are required for explanation",
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
        "Active_Days",
    ]

    # Build the same 44 features used by the Random Forest
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
    X_user = X_user[feature_columns]   # preserve training feature order

    # Prediction
    prediction = rf_model.predict(X_user)[0]

    # SHAP values
    shap_values = shap_explainer.shap_values(X_user)
    class_index = list(rf_model.classes_).index(prediction)
    shap_array = np.asarray(shap_values)

    if shap_array.ndim == 3:
        values_for_class = shap_array[0, :, class_index]
    else:
        values_for_class = shap_array[:, class_index]

    # Select top 5 absolute SHAP values
    explanation_df = pd.DataFrame(
        {"feature": feature_columns, "shap_value": values_for_class}
    )
    explanation_df["absolute_shap"] = explanation_df["shap_value"].abs()
    explanation_df = (
        explanation_df.sort_values("absolute_shap", ascending=False).head(5)
    )

    explanations = [
        {"feature": row["feature"], "shap_value": float(row["shap_value"])}
        for _, row in explanation_df.iterrows()
    ]

    return {
        "user_id": user_id,
        "behavior_state": prediction,
        "explanations": explanations,
    }


# --------------------------------------------------
# Recommendation for a user
# --------------------------------------------------

@app.get("/recommendation/{user_id}")
def get_recommendation(user_id: str, current_user: dict = Depends(authorize_user_path)):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT recommendation, created_at
            FROM recommendations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        recommendation = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {
        "user_id": user_id,
        "recommendation": recommendation[0],
        "created_at": recommendation[1],
    }


# --------------------------------------------------
# Alert priority for a user
# --------------------------------------------------

@app.get("/alert/{user_id}")
def get_alert(user_id: str, current_user: dict = Depends(authorize_user_path)):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT priority, created_at
            FROM alerts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        alert = cursor.fetchone()
        cursor.close()

    finally:
        conn.close()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert information not found")

    return {
        "user_id": user_id,
        "priority": alert[0],
        "created_at": alert[1],
    }


# --------------------------------------------------
# New-user behaviour prediction (faculty only)
# --------------------------------------------------

@app.post("/predict")
def predict_new_user(
    request: PredictionRequest,
    current_user: dict = Depends(require_faculty),
):
    """
    B5 — Faculty-only endpoint for running a prediction on manually supplied data.
    A student attempting this route will receive 403.
    """
    if len(request.periods) != 7:
        raise HTTPException(
            status_code=400,
            detail="Exactly 7 behavioural periods are required.",
        )

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
            "Active_Days": period.active_days,
        }
        for period in request.periods
    ]

    df = pd.DataFrame(data)

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
        "Active_Days",
    ]

    feature_data = {}
    for column in behaviour_columns:
        values = df[column].astype(float)
        feature_data[f"{column}_mean"] = values.mean()
        feature_data[f"{column}_std"] = values.std(ddof=1)
        feature_data[f"{column}_recent"] = values.iloc[-1]
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        feature_data[f"{column}_trend"] = slope

    X_new_user = pd.DataFrame([feature_data])
    X_new_user = X_new_user[feature_columns]

    prediction = rf_model.predict(X_new_user)[0]
    behavior_state = str(prediction)

    X_anomaly = anomaly_scaler.transform(X_new_user)
    anomaly_flag = int(isolation_forest.predict(X_anomaly)[0])
    anomaly_score = float(abs(isolation_forest.decision_function(X_anomaly)[0]))

    anomaly_status = "Normal" if anomaly_flag == 1 else "Anomalous"

    # Alert priority rules
    if behavior_state == "Declining" and anomaly_flag == -1:
        priority = "High"
    elif behavior_state == "Declining" and anomaly_flag == 1:
        priority = "Medium"
    elif anomaly_flag == -1:
        priority = "Medium"
    else:
        priority = "Low"

    # Recommendation rules
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

    bci = None   # BCI requires Sequence 8 data

    return {
        "behavior_state": behavior_state,
        "bci": bci,
        "bci_status": "BCI becomes available when Sequence 8 is available.",
        "anomaly_flag": anomaly_flag,
        "anomaly_status": anomaly_status,
        "anomaly_score": anomaly_score,
        "alert_priority": priority,
        "recommendation": recommendation,
    }


# --------------------------------------------------
# Faculty — student monitoring list  (B5, faculty only)
# --------------------------------------------------

@app.get("/faculty/students")
def get_faculty_students(current_user: dict = Depends(require_faculty)):
    """
    B5 — Returns summary data for all students.
    Only faculty accounts (verified from JWT role) can call this endpoint.
    """
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
                SELECT bci, behavior_state, predicted_at
                FROM predictions
                WHERE user_id = u.user_id
                ORDER BY predicted_at DESC
                LIMIT 1
            ) p ON TRUE

            LEFT JOIN LATERAL (
                SELECT anomaly_flag, anomaly_score, detected_at
                FROM anomalies
                WHERE user_id = u.user_id
                ORDER BY detected_at DESC
                LIMIT 1
            ) a ON TRUE

            LEFT JOIN LATERAL (
                SELECT priority, created_at
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
            "priority": row[8],
        }
        for row in students
    ]


# --------------------------------------------------
# Create behaviour record  (B5, faculty only)
# --------------------------------------------------

@app.post("/behavior")
def create_behavior(
    record: BehaviourRecordCreate,
    current_user: dict = Depends(require_faculty),
):
    """
    B5 — Faculty-only endpoint to add a behaviour record for a student.
    A student attempting this route will receive 403.
    """
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Verify the target student exists
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = %s",
            (record.user_id,),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="User not found")

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
            ),
        )

        record_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Behaviour record created successfully",
            "record_id": record_id,
            "user_id": record.user_id,
            "sequence": record.sequence,
        }

    except HTTPException:
        raise

    except UniqueViolation:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="Behaviour record already exists for this user and sequence.",
        )

    except Exception:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create behaviour record.",
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
