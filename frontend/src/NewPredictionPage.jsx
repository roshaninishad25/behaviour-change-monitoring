import { apiFetch } from "./api";
import { useState } from "react";
import "./NewPredictionPage.css";

const fields = [
  {
    key: "freq_course_view",
    label: "Course Views",
    description: "Number of course-view interactions"
  },
  {
    key: "freq_lecture_view",
    label: "Lecture Views",
    description: "Number of lecture-view interactions"
  },
  {
    key: "freq_forum_consume",
    label: "Forum Consumption",
    description: "Number of forum posts viewed/read"
  },
  {
    key: "freq_forum_contribute",
    label: "Forum Contributions",
    description: "Number of forum contributions"
  },
  {
    key: "regularity_course_view",
    label: "Course View Regularity",
    description: "Regularity value from 0 to 1"
  },
  {
    key: "regularity_lecture_view",
    label: "Lecture View Regularity",
    description: "Regularity value from 0 to 1"
  },
  {
    key: "regularity_forum_consume",
    label: "Forum Consumption Regularity",
    description: "Regularity value from 0 to 1"
  },
  {
    key: "regularity_forum_contribute",
    label: "Forum Contribution Regularity",
    description: "Regularity value from 0 to 1"
  },
  {
    key: "session_count",
    label: "Session Count",
    description: "Number of learning sessions"
  },
  {
    key: "total_duration",
    label: "Total Duration",
    description: "Total learning duration"
  },
  {
    key: "active_days",
    label: "Active Days",
    description: "Number of active learning days"
  }
];

const createEmptyPeriod = () => {
  const period = {};

  fields.forEach((field) => {
    period[field.key] = "";
  });

  return period;
};

export default function NewPredictionPage({ apiBaseUrl }) {
  const [currentSequence, setCurrentSequence] = useState(0);
  const [periods, setPeriods] = useState(
    Array.from({ length: 7 }, createEmptyPeriod)
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const updateField = (fieldKey, value) => {
    setPeriods((previous) => {
      const updated = [...previous];

      updated[currentSequence] = {
        ...updated[currentSequence],
        [fieldKey]: value
      };

      return updated;
    });
  };

  const validateCurrentSequence = () => {
    const currentPeriod = periods[currentSequence];

    for (const field of fields) {
      const value = currentPeriod[field.key];

      if (value === "") {
        return `${field.label} is required.`;
      }

      const numericValue = Number(value);

      if (!Number.isFinite(numericValue)) {
        return `${field.label} must be a valid number.`;
      }

      if (numericValue < 0) {
        return `${field.label} cannot be negative.`;
      }
    }

    const regularityFields = [
      "regularity_course_view",
      "regularity_lecture_view",
      "regularity_forum_consume",
      "regularity_forum_contribute"
    ];

    for (const key of regularityFields) {
      const value = Number(currentPeriod[key]);

      if (value < 0 || value > 1) {
        const field = fields.find((item) => item.key === key);

        return `${field.label} must be between 0 and 1.`;
      }
    }

    return "";
  };

  const handleNext = () => {
    setError("");

    const validationError = validateCurrentSequence();

    if (validationError) {
      setError(validationError);
      return;
    }

    setCurrentSequence((previous) => Math.min(previous + 1, 6));
  };

  const handleBack = () => {
    setError("");
    setCurrentSequence((previous) => Math.max(previous - 1, 0));
  };

  const handleSubmit = async () => {
    setError("");

    const validationError = validateCurrentSequence();

    if (validationError) {
      setError(validationError);
      return;
    }

    const incompleteSequence = periods.findIndex((period) =>
      fields.some((field) => period[field.key] === "")
    );

    if (incompleteSequence !== -1) {
      setCurrentSequence(incompleteSequence);
      setError(
        `Please complete Sequence ${incompleteSequence + 1} before submitting.`
      );
      return;
    }

    const payload = {
      periods: periods.map((period) => {
        const convertedPeriod = {};

        fields.forEach((field) => {
          convertedPeriod[field.key] = Number(period[field.key]);
        });

        return convertedPeriod;
      })
    };

    try {
      setLoading(true);

      const response = await apiFetch(`${apiBaseUrl}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Prediction could not be generated."
        );
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="new-prediction-page">
        <div className="prediction-result-card">
          <div className="prediction-result-header">
            <span className="prediction-eyebrow">Prediction Result</span>

            <h1>{result.behavior_state}</h1>

            <p>
              The behavioural pattern prediction has been generated from
              the seven submitted sequences.
            </p>
          </div>

          <div className="prediction-result-grid">
            <div className="prediction-stat">
              <span>Behaviour State</span>
              <strong>{result.behavior_state}</strong>
            </div>

            <div className="prediction-stat">
              <span>Anomaly Status</span>
              <strong>{result.anomaly_status}</strong>
            </div>

            <div className="prediction-stat">
              <span>Anomaly Score</span>
              <strong>{Number(result.anomaly_score).toFixed(4)}</strong>
            </div>

            <div className="prediction-stat">
              <span>Monitoring Priority</span>
              <strong>{result.alert_priority}</strong>
            </div>
          </div>

          <div className="prediction-info-block">
            <span>Recommendation</span>
            <p>{result.recommendation}</p>
          </div>

          <div className="prediction-info-block">
            <span>BCI</span>
            <p>
              {result.bci === null
                ? "Not available yet. The project's BCI requires Sequence 8."
                : Number(result.bci).toFixed(4)}
            </p>
          </div>

          <button
            className="prediction-secondary-button"
            onClick={() => {
              setResult(null);
              setCurrentSequence(0);
              setError("");
            }}
          >
            Start Another Assessment
          </button>
        </div>
      </div>
    );
  }

  const currentPeriod = periods[currentSequence];

  return (
    <div className="new-prediction-page">
      <div className="new-prediction-header">
        <span className="prediction-eyebrow">New Student Assessment</span>

        <h1>Behaviour Assessment</h1>

        <p>
          Enter the student's behavioural information across seven
          sequential observations. These observations are used to generate
          the behavioural prediction.
        </p>
      </div>

      <div className="sequence-progress">
        {periods.map((_, index) => (
          <button
            key={index}
            type="button"
            className={
              index === currentSequence
                ? "sequence-dot active"
                : index < currentSequence
                  ? "sequence-dot complete"
                  : "sequence-dot"
            }
            onClick={() => {
              setError("");
              setCurrentSequence(index);
            }}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="assessment-card">
        <div className="assessment-card-header">
          <div>
            <span className="sequence-label">
              Sequence {currentSequence + 1}
            </span>

            <h2>Behavioural Information</h2>
          </div>

          <span className="sequence-count">
            {currentSequence + 1} / 7
          </span>
        </div>

        <div className="assessment-fields">
          {fields.map((field) => (
            <div className="assessment-field" key={field.key}>
              <label htmlFor={field.key}>{field.label}</label>

              <input
                id={field.key}
                type="number"
                min="0"
                step="any"
                value={currentPeriod[field.key]}
                onChange={(event) =>
                  updateField(field.key, event.target.value)
                }
                placeholder="Enter value"
              />

              <small>{field.description}</small>
            </div>
          ))}
        </div>

        {error && <div className="assessment-error">{error}</div>}

        <div className="assessment-actions">
          <button
            type="button"
            className="prediction-secondary-button"
            onClick={handleBack}
            disabled={currentSequence === 0 || loading}
          >
            Previous
          </button>

          {currentSequence < 6 ? (
            <button
              type="button"
              className="prediction-primary-button"
              onClick={handleNext}
              disabled={loading}
            >
              Next Sequence
            </button>
          ) : (
            <button
              type="button"
              className="prediction-primary-button"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? "Generating Prediction..." : "Generate Prediction"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}