import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Activity,
  Lightbulb,
  Bell,
  UserRound,
  Menu,
  X,
  ChevronDown,
  ArrowUpRight,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import NewPredictionPage from "./NewPredictionPage";
import FacultyDashboard from "./FacultyDashboard";
import AuthPage from "./AuthPage";
import FacultyOverview from "./FacultyOverview";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import "./App.css";

const TREND_METRICS = [
  {
    key: "session_count",
    label: "Session count",
  },
  {
    key: "active_days",
    label: "Active days",
  },
  {
    key: "freq_course_view",
    label: "Course views",
  },
  {
    key: "freq_lecture_view",
    label: "Lecture views",
  },
  {
    key: "freq_forum_consume",
    label: "Forum consumption",
  },
  {
    key: "freq_forum_contribute",
    label: "Forum contributions",
  },
  {
    key: "total_duration",
    label: "Total duration",
  },
  {
    key: "final_grade",
    label: "Final grade",
  },
];

function BehaviourPage({ trend }) {
  const [selectedMetric, setSelectedMetric] =
    useState("session_count");

  const selectedLabel =
    TREND_METRICS.find((metric) => metric.key === selectedMetric)?.label ||
    "Session count";

  const firstSequence = trend[0];
  const lastSequence = trend[trend.length - 1];

  const sessionChange =
    firstSequence && lastSequence
      ? lastSequence.session_count - firstSequence.session_count
      : 0;

  const activeDayChange =
    firstSequence && lastSequence
      ? lastSequence.active_days - firstSequence.active_days
      : 0;

  const gradeChange =
    firstSequence && lastSequence
      ? lastSequence.final_grade - firstSequence.final_grade
      : 0;

  return (
    <div className="behaviour-page">
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <Activity size={14} />
            Behaviour history
          </div>

          <h1>Behaviour analysis</h1>

          <p>
            Explore behavioural activity across the eight sequential
            courses.
          </p>
        </div>

        <div className="date-info">
          <span>Observations</span>
          <strong>{trend.length} sequences</strong>
        </div>
      </section>

      <section className="behaviour-summary">
        <div className="metric-card">
          <div className="metric-top">
            <span>Session change</span>

            <div className="metric-icon">
              <Activity size={18} />
            </div>
          </div>

          <div className="metric-value">
            {sessionChange >= 0 ? "+" : ""}
            {sessionChange}
          </div>

          <div className="metric-description">
            Sequence 1 → Sequence 8
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Active-day change</span>

            <div className="metric-icon">
              <ArrowUpRight size={18} />
            </div>
          </div>

          <div className="metric-value">
            {activeDayChange >= 0 ? "+" : ""}
            {activeDayChange}
          </div>

          <div className="metric-description">
            Sequence 1 → Sequence 8
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Final grade change</span>

            <div className="metric-icon">
              <ShieldCheck size={18} />
            </div>
          </div>

          <div className="metric-value">
            {gradeChange >= 0 ? "+" : ""}
            {gradeChange.toFixed(2)}
          </div>

          <div className="metric-description">
            Sequence 1 → Sequence 8
          </div>
        </div>
      </section>

      <section className="panel behaviour-chart-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              Sequence analysis
            </span>

            <h2>{selectedLabel}</h2>

            <p>
              Change in {selectedLabel.toLowerCase()} across
              sequential courses.
            </p>
          </div>

          <select
            className="select-button"
            value={selectedMetric}
            onChange={(event) =>
              setSelectedMetric(event.target.value)
            }
          >
            {TREND_METRICS.map((metric) => (
              <option key={metric.key} value={metric.key}>
                {metric.label}
              </option>
            ))}
          </select>
        </div>

        <div className="behaviour-chart">
          <ResponsiveContainer width="100%" height={330}>
            <LineChart
              data={trend}
              margin={{
                top: 10,
                right: 20,
                left: 10,
                bottom: 10,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />

              <XAxis
                dataKey="sequence"
                tickFormatter={(value) => `Seq ${value}`}
              />

              <YAxis />

              <Tooltip
                labelFormatter={(value) =>
                  `Sequence ${value}`
                }
                formatter={(value) => [
                  Number(value).toLocaleString(),
                  selectedLabel,
                ]}
              />

              <Line
                type="monotone"
                dataKey={selectedMetric}
                stroke="currentColor"
                strokeWidth={3}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel behaviour-table-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              Behaviour records
            </span>

            <h2>Sequence details</h2>

            <p>
              Recorded behavioural activity for each sequential
              course.
            </p>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="behaviour-table">
            <thead>
              <tr>
                <th>Sequence</th>
                <th>Sessions</th>
                <th>Active days</th>
                <th>Course views</th>
                <th>Lecture views</th>
                <th>Forum consumed</th>
                <th>Forum contributions</th>
                <th>Total duration</th>
                <th>Final grade</th>
              </tr>
            </thead>

            <tbody>
              {trend.map((record) => (
                <tr key={record.sequence}>
                  <td>
                    <strong>Seq {record.sequence}</strong>
                  </td>

                  <td>{record.session_count}</td>

                  <td>{record.active_days}</td>

                  <td>{record.freq_course_view}</td>

                  <td>{record.freq_lecture_view}</td>

                  <td>{record.freq_forum_consume}</td>

                  <td>{record.freq_forum_contribute}</td>

                  <td>
                    {Number(
                      record.total_duration
                    ).toLocaleString()}
                  </td>

                  <td>
                    <span className="grade-value">
                      {record.final_grade.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function InsightsPage({ dashboard, explanation }) {
  const behaviorState = dashboard.prediction?.behavior_state || "Not available";
  const anomalyIsNormal = dashboard.anomaly?.anomaly_flag === 1;

  const maxShapValue =
    explanation.length > 0
      ? Math.max(
        ...explanation.map((item) =>
          Math.abs(item.shap_value)
        )
      )
      : 0;

  return (
    <div className="insights-page">
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <Lightbulb size={14} />
            Explainable AI
          </div>

          <h1>Model insights</h1>

          <p>
            Understand how the behavioural models interpret the
            current user pattern.
          </p>
        </div>

        <div className="date-info">
          <span>Prediction</span>
          <strong>{behaviorState}</strong>
        </div>
      </section>

      <section className="insight-model-grid">
        <div className="insight-model-card">
          <div className="insight-card-icon">
            <Activity size={20} />
          </div>

          <span className="panel-kicker">
            Classification model
          </span>

          <h2>Random Forest</h2>

          <div className="insight-result">
            {behaviorState}
          </div>

          <p>
            The classification model predicts the current
            behavioural state using historical behavioural
            features and trend information.
          </p>
        </div>

        <div className="insight-model-card">
          <div className="insight-card-icon">
            <ShieldCheck size={20} />
          </div>

          <span className="panel-kicker">
            Anomaly detection
          </span>

          <h2>Isolation Forest</h2>

          <div className="insight-result">
            {!dashboard.anomaly
              ? "Not available"
              : anomalyIsNormal
                ? "Normal"
                : "Unusual"}
          </div>

          <p>
            The anomaly detector identifies behavioural patterns
            that are unusual relative to the observed dataset.
          </p>

          <div className="insight-score">
            Score:{" "}
            {dashboard.anomaly?.anomaly_score?.toFixed(4)}
          </div>
        </div>

        <div className="insight-model-card">
          <div className="insight-card-icon">
            <ArrowUpRight size={20} />
          </div>

          <span className="panel-kicker">
            Behavioural indicator
          </span>

          <h2>Behavioural Change Index</h2>

          <div className="insight-result">
            {dashboard.prediction?.bci != null
              ? Number(dashboard.prediction.bci).toFixed(4)
              : "—"}
          </div>

          <p>
            The BCI summarizes standardized changes across the
            behavioural variables used to construct the monitoring
            state.
          </p>
        </div>
      </section>

      <section className="panel shap-insight-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              Explainable AI
            </span>

            <h2>Why was this state predicted?</h2>

            <p>
              SHAP values show each feature's contribution toward
              the current model prediction.
            </p>
          </div>

          <span className="model-tag">
            SHAP • Random Forest
          </span>
        </div>

        <div className="insight-shap-list">
          {explanation.map((item) => {
            const width =
              maxShapValue === 0
                ? 0
                : (Math.abs(item.shap_value) /
                  maxShapValue) *
                100;

            return (
              <div
                className="insight-shap-item"
                key={item.feature}
              >
                <div className="insight-shap-header">
                  <span>{item.feature}</span>

                  <strong>
                    {item.shap_value >= 0 ? "+" : ""}
                    {item.shap_value.toFixed(4)}
                  </strong>
                </div>

                <div className="insight-shap-track">
                  <div
                    className="insight-shap-fill"
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="insight-note">
          <ShieldCheck size={16} />

          <span>
            SHAP values describe model contribution and should not
            be interpreted as causal effects.
          </span>
        </div>
      </section>

      <section className="insight-bottom-grid">
        <div className="panel">
          <div className="panel-header compact">
            <div>
              <span className="panel-kicker">
                Decision support
              </span>

              <h2>Recommendation</h2>
            </div>

            <div className="recommendation-icon">
              <Lightbulb size={19} />
            </div>
          </div>

          <div className="recommendation-content">
            <div className="recommendation-status">
              {behaviorState === "Not available"
                ? "Monitoring not started"
                : `${behaviorState} behaviour`}
            </div>

            <p>
              {dashboard.recommendation?.recommendation ||
                "No recommendation is available yet. Behavioural monitoring data has not been recorded for this account."}
            </p>

            <div className="recommendation-note">
              <ShieldCheck size={15} />
              Rule-based recommendation
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header compact">
            <div>
              <span className="panel-kicker">
                Monitoring
              </span>

              <h2>Alert priority</h2>
            </div>

            <Bell size={19} />
          </div>

          <div className="insight-alert">
            <strong>
              {dashboard.alert?.priority || "Not available"}
            </strong>

            <p>
              This priority represents the monitoring attention
              assigned by the decision rules.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function FacultyAlertsPage({ apiBaseUrl }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchFacultyAlerts() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${apiBaseUrl}/faculty/students`
        );

        if (!response.ok) {
          throw new Error(
            "Failed to load faculty alert data."
          );
        }

        const data = await response.json();

        setStudents(data);
      } catch (err) {
        setError(
          err.message ||
          "Unable to load faculty alerts."
        );
      } finally {
        setLoading(false);
      }
    }

    fetchFacultyAlerts();
  }, [apiBaseUrl]);

  const highPriority = students.filter(
    (student) => student.priority === "High"
  );

  const mediumPriority = students.filter(
    (student) => student.priority === "Medium"
  );

  const elevatedStudents = students.filter(
    (student) =>
      student.priority === "Medium" ||
      student.priority === "High"
  );

  if (loading) {
    return (
      <div className="loading-screen">
        Loading faculty alerts...
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-screen">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="faculty-alerts-page">

      {/* Header */}
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <Bell size={14} />
            Faculty monitoring
          </div>

          <h1>Alerts & monitoring</h1>

          <p>
            Review students currently assigned elevated
            monitoring priority by the behavioural
            decision rules.
          </p>
        </div>

        <div className="date-info">
          <span>Students requiring attention</span>
          <strong>{elevatedStudents.length}</strong>
        </div>
      </section>

      {/* Summary */}
      <section className="metrics-grid">

        <div className="metric-card">
          <div className="metric-top">
            <span>High priority</span>

            <div className="metric-icon">
              <Bell size={18} />
            </div>
          </div>

          <div className="metric-value">
            {highPriority.length}
          </div>

          <div className="metric-description">
            Students assigned high monitoring priority
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Medium priority</span>

            <div className="metric-icon">
              <Bell size={18} />
            </div>
          </div>

          <div className="metric-value">
            {mediumPriority.length}
          </div>

          <div className="metric-description">
            Students assigned medium monitoring priority
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Elevated monitoring</span>

            <div className="metric-icon">
              <Activity size={18} />
            </div>
          </div>

          <div className="metric-value">
            {elevatedStudents.length}
          </div>

          <div className="metric-description">
            Medium or high monitoring priority
          </div>
        </div>

      </section>

      {/* Alert information */}
      <section className="panel faculty-alerts-panel">

        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              Decision-support monitoring
            </span>

            <h2>Students requiring attention</h2>

            <p>
              These entries are based on the software's
              current behaviour-state and anomaly decision
              rules.
            </p>
          </div>

          <Bell size={19} />
        </div>

        {elevatedStudents.length === 0 ? (
          <div className="faculty-alerts-empty">
            <ShieldCheck size={20} />

            <span>
              No students currently have an elevated
              monitoring priority.
            </span>
          </div>
        ) : (
          <div className="faculty-alert-list">

            {elevatedStudents.map((student) => (

              <div
                className="faculty-alert-row"
                key={student.user_id}
              >

                <div className="faculty-alert-student">
                  <div className="faculty-alert-avatar">
                    {student.name
                      ?.charAt(0)
                      .toUpperCase() || "U"}
                  </div>

                  <div>
                    <strong>
                      {student.name}
                    </strong>

                    <span>
                      {student.user_id}
                    </span>
                  </div>
                </div>

                <div className="faculty-alert-state">
                  <span>
                    Behaviour
                  </span>

                  <strong>
                    {student.behavior_state ||
                      "Not available"}
                  </strong>
                </div>

                <div className="faculty-alert-anomaly">
                  <span>
                    Pattern
                  </span>

                  <strong>
                    {student.anomaly_flag === -1
                      ? "Unusual"
                      : "Normal"}
                  </strong>
                </div>

                <div className="faculty-alert-priority">
                  <span>
                    Priority
                  </span>

                  <strong>
                    {student.priority}
                  </strong>
                </div>

              </div>

            ))}

          </div>
        )}

      </section>

      {/* Interpretation */}
      <section className="panel faculty-alert-note">

        <div className="panel-header compact">
          <div>
            <span className="panel-kicker">
              Interpretation
            </span>

            <h2>About these alerts</h2>
          </div>
        </div>

        <p>
          Monitoring priority is a software-generated
          indicator based on behavioural state and anomaly
          status. It is intended to support faculty review
          of student activity and should not be treated as
          a diagnosis or definitive assessment of a person.
        </p>

      </section>

    </div>
  );
}

function AlertsPage({
  dashboard,
  isFaculty,
  apiBaseUrl
}) {
  if (isFaculty) {
    return (
      <FacultyAlertsPage
        apiBaseUrl={apiBaseUrl}
      />
    );
  }

  const behaviorState =
    dashboard.prediction?.behavior_state || "Not available";

  const anomalyIsNormal =
    dashboard.anomaly?.anomaly_flag === 1;

  const anomalyStatus = dashboard.anomaly
    ? anomalyIsNormal
      ? "Normal"
      : "Unusual"
    : "Not available";

  const priority =
    dashboard.alert?.priority || "Not available";

  const priorityDescription = {
    High: "Requires timely monitoring attention based on the current decision rules.",
    Medium: "Warrants additional monitoring based on the current behavioural pattern.",
    Low: "No elevated monitoring attention is currently required.",
  };

  return (
    <div className="alerts-page">
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <Bell size={14} />
            Monitoring alerts
          </div>

          <h1>Alerts & monitoring</h1>

          <p>
            Review the current monitoring priority and unusual-pattern
            detection for this user.
          </p>
        </div>

        <div className="date-info">
          <span>Current priority</span>
          <strong>{priority}</strong>
        </div>
      </section>

      <section className="alert-main-card">
        <div className="alert-main-header">
          <div className="alert-icon-large">
            <Bell size={24} />
          </div>

          <div>
            <span className="panel-kicker">
              Current monitoring priority
            </span>

            <h2>{priority}</h2>
          </div>
        </div>

        <p className="alert-main-description">
          {priorityDescription[priority]}
        </p>

        <div className="priority-line alert-priority-line">
          <span
            className={
              priority === "Low" ? "priority-active" : ""
            }
          />

          <span
            className={
              priority === "Medium" ? "priority-active" : ""
            }
          />

          <span
            className={
              priority === "High" ? "priority-active" : ""
            }
          />
        </div>
      </section>

      <section className="alert-info-grid">
        <div className="panel alert-info-card">
          <div className="panel-header compact">
            <div>
              <span className="panel-kicker">
                Behaviour model
              </span>

              <h2>Behaviour state</h2>
            </div>

            <Activity size={19} />
          </div>

          <div className="alert-result">
            {behaviorState}
          </div>

          <p>
            Current state predicted by the Random Forest
            classification model.
          </p>
        </div>

        <div className="panel alert-info-card">
          <div className="panel-header compact">
            <div>
              <span className="panel-kicker">
                Pattern detection
              </span>

              <h2>Anomaly status</h2>
            </div>

            <ShieldCheck size={19} />
          </div>

          <div className="alert-result">
            {anomalyStatus}
          </div>

          <p>
            Isolation Forest anomaly score:
            {" "}
            <strong>
              {dashboard.anomaly?.anomaly_score != null
                ? Number(dashboard.anomaly.anomaly_score).toFixed(4)
                : "—"}
            </strong>
          </p>
        </div>
      </section>

      <section className="panel alert-recommendation-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              Decision support
            </span>

            <h2>Recommended action</h2>

            <p>
              Recommendation generated from the current behaviour
              state and anomaly result.
            </p>
          </div>

          <div className="recommendation-icon">
            <Lightbulb size={19} />
          </div>
        </div>

        <div className="alert-recommendation-box">
          <div className="recommendation-status">
            {behaviorState === "Not available"
              ? "Monitoring not started"
              : `${behaviorState} behaviour`}
          </div>

          <p>
            {dashboard.recommendation?.recommendation ||
              "No recommendation is available yet. Behavioural monitoring data has not been recorded for this account."}
          </p>

          <div className="recommendation-note">
            <ShieldCheck size={15} />
            Rule-based recommendation
          </div>
        </div>
      </section>

      <section className="panel monitoring-note-panel">
        <div className="panel-header compact">
          <div>
            <span className="panel-kicker">
              Interpretation
            </span>

            <h2>About monitoring priority</h2>
          </div>
        </div>

        <p className="monitoring-note">
          Alert priority is a software-generated monitoring
          indicator based on the predicted behavioural state and
          anomaly result. It is intended to support review and
          should not be interpreted as a diagnosis or definitive
          assessment of a person.
        </p>
      </section>
    </div>
  );
}

function ProfilePage({ user }) {
  return (
    <div className="profile-page">
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <UserRound size={14} />
            Account
          </div>

          <h1>Profile</h1>

          <p>
            View the account information associated with this
            monitoring profile.
          </p>
        </div>

        <div className="date-info">
          <span>Account role</span>
          <strong>{user.role}</strong>
        </div>
      </section>

      <section className="profile-main-grid">
        <div className="panel profile-card">
          <div className="profile-avatar">
            <UserRound size={30} />
          </div>

          <h2>{user.name}</h2>

          <p className="profile-role">{user.role}</p>

          <div className="profile-id">
            User ID: <strong>{user.user_id}</strong>
          </div>
        </div>

        <div className="panel profile-details-card">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">
                Account information
              </span>

              <h2>Profile details</h2>

              <p>
                Information retrieved from the system database.
              </p>
            </div>

            <UserRound size={19} />
          </div>

          <div className="profile-details">
            <div className="profile-detail-row">
              <span>Name</span>
              <strong>{user.name}</strong>
            </div>

            <div className="profile-detail-row">
              <span>User ID</span>
              <strong>{user.user_id}</strong>
            </div>

            <div className="profile-detail-row">
              <span>Email</span>
              <strong>{user.email}</strong>
            </div>

            <div className="profile-detail-row">
              <span>Role</span>
              <strong>{user.role}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="panel profile-system-card">
        <div className="panel-header compact">
          <div>
            <span className="panel-kicker">
              Monitoring system
            </span>

            <h2>Behaviour monitoring</h2>
          </div>

          <ShieldCheck size={19} />
        </div>

        <p>
          This profile is connected to the PRJ-221 Behavioural
          Change Monitoring Software. The system analyses
          behavioural activity across sequential observations,
          identifies unusual patterns, explains model predictions,
          and provides rule-based monitoring recommendations.
        </p>

        <div className="profile-system-tags">
          <span>Behaviour analysis</span>
          <span>Anomaly detection</span>
          <span>Explainable AI</span>
          <span>Decision support</span>
        </div>
      </section>
    </div>
  );
}

function App() {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem("prj221_user");
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const handleLogin = (user) => {
    localStorage.setItem(
      "prj221_user",
      JSON.stringify(user)
    );

    setCurrentUser(user);
    setActivePage("Dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("prj221_user");
    setCurrentUser(null);
  };

  const [activePage, setActivePage] = useState("Dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [dashboard, setDashboard] = useState(null);
  const [trend, setTrend] = useState([]);
  const [explanation, setExplanation] = useState([]);
  const [profile, setProfile] = useState(null);
  const [selectedMetric, setSelectedMetric] =
    useState("session_count");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const isFaculty =
    currentUser?.role?.toLowerCase() === "faculty";

  const navigation = isFaculty
    ? [
      { name: "Dashboard", icon: LayoutDashboard },
      { name: "Faculty", icon: UserRound },
      { name: "New Assessment", icon: Sparkles },
      { name: "Alerts", icon: Bell },
      { name: "Profile", icon: UserRound },
    ]
    : [
      { name: "Dashboard", icon: LayoutDashboard },
      { name: "Behaviour", icon: Activity },
      { name: "Insights", icon: Lightbulb },
      { name: "Alerts", icon: Bell },
      { name: "Profile", icon: UserRound },
    ];


  useEffect(() => {
    if (!currentUser) {
      return;
    }

    async function fetchDashboard() {
      try {
        setLoading(true);
        setError("");

        const userId = currentUser.user_id;

        // ------------------------------------------
        // Dashboard
        // ------------------------------------------

        const dashboardResponse = await fetch(
          `${API_BASE_URL}/dashboard/${userId}`
        );

        if (!dashboardResponse.ok) {
          throw new Error(
            "Failed to fetch dashboard data"
          );
        }

        const dashboardData =
          await dashboardResponse.json();

        setDashboard(dashboardData);

        // ------------------------------------------
        // Behaviour trend
        // ------------------------------------------

        const trendResponse = await fetch(
          `${API_BASE_URL}/trend/${userId}`
        );

        if (trendResponse.ok) {
          const trendData =
            await trendResponse.json();

          setTrend(trendData);
        } else if (trendResponse.status === 404) {
          // New student may not have behaviour history yet
          setTrend([]);
        } else {
          throw new Error(
            "Failed to fetch trend data"
          );
        }

        // ------------------------------------------
        // SHAP explanation
        // ------------------------------------------

        const explanationResponse = await fetch(
          `${API_BASE_URL}/explanation/${userId}`
        );

        if (explanationResponse.ok) {
          const explanationData =
            await explanationResponse.json();

          setExplanation(
            explanationData.explanations || []
          );
        } else if (
          explanationResponse.status === 404
        ) {
          setExplanation([]);
        } else {
          throw new Error(
            "Failed to fetch explanation data"
          );
        }

      } catch (err) {
        console.error(err);

        setError(
          err.message ||
          "Unable to connect to the backend."
        );
      } finally {
        setLoading(false);
      }
    }

    fetchDashboard();

  }, [currentUser, API_BASE_URL]);

  if (!currentUser) {
    return (
      <AuthPage
        apiBaseUrl={API_BASE_URL}
        onLogin={handleLogin}
      />
    );
  }

  if (loading) {
    return (
      <div className="loading-screen">
        Loading dashboard...
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="loading-screen">
        <p>{error || "No dashboard data available."}</p>
      </div>
    );
  }

  const behaviorState =
    dashboard.prediction?.behavior_state || "Not available";

  const anomalyIsNormal =
    dashboard.anomaly?.anomaly_flag === 1;

  const anomalyStatus = dashboard.anomaly
    ? anomalyIsNormal
      ? "Normal"
      : "Unusual"
    : "Not available";

  const alertPriority =
    dashboard.alert?.priority || "Not available";

  // Calculate the maximum SHAP magnitude once
  const maxShapValue =
    explanation.length > 0
      ? Math.max(
        ...explanation.map((item) =>
          Math.abs(item.shap_value)
        )
      )
      : 0;

  return (
    <div className="app">
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`sidebar ${sidebarOpen ? "sidebar-open" : ""
          }`}
      >
        <div className="brand">
          <div className="brand-mark">
            <Activity size={20} />
          </div>

          <div>
            <strong>PRJ-221</strong>
            <span>Behaviour Monitor</span>
          </div>

          <button
            className="close-sidebar"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="navigation">
          <span className="nav-label">WORKSPACE</span>

          {navigation.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.name;

            return (
              <button
                key={item.name}
                className={`nav-item ${active ? "active" : ""
                  }`}
                onClick={() => {
                  setActivePage(item.name);
                  setSidebarOpen(false);
                }}
              >
                <Icon size={19} />
                <span>{item.name}</span>

                {item.name === "Alerts" && (
                  <span className="notification-dot" />
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-indicator" />

            <div>
              <strong>System online</strong>
              <span>AI services connected</span>
            </div>
          </div>
        </div>
      </aside>

      <div className="main-wrapper">
        <header className="topbar">
          <button
            className="menu-button"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={21} />
          </button>

          <div className="breadcrumb">
            <span>Workspace</span>
            <span>/</span>
            <strong>{activePage}</strong>
          </div>

          <div className="topbar-actions">
            <button className="icon-button">
              <Bell size={19} />
              <span className="bell-dot" />
            </button>

            <div className="topbar-user">
              <div className="mini-avatar">U</div>

              <div className="topbar-user-info">
                <strong>{currentUser.name}</strong>
                <span>{currentUser.role}</span>
              </div>

              <ChevronDown size={16} />
            </div>
          </div>
        </header>

        <main className="content">
          {activePage === "Dashboard" && isFaculty ? (
            <FacultyOverview apiBaseUrl={API_BASE_URL} />
          ) : activePage === "Behaviour" ? (
            <BehaviourPage trend={trend} />
          ) : activePage === "New Assessment" ? (
            <NewPredictionPage apiBaseUrl={API_BASE_URL} />
          ) : activePage === "Faculty" ? (
            <FacultyDashboard apiBaseUrl={API_BASE_URL} />
          ) : activePage === "Insights" ? (
            <InsightsPage
              dashboard={dashboard}
              explanation={explanation}
            />
          ) : activePage === "Alerts" ? (
            <AlertsPage
              dashboard={dashboard}
              isFaculty={isFaculty}
              apiBaseUrl={API_BASE_URL}
            />
          ) : activePage === "Profile" ? (
            <ProfilePage user={profile || dashboard.user} />
          ) : (
            <>
              <section className="page-heading">
                <div>
                  <div className="eyebrow">
                    <Sparkles size={14} />
                    AI-powered behavioural insights
                  </div>

                  <h1>Behaviour overview</h1>

                  <p>
                    Monitor behavioural patterns, changes and model
                    insights across course sequences.
                  </p>
                </div>

                <div className="date-info">
                  <span>Monitoring user</span>
                  <strong>{dashboard.user.name}</strong>
                </div>
              </section>

              <section className="metrics-grid">
                <div className="metric-card state-card">
                  <div className="metric-top">
                    <span>Behaviour state</span>

                    <div className="metric-icon">
                      <Activity size={18} />
                    </div>
                  </div>

                  <div className="metric-value">
                    {behaviorState}
                  </div>

                  <div className="metric-description">
                    Current predicted state
                  </div>

                  <div
                    className={`state-badge ${behaviorState.toLowerCase()}`}
                  >
                    <span />
                    Monitoring
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-top">
                    <span>Behavioural Change Index</span>

                    <div className="metric-icon">
                      <ArrowUpRight size={18} />
                    </div>
                  </div>

                  <div className="metric-value">
                    {dashboard.prediction?.bci != null
                      ? Number(dashboard.prediction.bci).toFixed(4)
                      : "—"}
                  </div>

                  <div className="metric-description">
                    Relative change across behaviour features
                  </div>

                  <div className="metric-footnote">
                    Data-driven indicator
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-top">
                    <span>Pattern status</span>

                    <div className="metric-icon">
                      <ShieldCheck size={18} />
                    </div>
                  </div>

                  <div className="metric-value">
                    {anomalyStatus}
                  </div>

                  <div className="metric-description">
                    Isolation Forest result
                  </div>

                  <div className="metric-footnote">
                    Score:{" "}
                    {dashboard.anomaly?.anomaly_score != null
                      ? Number(dashboard.anomaly.anomaly_score).toFixed(4)
                      : "—"}
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-top">
                    <span>Alert priority</span>

                    <div className="metric-icon">
                      <Bell size={18} />
                    </div>
                  </div>

                  <div className="metric-value">
                    {dashboard.alert?.priority || "Not available"}
                  </div>

                  <div className="metric-description">
                    Current monitoring priority
                  </div>

                  <div className="priority-line">
                    <span
                      className={
                        alertPriority === "Low"
                          ? "priority-active"
                          : ""
                      }
                    />

                    <span
                      className={
                        alertPriority === "Medium"
                          ? "priority-active"
                          : ""
                      }
                    />

                    <span
                      className={
                        alertPriority === "High"
                          ? "priority-active"
                          : ""
                      }
                    />
                  </div>
                </div>
              </section>

              <section className="dashboard-grid">
                <div className="panel trend-panel">
                  <div className="panel-header">
                    <div>
                      <span className="panel-kicker">
                        Behaviour over time
                      </span>

                      <h2>Activity trend</h2>

                      <p>
                        Behavioural activity across sequential
                        courses
                      </p>
                    </div>

                    <select
                      className="select-button"
                      value={selectedMetric}
                      onChange={(event) =>
                        setSelectedMetric(
                          event.target.value
                        )
                      }
                    >
                      {TREND_METRICS.map((metric) => (
                        <option
                          key={metric.key}
                          value={metric.key}
                        >
                          {metric.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="chart-area">
                    <ResponsiveContainer
                      width="100%"
                      height={300}
                    >
                      <LineChart
                        data={trend}
                        margin={{
                          top: 10,
                          right: 10,
                          left: 0,
                          bottom: 10,
                        }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />

                        <XAxis
                          dataKey="sequence"
                          tickFormatter={(value) =>
                            `Seq ${value}`
                          }
                        />

                        <YAxis />

                        <Tooltip
                          labelFormatter={(value) =>
                            `Sequence ${value}`
                          }
                          formatter={(value) => [
                            Number(
                              value
                            ).toLocaleString(),
                            TREND_METRICS.find(
                              (metric) =>
                                metric.key ===
                                selectedMetric
                            )?.label ||
                            selectedMetric,
                          ]}
                        />

                        <Line
                          type="monotone"
                          dataKey={selectedMetric}
                          stroke="currentColor"
                          strokeWidth={3}
                          dot={{ r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="panel recommendation-panel">
                  <div className="panel-header compact">
                    <div>
                      <span className="panel-kicker">
                        Decision support
                      </span>

                      <h2>Recommendation</h2>
                    </div>

                    <div className="recommendation-icon">
                      <Lightbulb size={19} />
                    </div>
                  </div>

                  <div className="recommendation-content">
                    <div className="recommendation-status">
                      {behaviorState === "Not available"
                        ? "Monitoring not started"
                        : `${behaviorState} behaviour`}
                    </div>

                    <p>
                      {dashboard.recommendation?.recommendation ||
                        "No recommendation is available yet. Behavioural monitoring data has not been recorded for this account."}
                    </p>

                    <div className="recommendation-note">
                      <ShieldCheck size={15} />
                      Rule-based recommendation
                    </div>
                  </div>
                </div>

                <div className="panel shap-panel">
                  <div className="panel-header">
                    <div>
                      <span className="panel-kicker">
                        Explainable AI
                      </span>

                      <h2>Why this prediction?</h2>

                      <p>
                        Features with the strongest
                        contribution to the current prediction
                      </p>
                    </div>

                    <span className="model-tag">
                      Random Forest
                    </span>
                  </div>

                  <div className="shap-list">
                    {explanation.map((item) => {
                      const width =
                        maxShapValue === 0
                          ? 0
                          : (Math.abs(
                            item.shap_value
                          ) /
                            maxShapValue) *
                          100;

                      return (
                        <div
                          className="shap-item"
                          key={item.feature}
                        >
                          <div className="shap-info">
                            <span>{item.feature}</span>

                            <strong>
                              {item.shap_value >= 0
                                ? "+"
                                : ""}
                              {item.shap_value.toFixed(4)}
                            </strong>
                          </div>

                          <div className="shap-track">
                            <div
                              className="shap-fill"
                              style={{
                                width: `${width}%`,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="panel anomaly-panel">
                  <div className="panel-header compact">
                    <div>
                      <span className="panel-kicker">
                        Pattern detection
                      </span>

                      <h2>Anomaly status</h2>
                    </div>

                    <div className="normal-badge">
                      <span />

                      {!dashboard.anomaly
                        ? "Not available"
                        : anomalyIsNormal
                          ? "Normal"
                          : "Unusual"}
                    </div>
                  </div>

                  <div className="anomaly-score">
                    <span>Anomaly score</span>

                    <strong>
                      {dashboard.anomaly?.anomaly_score != null
                        ? Number(
                          dashboard.anomaly.anomaly_score
                        ).toFixed(4)
                        : "—"}
                    </strong>
                  </div>

                  <p className="anomaly-description">
                    {!dashboard.anomaly
                      ? "No behavioural monitoring data is available yet."
                      : anomalyIsNormal
                        ? "No unusual behavioural pattern was detected for this monitoring period."
                        : "An unusual behavioural pattern was detected. Review recent activity for context."}
                  </p>

                  <div className="anomaly-scale">
                    <div className="scale-track">
                      <div className="scale-marker" />
                    </div>

                    <div className="scale-labels">
                      <span>More unusual</span>
                      <span>Less unusual</span>
                    </div>
                  </div>
                </div>
              </section>

              <footer className="dashboard-footer">
                <span>
                  PRJ-221 Behavioural Change Monitoring Software
                </span>

                <span>
                  AI-assisted decision support • Not a diagnosis
                </span>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;