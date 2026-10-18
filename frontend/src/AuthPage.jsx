import { useState } from "react";
import { ArrowRight, ShieldCheck, UserPlus, UserRound } from "lucide-react";

import "./AuthPage.css";

export default function AuthPage({ apiBaseUrl, onLogin }) {
  const [mode, setMode] = useState("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const resetForm = () => {
    setName("");
    setEmail("");
    setPassword("");
    setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (mode === "register" && !name.trim()) {
      setError("Please enter your name.");
      return;
    }

    if (!email.trim()) {
      setError("Please enter your email.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setLoading(true);

      const endpoint =
        mode === "login"
          ? `${apiBaseUrl}/login`
          : `${apiBaseUrl}/register`;

      const payload =
        mode === "login"
          ? {
              email,
              password
            }
          : {
              name,
              email,
              password
            };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed."
        );
      }

      if (mode === "login") {
        if (data.user && data.access_token) {
          localStorage.setItem("prj221_token", data.access_token);
          onLogin(data.user, data.access_token);
        }
      } else {
        setMode("login");
        setPassword("");
        setError(
          "Account created successfully. Please log in."
        );
      }
    } catch (err) {
      setError(
        err.message || "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode((previous) =>
      previous === "login" ? "register" : "login"
    );

    resetForm();
  };

  return (
    <div className="auth-page">
      <div className="auth-shell">

        <div className="auth-brand-panel">
          <div className="auth-brand-icon">
            <ShieldCheck size={24} />
          </div>

          <span className="auth-eyebrow">
            PRJ_221
          </span>

          <h1>
            Behavioural Change
            <br />
            Monitoring Software
          </h1>

          <p>
            A behavioural monitoring platform for
            longitudinal learning activity, model-based
            prediction and student support.
          </p>

          <div className="auth-feature">
            <ShieldCheck size={17} />
            <span>Secure role-based access</span>
          </div>

          <div className="auth-feature">
            <ShieldCheck size={17} />
            <span>Behavioural pattern monitoring</span>
          </div>

          <div className="auth-feature">
            <ShieldCheck size={17} />
            <span>Explainable ML predictions</span>
          </div>
        </div>

        <div className="auth-form-panel">

          <div className="auth-form-header">
            <span className="auth-form-eyebrow">
              {mode === "login"
                ? "Welcome back"
                : "Create account"}
            </span>

            <h2>
              {mode === "login"
                ? "Sign in"
                : "Register as a student"}
            </h2>

            <p>
              {mode === "login"
                ? "Enter your account details to continue."
                : "Create your student account to access the monitoring workspace."}
            </p>
          </div>

          {mode === "login" && (
            <div className="auth-role-presets">
              <span className="auth-presets-title">Quick Portal Access:</span>
              <div className="auth-preset-buttons">
                <button
                  type="button"
                  className="preset-btn student-preset"
                  onClick={() => {
                    setEmail("00050f0e@example.com");
                    setPassword("Student123!");
                    setError("");
                  }}
                >
                  <UserRound size={15} />
                  <span>Login as Student</span>
                </button>
                <button
                  type="button"
                  className="preset-btn faculty-preset"
                  onClick={() => {
                    setEmail("testfaculty@example.com");
                    setPassword("Faculty123!");
                    setError("");
                  }}
                >
                  <ShieldCheck size={15} />
                  <span>Login as Faculty</span>
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>

            {mode === "register" && (
              <div className="auth-field">
                <label htmlFor="name">
                  Full Name
                </label>

                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  placeholder="Enter your full name"
                />
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="Enter your email"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="password">
                Password
              </label>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div
                className={
                  error.startsWith("Account created")
                    ? "auth-message success"
                    : "auth-message"
                }
              >
                {error}
              </div>
            )}

            <button
              className="auth-submit-button"
              type="submit"
              disabled={loading}
            >
              {loading ? (
                "Please wait..."
              ) : mode === "login" ? (
                <>
                  Sign In
                  <ArrowRight size={17} />
                </>
              ) : (
                <>
                  Create Account
                  <UserPlus size={17} />
                </>
              )}
            </button>
          </form>

          <div className="auth-switch">
            <span>
              {mode === "login"
                ? "Don't have a student account?"
                : "Already have an account?"}
            </span>

            <button
              type="button"
              onClick={switchMode}
            >
              {mode === "login"
                ? "Register"
                : "Sign in"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}