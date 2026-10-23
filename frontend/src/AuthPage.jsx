import { useState } from "react";
import { ArrowRight, ShieldCheck, UserPlus, UserRound, KeyRound } from "lucide-react";

import "./AuthPage.css";

/**
 * AuthPage — B1/B2/B7
 *
 * Handles three modes:
 *   "login"          — POST /auth/login
 *   "register"       — POST /auth/signup  (student self-registration)
 *   "facultyRegister"— POST /auth/signup/faculty (invite-code gated)
 *
 * After a successful login the onLogin callback receives (user, token) so
 * the parent App can store the token and switch to the dashboard.
 *
 * After a successful registration the form switches back to "login" with a
 * success message — the user must then log in explicitly.
 */
export default function AuthPage({ apiBaseUrl, onLogin }) {
  // "login" | "register" | "facultyRegister"
  const [mode, setMode] = useState("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState(""); // B1 — faculty invite code

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const resetForm = () => {
    setName("");
    setEmail("");
    setPassword("");
    setInviteCode("");
    setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    // Client-side validation
    if (mode !== "login" && !name.trim()) {
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
    if (mode === "facultyRegister" && !inviteCode.trim()) {
      setError("Please enter the faculty invite code.");
      return;
    }

    try {
      setLoading(true);

      // Choose the correct backend endpoint
      let endpoint;
      let payload;

      if (mode === "login") {
        endpoint = `${apiBaseUrl}/auth/login`;
        payload = { email, password };
      } else if (mode === "register") {
        endpoint = `${apiBaseUrl}/auth/signup`;
        payload = { name, email, password };
      } else {
        // facultyRegister
        endpoint = `${apiBaseUrl}/auth/signup/faculty`;
        payload = { name, email, password, invite_code: inviteCode };
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }

      if (mode === "login") {
        // B2 — Store token and hand user object up to App
        if (data.user && data.access_token) {
          localStorage.setItem("prj221_token", data.access_token);
          onLogin(data.user, data.access_token);
        }
      } else {
        // Registration successful — redirect to login
        setMode("login");
        setPassword("");
        setInviteCode("");
        setError("Account created successfully. Please log in.");
      }
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (target) => {
    setMode(target);
    resetForm();
  };

  // Human-readable heading strings
  const heading = {
    login: "Sign in",
    register: "Register as a student",
    facultyRegister: "Register as faculty",
  }[mode];

  const subheading = {
    login: "Enter your account details to continue.",
    register: "Create your student account to access the monitoring workspace.",
    facultyRegister:
      "Enter your details and the faculty invite code provided by your administrator.",
  }[mode];

  const eyebrow = {
    login: "Welcome back",
    register: "Create account",
    facultyRegister: "Faculty account",
  }[mode];

  return (
    <div className="auth-page">
      <div className="auth-shell">

        {/* Brand panel */}
        <div className="auth-brand-panel">
          <div className="auth-brand-icon">
            <ShieldCheck size={24} />
          </div>

          <span className="auth-eyebrow">PRJ_221</span>

          <h1>
            Behavioural Change
            <br />
            Monitoring Software
          </h1>

          <p>
            A behavioural monitoring platform for longitudinal learning
            activity, model-based prediction and student support.
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

        {/* Form panel */}
        <div className="auth-form-panel">

          <div className="auth-form-header">
            <span className="auth-form-eyebrow">{eyebrow}</span>
            <h2>{heading}</h2>
            <p>{subheading}</p>
          </div>

          {/* Quick-access preset buttons (login mode only) */}
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

            {/* Name field — registration modes only */}
            {mode !== "login" && (
              <div className="auth-field">
                <label htmlFor="name">Full Name</label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Enter your full name"
                />
              </div>
            )}

            {/* Email */}
            <div className="auth-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Enter your email"
              />
            </div>

            {/* Password */}
            <div className="auth-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={
                  mode === "login"
                    ? "Enter your password"
                    : "At least 8 characters"
                }
              />
            </div>

            {/* Faculty invite code — facultyRegister mode only */}
            {mode === "facultyRegister" && (
              <div className="auth-field">
                <label htmlFor="inviteCode">Faculty Invite Code</label>
                <input
                  id="inviteCode"
                  type="password"
                  value={inviteCode}
                  onChange={(event) => setInviteCode(event.target.value)}
                  placeholder="Enter the faculty invite code"
                />
              </div>
            )}

            {/* Error / success message */}
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
              ) : mode === "register" ? (
                <>
                  Create Student Account
                  <UserPlus size={17} />
                </>
              ) : (
                <>
                  Create Faculty Account
                  <KeyRound size={17} />
                </>
              )}
            </button>
          </form>

          {/* Mode switcher links */}
          <div className="auth-switch">
            {mode === "login" && (
              <>
                <span>Don't have a student account?</span>
                <button type="button" onClick={() => switchMode("register")}>
                  Register as student
                </button>
                <span style={{ margin: "0 6px", opacity: 0.4 }}>•</span>
                <button type="button" onClick={() => switchMode("facultyRegister")}>
                  Faculty registration
                </button>
              </>
            )}
            {mode === "register" && (
              <>
                <span>Already have an account?</span>
                <button type="button" onClick={() => switchMode("login")}>
                  Sign in
                </button>
              </>
            )}
            {mode === "facultyRegister" && (
              <>
                <span>Already have an account?</span>
                <button type="button" onClick={() => switchMode("login")}>
                  Sign in
                </button>
              </>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
