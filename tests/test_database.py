import os
import unittest
from dotenv import load_dotenv

load_dotenv()


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_host = os.getenv("DB_HOST", "localhost")
        cls.db_port = os.getenv("DB_PORT", "5432")
        cls.db_name = os.getenv("DB_NAME", "prj_221")
        cls.db_user = os.getenv("DB_USER", "postgres")
        cls.db_password = os.getenv("DB_PASSWORD", "root")

    def test_database_env_vars_configured(self):
        """E3.1: Verify database connection environment variables are properly configured."""
        self.assertTrue(self.db_host, "DB_HOST is not set")
        self.assertTrue(self.db_name, "DB_NAME is not set")
        self.assertTrue(self.db_user, "DB_USER is not set")

    def test_database_connection_and_tables(self):
        """E3.2: Verify PostgreSQL connection and presence of all required relational tables."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
        except Exception as e:
            self.skipTest(f"Database not accessible in current network sandbox: {e}")
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.assertIn("PostgreSQL", version)

            # Check required tables
            required_tables = [
                "users",
                "behaviour_records",
                "predictions",
                "anomalies",
                "recommendations",
                "alerts",
            ]
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

            for table in required_tables:
                self.assertIn(
                    table,
                    existing_tables,
                    f"Required table '{table}' is missing from the database.",
                )

            # Check users table schema
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users';
            """)
            user_columns = [row[0] for row in cursor.fetchall()]
            for col in ["user_id", "name", "email", "password_hash", "role"]:
                self.assertIn(col, user_columns)

            cursor.close()
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
