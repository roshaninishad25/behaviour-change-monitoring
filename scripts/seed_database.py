"""
Unified Database Seeding Script for PRJ_221.
Runs:
1. User seeding from raw CSV
2. Behavioural records seeding (8 sequences per user)
3. Pre-calculated ML predictions, anomalies, recommendations, and alerts
"""

import sys
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(script_name):
    script_path = os.path.join(PROJECT_ROOT, script_name)
    if not os.path.exists(script_path):
        print(f"[SKIP] {script_name} does not exist.")
        return False
    print(f"\n--- Running {script_name} ---")
    ret = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
    if ret.returncode != 0:
        print(f"[FAIL] {script_name} exited with error code {ret.returncode}")
        return False
    print(f"[OK] {script_name} completed.")
    return True


def main():
    print("=" * 60)
    print("PRJ_221 DATABASE SEEDING WORKFLOW")
    print("=" * 60)

    # 1. Users
    if not run_script("import_users.py"):
        print("Failed on import_users.py")
        sys.exit(1)

    # 2. Behaviour Records
    if not run_script("import_behaviour.py"):
        print("Failed on import_behaviour.py")
        sys.exit(1)

    # 3. ML Results (Predictions, Anomalies, Recommendations, Alerts)
    if not run_script("import_ml_results.py"):
        print("Failed on import_ml_results.py")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] All database records seeded successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
