
from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd()
MAIN = ROOT / "backend" / "app" / "main.py"
AUTH = ROOT / "frontend" / "src" / "AuthPage.jsx"
APP = ROOT / "frontend" / "src" / "App.jsx"
API = ROOT / "frontend" / "src" / "api.js"

FRONTEND_FILES = [
    APP,
    ROOT / "frontend" / "src" / "FacultyOverview.jsx",
    ROOT / "frontend" / "src" / "FacultyDashboard.jsx",
    ROOT / "frontend" / "src" / "FacultyStudentDetails.jsx",
    ROOT / "frontend" / "src" / "NewPredictionPage.jsx",
]

USER_ROUTES = [
    "get_user",
    "get_behavior",
    "get_dashboard",
    "get_trend",
    "get_anomaly",
    "get_prediction",
    "get_explanation",
    "get_recommendation",
    "get_alert",
]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def replace_once(source, pattern, replacement, label):
    updated, count = re.subn(
    pattern, replacement, source, count=1, flags=re.DOTALL
)
    require(count == 1, f"Expected exactly one match for: {label}")
    return updated


def main():
    require(ROOT.name == "PRJ_221", "Run this script from D:\\PRJ_221.")

    targets = [MAIN, AUTH, *FRONTEND_FILES]
    for path in targets:
        require(path.is_file(), f"Required file not found: {path}")

    require(not API.exists(), "frontend/src/api.js already exists; stopping safely.")

    env_path = ROOT / ".env"
    require(env_path.is_file(), ".env was not found.")
    env_text = env_path.read_text(encoding="utf-8")
    require(
        re.search(r"(?m)^JWT_SECRET_KEY\s*=\s*\S+", env_text),
        "JWT_SECRET_KEY is missing or empty in .env. Add a strong random secret first.",
    )

    try:
        import jwt
        import dotenv
    except ImportError as exc:
        raise RuntimeError(
            f"Missing dependency: {exc.name}. Install it with "
            "'python -m pip install PyJWT python-dotenv' and rerun."
        )

    main_source = MAIN.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")
    app_source = APP.read_text(encoding="utf-8")
    frontend_sources = {
        path: path.read_text(encoding="utf-8")
        for path in FRONTEND_FILES
    }

    require(
        "def create_access_token" not in main_source
        and "Depends(authorize_user_path)" not in main_source,
        "JWT changes appear to have already been applied. No files were changed.",
    )
    require("onLogin(data.user);" in auth_source, "AuthPage login callback differs.")
    require(
        'localStorage.setItem(\n      "prj221_user"' in app_source
        or '"prj221_user"' in app_source,
        "Could not find the expected user-storage code in App.jsx.",
    )

    # Prepare backend changes in memory.
    main_source = replace_once(
        main_source,
        r"from fastapi import FastAPI, HTTPException",
        "from fastapi import FastAPI, HTTPException, Depends\n"
        "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials",
        "FastAPI imports",
    )

    main_source = replace_once(
        main_source,
        r"from backend\.app\.database import get_connection",
        "from backend.app.database import get_connection\n"
        "from datetime import datetime, timedelta, timezone\n"
        "import os\n"
        "import jwt\n"
        "from dotenv import load_dotenv\n\n"
        "load_dotenv()\n\n"
        "JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')\n"
        "JWT_ALGORITHM = 'HS256'\n"
        "security = HTTPBearer(auto_error=False)\n\n"
        "def create_access_token(user_id: str, role: str):\n"
        "    if not JWT_SECRET_KEY:\n"
        "        raise HTTPException(status_code=500, detail='Authentication is not configured.')\n"
        "    payload = {\n"
        "        'sub': str(user_id),\n"
        "        'role': str(role),\n"
        "        'exp': datetime.now(timezone.utc) + timedelta(hours=8),\n"
        "    }\n"
        "    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)\n\n"
        "def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):\n"
        "    if credentials is None or not JWT_SECRET_KEY:\n"
        "        raise HTTPException(status_code=401, detail='Authentication required.', "
        "headers={'WWW-Authenticate': 'Bearer'})\n"
        "    try:\n"
        "        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, "
        "algorithms=[JWT_ALGORITHM])\n"
        "        user_id = payload.get('sub')\n"
        "        role = payload.get('role')\n"
        "        if not user_id or not role:\n"
        "            raise jwt.InvalidTokenError('Missing user or role')\n"
        "        return {'user_id': str(user_id), 'role': str(role)}\n"
        "    except jwt.InvalidTokenError:\n"
        "        raise HTTPException(status_code=401, detail='Invalid or expired token.', "
        "headers={'WWW-Authenticate': 'Bearer'})\n\n"
        "def authorize_user_path(user_id: str, current_user: dict = Depends(get_current_user)):\n"
        "    role = current_user['role'].lower()\n"
        "    if role == 'faculty':\n"
        "        return current_user\n"
        "    if role in ('student', 'user') and current_user['user_id'] == str(user_id):\n"
        "        return current_user\n"
        "    raise HTTPException(status_code=403, detail='You cannot access this student record.')\n\n"
        "def require_faculty(current_user: dict = Depends(get_current_user)):\n"
        "    if current_user['role'].lower() != 'faculty':\n"
        "        raise HTTPException(status_code=403, detail='Faculty access required.')\n"
        "    return current_user\n",
        "database import and JWT helpers",
    )

    for name in USER_ROUTES:
        main_source = replace_once(
            main_source,
            rf"def {name}\(user_id: str\):",
            f"def {name}(user_id: str, current_user: dict = Depends(authorize_user_path)):",
            f"protect {name}",
        )

    main_source = replace_once(
        main_source,
        r"def get_faculty_students\(\):",
        "def get_faculty_students(current_user: dict = Depends(require_faculty)):",
        "protect faculty student list",
    )

    main_source = replace_once(
        main_source,
        r"def predict_new_user\(request: PredictionRequest\):",
        "def predict_new_user(request: PredictionRequest, "
        "current_user: dict = Depends(require_faculty)):",
        "protect manual prediction",
    )

    main_source = replace_once(
        main_source,
        r"def create_behavior\(record: BehaviourRecordCreate\):",
        "def create_behavior(record: BehaviourRecordCreate, "
        "current_user: dict = Depends(require_faculty)):",
        "protect behavior creation",
    )

    main_source = replace_once(
        main_source,
        r'"message": "Login successful\.",',
        '"message": "Login successful.",\n'
        '        "access_token": create_access_token(str(user_id), role),\n'
        '        "token_type": "bearer",',
        "return JWT from login",
    )

    # Update AuthPage: only log in automatically when a token is returned.
    auth_source = replace_once(
        auth_source,
        r"onLogin\(data\.user\);",
        "if (data.user && data.access_token) {\n"
        "          onLogin(data.user, data.access_token);\n"
        "        }",
        "pass token from AuthPage",
    )

    # Require both a saved user and a token to restore a session.
    app_source = replace_once(
        app_source,
        r'const savedUser = localStorage\.getItem\("prj221_user"\);\s*'
        r"return savedUser \? JSON\.parse\(savedUser\) : null;",
        'const savedUser = localStorage.getItem("prj221_user");\n'
        '      const savedToken = localStorage.getItem("prj221_token");\n'
        "      return savedUser && savedToken ? JSON.parse(savedUser) : null;",
        "restore authenticated session",
    )

    app_source = replace_once(
        app_source,
        r"const handleLogin = \(user\) => \{.*?\n  \};",
        'const handleLogin = (user, token) => {\n'
        '    localStorage.setItem("prj221_user", JSON.stringify(user));\n'
        '    localStorage.setItem("prj221_token", token);\n'
        "    setCurrentUser(user);\n"
        "  };",
        "save token on login",
    )

    app_source = replace_once(
        app_source,
        r"const handleLogout = \(\) => \{.*?\n  \};",
        'const handleLogout = () => {\n'
        '    localStorage.removeItem("prj221_user");\n'
        '    localStorage.removeItem("prj221_token");\n'
        "    setCurrentUser(null);\n"
        "  };",
        "clear token on logout",
    )

    # Add authenticated fetch calls to every protected frontend API caller.
    updated_frontend = {}
    for path, source in frontend_sources.items():
        require("fetch(" in source, f"No fetch( call found in {path.name}; stopping safely.")
        source = source.replace("fetch(", "apiFetch(")
        source = 'import { apiFetch } from "./api";\n' + source
        updated_frontend[path] = source

    api_source = """export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("prj221_token");
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, { ...options, headers });
}
"""

    # Back up the exact pre-patch files before writing any changes.
    backup_dir = ROOT / "backups" / "pre-jwt-patch"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in [MAIN, AUTH, *FRONTEND_FILES]:
        shutil.copy2(path, backup_dir / path.name)

    # All pattern checks have passed. Now write the prepared changes.
    MAIN.write_text(main_source, encoding="utf-8")
    AUTH.write_text(auth_source, encoding="utf-8")
    APP.write_text(updated_frontend[APP], encoding="utf-8")

    for path, source in updated_frontend.items():
        if path != APP:
            path.write_text(source, encoding="utf-8")

    API.write_text(api_source, encoding="utf-8")

    print("JWT patch applied.")
    print(f"Safety backups: {backup_dir}")
    print("Changed backend routes:")
    print("  - Student-owned routes: JWT required; students restricted to their own user_id.")
    print("  - Faculty student list, manual prediction, behavior creation: faculty only.")
    print("  - Login returns an 8-hour access token.")
    print("Frontend token storage and authenticated API calls have been updated.")
    print("Next: run the validation and tests before using the app.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PATCH ABORTED: {exc}")
        print("No source files were written by this run.")
        sys.exit(1)
