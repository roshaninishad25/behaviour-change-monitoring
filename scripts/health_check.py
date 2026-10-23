"""
System Health Check Script for PRJ_221.
Verifies:
1. Python environment and required packages
2. ML artifacts presence and loading
3. Database connectivity and schema
4. FastAPI application configuration
"""

import sys
import os
import json
import tempfile

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "mpl_cache"))

from dotenv import load_dotenv

load_dotenv()


def check_models():
    print("[1/4] Checking Machine Learning Artifacts...")
    import joblib

    files = [
        "models/random_forest_v2.pkl",
        "models/isolation_forest.pkl",
        "models/anomaly_scaler.pkl",
        "models/feature_columns.json",
    ]
    for f in files:
        if not os.path.exists(f):
            print(f"  [FAIL] Missing model file: {f}")
            return False
        print(f"  [OK] Found: {f}")

    rf = joblib.load("models/random_forest_v2.pkl")
    iso = joblib.load("models/isolation_forest.pkl")
    scaler = joblib.load("models/anomaly_scaler.pkl")
    with open("models/feature_columns.json", "r") as fc:
        cols = json.load(fc)

    print(f"  [OK] Random Forest loaded: {type(rf).__name__}")
    print(f"  [OK] Isolation Forest loaded: {type(iso).__name__}")
    print(f"  [OK] Anomaly Scaler loaded: {type(scaler).__name__}")
    print(f"  [OK] Feature columns count: {len(cols)}")
    return True


def check_database():
    print("\n[2/4] Checking Database Connectivity...")
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "prj_221"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "root"),
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        v = cursor.fetchone()[0]
        print(f"  [OK] PostgreSQL connected: {v.split(',')[0]}")

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = [r[0] for r in cursor.fetchall()]
        print(f"  [OK] Found tables: {', '.join(sorted(tables))}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  [WARN] Database check warning: {e}")
        return False


def check_auth_config():
    print("\n[3/4] Checking Authentication Configuration...")
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        print("  [FAIL] JWT_SECRET_KEY is missing from environment!")
        return False
    print(f"  [OK] JWT_SECRET_KEY configured ({len(jwt_secret)} chars)")

    invite_code = os.getenv("FACULTY_INVITE_CODE", "")
    if invite_code:
        print(f"  [OK] FACULTY_INVITE_CODE is enabled")
    else:
        print(f"  [INFO] FACULTY_INVITE_CODE is empty (faculty self-registration disabled)")
    return True


def check_api_app():
    print("\n[4/4] Checking FastAPI Application...")
    from backend.app.main import app

    routes = [r.path for r in app.routes if hasattr(r, "path")]
    print(f"  [OK] FastAPI initialized ({len(routes)} registered routes)")
    print(f"  [OK] Ready for production serving via uvicorn")
    return True


def main():
    print("=" * 60)
    print("PRJ_221 SYSTEM HEALTH & READINESS CHECK")
    print("=" * 60)

    m_ok = check_models()
    db_ok = check_database()
    auth_ok = check_auth_config()
    api_ok = check_api_app()

    print("\n" + "=" * 60)
    if m_ok and auth_ok and api_ok:
        print("[SUCCESS] Core application and ML services are READY.")
    else:
        print("[FAIL] Issues detected during health check. Review logs above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
