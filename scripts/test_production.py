"""
PRJ_221 Live Production & Deployment Smoke Test Script.
Tests an active backend instance (local, staging, or production URL).
Usage:
    python scripts/test_production.py [TARGET_URL]
Example:
    python scripts/test_production.py http://127.0.0.1:8000
    python scripts/test_production.py https://api.yourdomain.com
"""

import sys
import requests


def run_smoke_test(base_url):
    print("=" * 60)
    print(f"PRJ_221 PRODUCTION SMOKE TEST: {base_url}")
    print("=" * 60)

    # 1. Health check / Root
    print("\n[1/6] Testing API Root...")
    try:
        r = requests.get(f"{base_url}/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print(f"  [OK] API is live: {r.json().get('message')}")
    except Exception as e:
        print(f"  [FAIL] Failed to reach API root: {e}")
        return False

    # 2. Student Authentication
    print("\n[2/6] Testing Student Authentication...")
    try:
        login_res = requests.post(
            f"{base_url}/auth/login",
            json={"email": "00050f0e@example.com", "password": "Student123!"},
            timeout=10,
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.status_code}"
        data = login_res.json()
        student_token = data.get("access_token")
        student_id = data.get("user", {}).get("user_id")
        assert student_token, "No access token in response"
        print(f"  [OK] Logged in student: {student_id} ({data['user']['name']})")
    except Exception as e:
        print(f"  [FAIL] Student login test failed: {e}")
        return False

    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Identity Verification (/auth/me)
    print("\n[3/6] Testing Identity Derivation (/auth/me)...")
    try:
        me_res = requests.get(f"{base_url}/auth/me", headers=student_headers, timeout=10)
        assert me_res.status_code == 200, f"Expected 200, got {me_res.status_code}"
        me_data = me_res.json()
        assert me_data["user_id"] == student_id, "User ID mismatch in /auth/me"
        print(f"  [OK] /auth/me returned correct identity: {me_data['name']} [{me_data['role']}]")
    except Exception as e:
        print(f"  [FAIL] /auth/me verification failed: {e}")
        return False

    # 4. Anti-IDOR Authorization Check
    print("\n[4/6] Testing Anti-IDOR Authorization Protection...")
    try:
        idor_res = requests.get(f"{base_url}/dashboard/FAKE_STUDENT_ID", headers=student_headers, timeout=10)
        assert idor_res.status_code == 403, f"Expected 403 Forbidden, got {idor_res.status_code}"
        print("  [OK] Cross-student access correctly blocked with 403 Forbidden")
    except Exception as e:
        print(f"  [FAIL] Anti-IDOR check failed: {e}")
        return False

    # 5. Role Boundary Check (Student blocked from Faculty route)
    print("\n[5/6] Testing Role RBAC Boundary Enforcement...")
    try:
        rbac_res = requests.get(f"{base_url}/faculty/students", headers=student_headers, timeout=10)
        assert rbac_res.status_code == 403, f"Expected 403, got {rbac_res.status_code}"
        print("  [OK] Student blocked from /faculty/students with 403 Forbidden")
    except Exception as e:
        print(f"  [FAIL] RBAC check failed: {e}")
        return False

    # 6. Faculty Authentication & Cohort Access
    print("\n[6/6] Testing Faculty Cohort Monitoring...")
    try:
        fac_login = requests.post(
            f"{base_url}/auth/login",
            json={"email": "testfaculty@example.com", "password": "Faculty123!"},
            timeout=10,
        )
        assert fac_login.status_code == 200, f"Faculty login failed: {fac_login.status_code}"
        fac_token = fac_login.json().get("access_token")
        fac_headers = {"Authorization": f"Bearer {fac_token}"}

        cohort_res = requests.get(f"{base_url}/faculty/students", headers=fac_headers, timeout=10)
        assert cohort_res.status_code == 200, f"Expected 200, got {cohort_res.status_code}"
        students = cohort_res.json()
        assert isinstance(students, list) and len(students) > 0, "No students returned in cohort"
        print(f"  [OK] Faculty successfully accessed cohort ({len(students)} students loaded)")
    except Exception as e:
        print(f"  [FAIL] Faculty cohort check failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] All 6 Production Smoke Tests Passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    success = run_smoke_test(target)
    sys.exit(0 if success else 1)
