import { apiFetch } from "./api";
import { useEffect, useMemo, useState } from "react";
import {
  Users,
  TrendingUp,
  Minus,
  TrendingDown,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw
} from "lucide-react";

import "./FacultyOverview.css";

export default function FacultyOverview({ apiBaseUrl }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchStudents = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `${apiBaseUrl}/faculty/students`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load faculty monitoring data."
        );
      }

      const data = await response.json();
      setStudents(data);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [apiBaseUrl]);

  const summary = useMemo(() => {
    return {
      total: students.length,

      improving: students.filter(
        (student) =>
          student.behavior_state === "Improving"
      ).length,

      stable: students.filter(
        (student) =>
          student.behavior_state === "Stable"
      ).length,

      declining: students.filter(
        (student) =>
          student.behavior_state === "Declining"
      ).length,

      elevated: students.filter(
        (student) =>
          student.priority === "Medium" ||
          student.priority === "High"
      ).length
    };
  }, [students]);

  const recentStudents = students.slice(0, 8);

  if (loading) {
    return (
      <div className="faculty-overview-state">
        <RefreshCw size={20} />
        <p>Loading faculty dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="faculty-overview-state">
        <AlertTriangle size={20} />
        <p>{error}</p>

        <button onClick={fetchStudents}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="faculty-overview-page">

      <section className="faculty-overview-header">
        <div>
          <span className="faculty-overview-eyebrow">
            Faculty Workspace
          </span>

          <h1>Faculty Dashboard</h1>

          <p>
            Overview of behavioural monitoring across
            the students currently available in the system.
          </p>
        </div>

        <button
          className="faculty-overview-refresh"
          onClick={fetchStudents}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </section>

      <section className="faculty-overview-summary">

        <div className="faculty-overview-card">
          <Users size={19} />
          <span>Total Students</span>
          <strong>{summary.total}</strong>
        </div>

        <div className="faculty-overview-card">
          <TrendingUp size={19} />
          <span>Improving</span>
          <strong>{summary.improving}</strong>
        </div>

        <div className="faculty-overview-card">
          <Minus size={19} />
          <span>Stable</span>
          <strong>{summary.stable}</strong>
        </div>

        <div className="faculty-overview-card">
          <TrendingDown size={19} />
          <span>Declining</span>
          <strong>{summary.declining}</strong>
        </div>

        <div className="faculty-overview-card">
          <AlertTriangle size={19} />
          <span>Elevated Priority</span>
          <strong>{summary.elevated}</strong>
        </div>

      </section>

      <section className="faculty-overview-panel">

        <div className="faculty-overview-panel-header">
          <div>
            <span>Monitoring snapshot</span>
            <h2>Student overview</h2>
          </div>

          <span>
            {students.length} students
          </span>
        </div>

        <div className="faculty-overview-table-wrap">
          <table className="faculty-overview-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Behaviour</th>
                <th>BCI</th>
                <th>Priority</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {recentStudents.map((student) => (
                <tr key={student.user_id}>

                  <td>
                    <div className="faculty-overview-student">
                      <div className="faculty-overview-avatar">
                        {student.name
                          ?.charAt(0)
                          .toUpperCase() || "U"}
                      </div>

                      <div>
                        <strong>{student.name}</strong>
                        <span>{student.user_id}</span>
                      </div>
                    </div>
                  </td>

                  <td>
                    {student.behavior_state ||
                      "Not available"}
                  </td>

                  <td>
                    {student.bci !== null &&
                    student.bci !== undefined
                      ? Number(
                          student.bci
                        ).toFixed(3)
                      : "—"}
                  </td>

                  <td>
                    {student.priority ||
                      "Not available"}
                  </td>

                  <td>
                    <ArrowUpRight size={17} />
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