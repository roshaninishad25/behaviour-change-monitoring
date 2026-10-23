import { apiFetch } from "./api";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  ShieldCheck,
  RefreshCw
} from "lucide-react";

import "./FacultyStudentDetails.css";

export default function FacultyStudentDetails({
  apiBaseUrl,
  studentId,
  onBack
}) {
  const [dashboard, setDashboard] = useState(null);
  const [trend, setTrend] = useState([]);
  const [explanation, setExplanation] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDetails = async () => {
    try {
      setLoading(true);
      setError("");

      const [dashboardResponse, trendResponse, explanationResponse] =
        await Promise.all([
          apiFetch(`${apiBaseUrl}/dashboard/${studentId}`),
          apiFetch(`${apiBaseUrl}/trend/${studentId}`),
          apiFetch(`${apiBaseUrl}/explanation/${studentId}`)
        ]);

      if (!dashboardResponse.ok) {
        throw new Error("Failed to fetch student dashboard data.");
      }

      if (!trendResponse.ok) {
        throw new Error("Failed to fetch student behaviour data.");
      }

      const dashboardData = await dashboardResponse.json();
      const trendData = await trendResponse.json();

      let explanationData = [];

      if (explanationResponse.ok) {
        const explanationResponseData =
          await explanationResponse.json();

        explanationData = explanationResponseData.explanations || [];
      }

      setDashboard(dashboardData);
      setTrend(trendData);
      setExplanation(explanationData);
    } catch (err) {
      setError(
        err.message || "Unable to load student details."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadDetails = async () => {
      try {
        setLoading(true);
        setError("");
        const [dashboardResponse, trendResponse, explanationResponse] =
          await Promise.all([
            apiFetch(`${apiBaseUrl}/dashboard/${studentId}`),
            apiFetch(`${apiBaseUrl}/trend/${studentId}`),
            apiFetch(`${apiBaseUrl}/explanation/${studentId}`)
          ]);

        if (!dashboardResponse.ok) {
          throw new Error("Failed to fetch student dashboard data.");
        }
        if (!trendResponse.ok) {
          throw new Error("Failed to fetch student behaviour data.");
        }
        const dashboardData = await dashboardResponse.json();
        const trendData = await trendResponse.json();
        let explanationData = [];
        if (explanationResponse.ok) {
          const expRes = await explanationResponse.json();
          explanationData = expRes.explanations || [];
        }
        if (isMounted) {
          setDashboard(dashboardData);
          setTrend(trendData);
          setExplanation(explanationData);
        }
      } catch (err) {
        if (isMounted) setError(err.message || "Unable to load student details.");
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadDetails();
    return () => { isMounted = false; };
  }, [apiBaseUrl, studentId]);

  if (loading) {
    return (
      <div className="faculty-detail-state">
        <RefreshCw size={20} />
        <p>Loading student monitoring details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="faculty-detail-state faculty-detail-error">
        <AlertTriangle size={20} />
        <p>{error}</p>

        <button onClick={fetchDetails}>
          Try Again
        </button>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  const prediction = dashboard.prediction;
  const anomaly = dashboard.anomaly;
  const recommendation = dashboard.recommendation;
  const alert = dashboard.alert;

  const behaviourState =
    prediction?.behavior_state || "Unavailable";

  const getStateIcon = () => {
    if (behaviourState === "Improving") {
      return <TrendingUp size={18} />;
    }

    if (behaviourState === "Declining") {
      return <TrendingDown size={18} />;
    }

    return <Minus size={18} />;
  };

  const getMaxShap = () => {
    if (!explanation.length) {
      return 0;
    }

    return Math.max(
      ...explanation.map((item) =>
        Math.abs(Number(item.shap_value))
      )
    );
  };

  const maxShap = getMaxShap();

  return (
    <div className="faculty-detail-page">

      {/* Header */}
      <div className="faculty-detail-header">

        <button
          className="faculty-back-button"
          onClick={onBack}
        >
          <ArrowLeft size={17} />
          Back to Students
        </button>

        <div className="faculty-detail-heading">
          <div className="faculty-detail-avatar">
            {dashboard.user.name
              ? dashboard.user.name
                  .charAt(0)
                  .toUpperCase()
              : "U"}
          </div>

          <div>
            <span>Student Monitoring</span>

            <h1>{dashboard.user.name}</h1>

            <p>
              {dashboard.user.user_id} ·{" "}
              {dashboard.user.email}
            </p>
          </div>
        </div>
      </div>

      {/* Top monitoring cards */}
      <div className="faculty-detail-grid">

        <div className="faculty-detail-card">
          <span>Behaviour State</span>

          <strong className="faculty-detail-state-value">
            {getStateIcon()}
            {behaviourState}
          </strong>
        </div>

        <div className="faculty-detail-card">
          <span>BCI</span>

          <strong>
            {prediction?.bci !== null &&
            prediction?.bci !== undefined
              ? Number(prediction.bci).toFixed(4)
              : "—"}
          </strong>
        </div>

        <div className="faculty-detail-card">
          <span>Anomaly</span>

          <strong>
            {anomaly
              ? anomaly.anomaly_flag === -1
                ? "Anomalous"
                : "Normal"
              : "Unavailable"}
          </strong>
        </div>

        <div className="faculty-detail-card">
          <span>Monitoring Priority</span>

          <strong>
            {alert?.priority || "Unavailable"}
          </strong>
        </div>

      </div>

      {/* Behaviour trend */}
      <section className="faculty-detail-section">

        <div className="faculty-detail-section-header">
          <div>
            <span>Behaviour History</span>
            <h2>Sequential Activity</h2>
          </div>

          <span>
            {trend.length} observations
          </span>
        </div>

        <div className="faculty-trend-table-wrapper">
          <table className="faculty-trend-table">
            <thead>
              <tr>
                <th>Sequence</th>
                <th>Course Views</th>
                <th>Lecture Views</th>
                <th>Forum Consumption</th>
                <th>Forum Contributions</th>
                <th>Sessions</th>
                <th>Active Days</th>
                <th>Final Grade</th>
              </tr>
            </thead>

            <tbody>
              {trend.map((item) => (
                <tr key={item.sequence}>
                  <td>{item.sequence}</td>
                  <td>{item.freq_course_view}</td>
                  <td>{item.freq_lecture_view}</td>
                  <td>{item.freq_forum_consume}</td>
                  <td>{item.freq_forum_contribute}</td>
                  <td>{item.session_count}</td>
                  <td>{item.active_days}</td>
                  <td>
                    {item.final_grade !== null &&
                    item.final_grade !== undefined
                      ? Number(item.final_grade).toFixed(2)
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </section>

      {/* Bottom information */}
      <div className="faculty-detail-bottom-grid">

        <section className="faculty-detail-section compact">

          <div className="faculty-detail-section-header">
            <div>
              <span>Model Explanation</span>
              <h2>Top Contributing Features</h2>
            </div>
          </div>

          {explanation.length > 0 ? (
            <div className="faculty-shap-list">

              {explanation.map((item) => {
                const value = Number(item.shap_value);
                const width =
                  maxShap > 0
                    ? (Math.abs(value) / maxShap) * 100
                    : 0;

                return (
                  <div
                    className="faculty-shap-row"
                    key={item.feature}
                  >
                    <div className="faculty-shap-label">
                      <span>{item.feature}</span>

                      <strong>
                        {value >= 0 ? "+" : ""}
                        {value.toFixed(4)}
                      </strong>
                    </div>

                    <div className="faculty-shap-track">
                      <div
                        className="faculty-shap-bar"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>
                );
              })}

            </div>
          ) : (
            <div className="faculty-detail-muted">
              Explanation data is unavailable.
            </div>
          )}

        </section>

        <section className="faculty-detail-section compact">

          <div className="faculty-detail-section-header">
            <div>
              <span>Monitoring</span>
              <h2>Recommendation</h2>
            </div>

            <ShieldCheck size={19} />
          </div>

          <div className="faculty-recommendation">
            <p>
              {recommendation?.recommendation ||
                "No recommendation is currently available."}
            </p>
          </div>

          <div className="faculty-monitoring-row">
            <span>Anomaly score</span>

            <strong>
              {anomaly?.anomaly_score !== null &&
              anomaly?.anomaly_score !== undefined
                ? Number(anomaly.anomaly_score).toFixed(4)
                : "—"}
            </strong>
          </div>

          <div className="faculty-monitoring-row">
            <span>Priority</span>

            <strong>
              {alert?.priority || "—"}
            </strong>
          </div>

        </section>

      </div>

    </div>
  );
}