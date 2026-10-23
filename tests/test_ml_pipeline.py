import os
import json
import unittest
import joblib
import numpy as np
import pandas as pd


class TestMLPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rf_model_path = "models/random_forest_v2.pkl"
        cls.if_model_path = "models/isolation_forest.pkl"
        cls.scaler_path = "models/anomaly_scaler.pkl"
        cls.features_path = "models/feature_columns.json"

        # Ensure model files exist
        assert os.path.exists(cls.rf_model_path), f"Missing {cls.rf_model_path}"
        assert os.path.exists(cls.if_model_path), f"Missing {cls.if_model_path}"
        assert os.path.exists(cls.scaler_path), f"Missing {cls.scaler_path}"
        assert os.path.exists(cls.features_path), f"Missing {cls.features_path}"

        cls.rf_model = joblib.load(cls.rf_model_path)
        cls.isolation_forest = joblib.load(cls.if_model_path)
        cls.scaler = joblib.load(cls.scaler_path)

        with open(cls.features_path, "r") as f:
            cls.feature_columns = json.load(f)

    def test_models_exist_and_load(self):
        """E2.1: Verify all trained machine learning artifacts load properly."""
        self.assertIsNotNone(self.rf_model)
        self.assertIsNotNone(self.isolation_forest)
        self.assertIsNotNone(self.scaler)
        self.assertIsInstance(self.feature_columns, list)

    def test_feature_columns_schema(self):
        """E2.2: Verify exactly 44 features are registered in expected training order."""
        self.assertEqual(len(self.feature_columns), 44)
        for col in self.feature_columns:
            self.assertTrue(
                col.endswith("_mean")
                or col.endswith("_std")
                or col.endswith("_recent")
                or col.endswith("_trend"),
                f"Feature column {col} does not follow expected naming convention",
            )

    def test_feature_engineering_pipeline(self):
        """E2.3: Verify that 7 sequential periods transform into exactly 44 features."""
        # 7 synthetic periods
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

        sample_periods = []
        for seq in range(1, 8):
            sample_periods.append({
                "Freq_Course_View": 10.0 + seq * 2,
                "Freq_Forum_Consume": 5.0 + seq,
                "Freq_Forum_Contribute": 1.0 + (seq % 2),
                "Freq_Lecture_View": 4.0 + seq,
                "Regularity_Course_View": 0.5 + (seq * 0.05),
                "Regularity_Lecture_View": 0.6,
                "Regularity_Forum_Consume": 0.4,
                "Regularity_Forum_Contribute": 0.3,
                "Session_Count": 15 + seq,
                "Total_Duration": 3600 + seq * 500,
                "Active_Days": 3 + (seq % 4),
            })

        df = pd.DataFrame(sample_periods)
        self.assertEqual(len(df), 7)

        # Build feature dict
        feature_data = {}
        for column in behaviour_columns:
            values = df[column].astype(float)
            feature_data[f"{column}_mean"] = values.mean()
            feature_data[f"{column}_std"] = values.std(ddof=1)
            feature_data[f"{column}_recent"] = values.iloc[-1]

            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            feature_data[f"{column}_trend"] = slope

        X_user = pd.DataFrame([feature_data])[self.feature_columns]
        self.assertEqual(X_user.shape, (1, 44))
        self.assertFalse(X_user.isna().any().any(), "Features should not contain NaN")

    def test_random_forest_inference(self):
        """E2.4: Verify Random Forest inference produces valid behavioral state."""
        # Create valid input vector of zeros/means
        sample_input = pd.DataFrame(
            np.ones((1, 44)), columns=self.feature_columns
        )
        prediction = self.rf_model.predict(sample_input)[0]

        valid_states = ["Improving", "Stable", "Declining"]
        self.assertIn(
            str(prediction),
            valid_states,
            f"Prediction {prediction} must be one of {valid_states}",
        )

    def test_isolation_forest_anomaly(self):
        """E2.5: Verify Isolation Forest produces valid anomaly flags (-1 or 1) and scores."""
        sample_input = pd.DataFrame(
            np.ones((1, 44)), columns=self.feature_columns
        )
        scaled_input = self.scaler.transform(sample_input)

        flag = int(self.isolation_forest.predict(scaled_input)[0])
        score = float(abs(self.isolation_forest.decision_function(scaled_input)[0]))

        self.assertIn(flag, [1, -1])
        self.assertGreaterEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
