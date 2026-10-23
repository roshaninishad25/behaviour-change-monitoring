import { apiFetch } from "./api";
import { useEffect, useMemo, useState } from "react";
import {
  Search,
  Users,
  TrendingUp,
  Minus,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  ArrowUpRight
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from "recharts";



import FacultyStudentDetails from "./FacultyStudentDetails";
import "./FacultyDashboard.css";

export default function FacultyDashboard({ apiBaseUrl }) {
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [stateFilter, setStateFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");

  const fetchStudents = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `${apiBaseUrl}/faculty/students`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch faculty student data.");
      }

      const data = await response.json();

      setStudents(data);
    } catch (err) {
      setError(
        err.message || "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await apiFetch(`${apiBaseUrl}/faculty/students`);
        if (!response.ok) {
          throw new Error("Failed to fetch faculty student data.");
        }
        const data = await response.json();
        if (isMounted) setStudents(data);
      } catch (err) {
        if (isMounted) setError(err.message || "Unable to connect to the backend.");
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadData();
    return () => { isMounted = false; };
  }, [apiBaseUrl]);

  const summary = useMemo(() => {
    return {
      total: students.length,

      improving: students.filter(
        (student) => student.behavior_state === "Improving"
      ).length,

      stable: students.filter(
        (student) => student.behavior_state === "Stable"
      ).length,

      declining: students.filter(
        (student) => student.behavior_state === "Declining"
      ).length,

      elevated: students.filter(
        (student) =>
          student.priority === "Medium" ||
          student.priority === "High"
      ).length
    };
  }, [students]);

  const filteredStudents = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();

    return students.filter((student) => {
      const matchesSearch =
        !search ||
        student.user_id.toLowerCase().includes(search) ||
        student.name.toLowerCase().includes(search) ||
        student.email.toLowerCase().includes(search);

      const matchesState =
        stateFilter === "All" ||
        student.behavior_state === stateFilter;

      const matchesPriority =
        priorityFilter === "All" ||
        student.priority === priorityFilter;

      return (
        matchesSearch &&
        matchesState &&
        matchesPriority
      );
    });
  }, [
    students,
    searchTerm,
    stateFilter,
    priorityFilter
  ]);

  const behaviourChartData = [
    {
      state: "Improving",
      students: summary.improving
    },
    {
      state: "Stable",
      students: summary.stable
    },
    {
      state: "Declining",
      students: summary.declining
    }
  ];

  const priorityChartData = [
    {
      priority: "Low",
      students: students.filter(
        (student) => student.priority === "Low"
      ).length
    },
    {
      priority: "Medium",
      students: students.filter(
        (student) => student.priority === "Medium"
      ).length
    },
    {
      priority: "High",
      students: students.filter(
        (student) => student.priority === "High"
      ).length
    }
  ];

  const getStateIcon = (state) => {
    if (state === "Improving") {
      return <TrendingUp size={16} />;
    }

    if (state === "Declining") {
      return <TrendingDown size={16} />;
    }

    return <Minus size={16} />;
  };

  const getPriorityClass = (priority) => {
    if (priority === "High") {
      return "priority-high";
    }

    if (priority === "Medium") {
      return "priority-medium";
    }

    return "priority-low";
  };

  if (selectedStudentId) {
    return (
      <FacultyStudentDetails
        apiBaseUrl={apiBaseUrl}
        studentId={selectedStudentId}
        onBack={() => setSelectedStudentId(null)}
      />
    );
  }
  return (
    <div className="faculty-page">

      {/* Header */}
      <section className="faculty-header">
        <div>
          <span className="faculty-eyebrow">
            Faculty Workspace
          </span>

          <h1>Student Monitoring</h1>

          <p>
            Monitor behavioural patterns, prediction states,
            anomaly signals and monitoring priorities across
            the students in the system.
          </p>
        </div>

        <button
          className="faculty-refresh-button"
          onClick={fetchStudents}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </section>

      {/* Summary cards */}
      <section className="faculty-summary-grid">

        <div className="faculty-summary-card">
          <div className="faculty-summary-icon">
            <Users size={19} />
          </div>

          <div>
            <span>Total Students</span>
            <strong>{summary.total}</strong>
          </div>
        </div>

        <div className="faculty-summary-card">
          <div className="faculty-summary-icon">
            <TrendingUp size={19} />
          </div>

          <div>
            <span>Improving</span>
            <strong>{summary.improving}</strong>
          </div>
        </div>

        <div className="faculty-summary-card">
          <div className="faculty-summary-icon">
            <Minus size={19} />
          </div>

          <div>
            <span>Stable</span>
            <strong>{summary.stable}</strong>
          </div>
        </div>

        <div className="faculty-summary-card">
          <div className="faculty-summary-icon">
            <TrendingDown size={19} />
          </div>

          <div>
            <span>Declining</span>
            <strong>{summary.declining}</strong>
          </div>
        </div>

        <div className="faculty-summary-card">
          <div className="faculty-summary-icon">
            <AlertTriangle size={19} />
          </div>

          <div>
            <span>Elevated Priority</span>
            <strong>{summary.elevated}</strong>
          </div>
        </div>

      </section>

      {/* Faculty summary charts */}
      <section className="faculty-chart-grid">

        <div className="faculty-chart-card">

          <div className="faculty-chart-header">
            <div>
              <span>Behaviour distribution</span>
              <h2>Student behaviour states</h2>
            </div>
          </div>

          <div className="faculty-chart">
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <BarChart
                data={behaviourChartData}
                margin={{
                  top: 10,
                  right: 15,
                  left: 0,
                  bottom: 10
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="state" />

                <YAxis allowDecimals={false} />

                <Tooltip />

                <Bar
                  dataKey="students"
                  fill="currentColor"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

        </div>


        <div className="faculty-chart-card">

          <div className="faculty-chart-header">
            <div>
              <span>Monitoring priority</span>
              <h2>Priority distribution</h2>
            </div>
          </div>

          <div className="faculty-chart">
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <BarChart
                data={priorityChartData}
                margin={{
                  top: 10,
                  right: 15,
                  left: 0,
                  bottom: 10
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="priority" />

                <YAxis allowDecimals={false} />

                <Tooltip />

                <Bar
                  dataKey="students"
                  fill="currentColor"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

        </div>

      </section>

      {/* Student monitoring table */}
      <section className="faculty-table-card">

        <div className="faculty-table-header">

          <div>
            <span className="faculty-section-label">
              Student Overview
            </span>

            <h2>Students</h2>
          </div>

          <span className="faculty-result-count">
            {filteredStudents.length} shown
          </span>

        </div>

        {/* Filters */}
        <div className="faculty-filters">

          <div className="faculty-search">
            <Search size={17} />

            <input
              type="text"
              placeholder="Search by student ID, name or email..."
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
            />
          </div>

          <select
            value={stateFilter}
            onChange={(event) =>
              setStateFilter(event.target.value)
            }
          >
            <option value="All">All states</option>
            <option value="Improving">Improving</option>
            <option value="Stable">Stable</option>
            <option value="Declining">Declining</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(event) =>
              setPriorityFilter(event.target.value)
            }
          >
            <option value="All">All priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>

        </div>

        {/* Loading */}
        {loading && (
          <div className="faculty-empty-state">
            <RefreshCw size={20} />
            <p>Loading student monitoring data...</p>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="faculty-error-state">
            <AlertTriangle size={20} />
            <p>{error}</p>

            <button onClick={fetchStudents}>
              Try Again
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading &&
          !error &&
          filteredStudents.length === 0 && (
            <div className="faculty-empty-state">
              <Users size={22} />
              <p>No students match the current filters.</p>
            </div>
          )}

        {/* Table */}
        {!loading &&
          !error &&
          filteredStudents.length > 0 && (
            <div className="faculty-table-wrapper">

              <table className="faculty-table">

                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Behaviour State</th>
                    <th>BCI</th>
                    <th>Anomaly</th>
                    <th>Priority</th>
                    <th></th>
                  </tr>
                </thead>

                <tbody>
                  {filteredStudents.map((student) => (
                    <tr key={student.user_id}>

                      <td>
                        <div className="faculty-student-cell">
                          <div className="faculty-avatar">
                            {student.name
                              ? student.name
                                .charAt(0)
                                .toUpperCase()
                              : "U"}
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
                      </td>

                      <td>
                        <div
                          className={`faculty-state faculty-state-${String(
                            student.behavior_state || "Unknown"
                          ).toLowerCase()}`}
                        >
                          {getStateIcon(
                            student.behavior_state
                          )}

                          <span>
                            {student.behavior_state ||
                              "Unavailable"}
                          </span>
                        </div>
                      </td>

                      <td>
                        <strong className="faculty-bci">
                          {student.bci !== null &&
                            student.bci !== undefined
                            ? Number(
                              student.bci
                            ).toFixed(3)
                            : "—"}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={
                            student.anomaly_flag === -1
                              ? "faculty-anomaly anomalous"
                              : "faculty-anomaly normal"
                          }
                        >
                          {student.anomaly_flag === -1
                            ? "Anomalous"
                            : "Normal"}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`faculty-priority ${getPriorityClass(
                            student.priority
                          )}`}
                        >
                          {student.priority ||
                            "Unavailable"}
                        </span>
                      </td>

                      <td>
                        <button
                          className="faculty-view-button"
                          title="View student"
                          onClick={() =>
                            setSelectedStudentId(student.user_id)
                          }
                        >
                          <ArrowUpRight size={17} />
                        </button>
                      </td>

                    </tr>
                  ))}
                </tbody>

              </table>

            </div>
          )}

      </section>
    </div>
  );
}