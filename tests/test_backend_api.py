import unittest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from backend.app.main import (
    app,
    hash_password,
    verify_password,
    create_access_token,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)
import jwt


class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ----------------------------------------------------
    # B3: Password Hashing & Verification Tests
    # ----------------------------------------------------
    def test_password_hashing_and_verification(self):
        """E1.1: Verify PBKDF2-SHA256 password hashing and constant-time verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Check format
        parts = hashed.split("$")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2_sha256")
        self.assertEqual(parts[1], "310000")

        # Verify correct password succeeds
        self.assertTrue(verify_password(password, hashed))

        # Verify wrong password fails
        self.assertFalse(verify_password("WrongPassword123!", hashed))
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(password, "invalid$format"))

    # ----------------------------------------------------
    # B2/B4: Token Handling & Identity Derivation Tests
    # ----------------------------------------------------
    def test_jwt_generation_and_decoding(self):
        """E1.2: Verify JWT access token generation and claims payload."""
        token = create_access_token(user_id="TEST0001", role="Student")
        self.assertIsInstance(token, str)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload.get("sub"), "TEST0001")
        self.assertEqual(payload.get("role"), "Student")
        self.assertIn("exp", payload)

    def test_unauthenticated_request_rejected(self):
        """E1.3: Verify protected endpoints return 401 without Bearer token."""
        response = self.client.get("/dashboard/00050F0E")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json().get("detail", ""))

    def test_invalid_token_rejected(self):
        """E1.4: Verify malformed or forged JWT returns 401."""
        headers = {"Authorization": "Bearer invalid.token.value"}
        response = self.client.get("/dashboard/00050F0E", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid or expired token", response.json().get("detail", ""))

    # ----------------------------------------------------
    # B1: Signup & Registration Validation Tests
    # ----------------------------------------------------
    def test_signup_short_password_rejected(self):
        """E1.5: Verify registration rejects passwords shorter than 8 characters."""
        payload = {
            "name": "Test Student",
            "email": "shortpass@example.com",
            "password": "short",
        }
        response = self.client.post("/auth/signup", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 8 characters", response.json().get("detail", ""))

    @patch("backend.app.main.get_connection")
    def test_signup_duplicate_email_rejected(self, mock_get_conn):
        """E1.6: Verify registration rejects already-existing email address."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("EXISTING_ID",)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        payload = {
            "name": "Existing Student",
            "email": "existing@example.com",
            "password": "Password123!",
        }
        response = self.client.post("/auth/signup", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.json().get("detail", ""))

    def test_faculty_signup_without_invite_code(self):
        """E1.7: Verify faculty registration fails without proper invite code."""
        payload = {
            "name": "Fake Faculty",
            "email": "faculty@example.com",
            "password": "FacultyPassword123!",
            "invite_code": "wrong_invite_code_123",
        }
        response = self.client.post("/auth/signup/faculty", json=payload)
        self.assertEqual(response.status_code, 403)

    # ----------------------------------------------------
    # B5/B6/C1/C2/C3: Authorization & IDOR Protection Tests
    # ----------------------------------------------------
    def test_student_cannot_access_other_student_dashboard(self):
        """E1.8: Anti-IDOR: Student A cannot access Student B's dashboard (returns 403)."""
        student_a_token = create_access_token(user_id="STU_AAA", role="Student")
        headers = {"Authorization": f"Bearer {student_a_token}"}

        # Attempt to access STU_BBB
        response = self.client.get("/dashboard/STU_BBB", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("not authorised", response.json().get("detail", ""))

    def test_student_cannot_access_faculty_endpoints(self):
        """E1.9: Role-RBAC: Student cannot access faculty monitoring list."""
        student_token = create_access_token(user_id="STU_AAA", role="Student")
        headers = {"Authorization": f"Bearer {student_token}"}

        response = self.client.get("/faculty/students", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Faculty access required", response.json().get("detail", ""))

    def test_student_cannot_post_batch_prediction(self):
        """E1.10: Role-RBAC: Student cannot call POST /predict."""
        student_token = create_access_token(user_id="STU_AAA", role="Student")
        headers = {"Authorization": f"Bearer {student_token}"}

        payload = {"periods": []}
        response = self.client.post("/predict", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)

    # ----------------------------------------------------
    # A4: Prediction Input Validation Tests
    # ----------------------------------------------------
    def test_predict_requires_exactly_7_periods(self):
        """E1.11: Prediction pipeline requires exactly 7 sequential periods."""
        faculty_token = create_access_token(user_id="FAC_001", role="Faculty")
        headers = {"Authorization": f"Bearer {faculty_token}"}

        # Send only 3 periods instead of 7
        sample_period = {
            "freq_course_view": 10.0,
            "freq_forum_consume": 5.0,
            "freq_forum_contribute": 1.0,
            "freq_lecture_view": 4.0,
            "regularity_course_view": 0.5,
            "regularity_lecture_view": 0.6,
            "regularity_forum_consume": 0.4,
            "regularity_forum_contribute": 0.3,
            "session_count": 15.0,
            "total_duration": 3600.0,
            "active_days": 3.0,
        }
        payload = {"periods": [sample_period] * 3}

        response = self.client.post("/predict", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Exactly 7 behavioural periods", response.json().get("detail", ""))

    def test_predict_full_pipeline_success(self):
        """E1.12: Prediction pipeline returns full prediction payload with 7 periods."""
        faculty_token = create_access_token(user_id="FAC_001", role="Faculty")
        headers = {"Authorization": f"Bearer {faculty_token}"}

        sample_period = {
            "freq_course_view": 10.0,
            "freq_forum_consume": 5.0,
            "freq_forum_contribute": 1.0,
            "freq_lecture_view": 4.0,
            "regularity_course_view": 0.5,
            "regularity_lecture_view": 0.6,
            "regularity_forum_consume": 0.4,
            "regularity_forum_contribute": 0.3,
            "session_count": 15.0,
            "total_duration": 3600.0,
            "active_days": 3.0,
        }
        payload = {"periods": [sample_period] * 7}

        response = self.client.post("/predict", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("behavior_state", data)
        self.assertIn("anomaly_status", data)
        self.assertIn("alert_priority", data)
        self.assertIn("recommendation", data)


if __name__ == "__main__":
    unittest.main()
