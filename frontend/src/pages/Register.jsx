import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL;

function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API}/register/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMessage = "Registration failed.";

        if (data.username) {
          errorMessage = data.username[0];
        } else if (data.email) {
          errorMessage = data.email[0];
        } else if (data.password) {
          errorMessage = data.password[0];
        } else if (data.detail) {
          errorMessage = data.detail;
        }

        setError(errorMessage);
        return;
      }

      setSuccess(
        "Account created successfully! Redirecting to login..."
      );

      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (error) {
      console.error("Registration error:", error);

      setError(
        "Unable to connect to the server. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>

        {/* Logo */}
        <div style={styles.logo}>
          💰
        </div>

        {/* Heading */}
        <h1 style={styles.title}>
          Create Account
        </h1>

        <p style={styles.subtitle}>
          Create your BudgetBuddy account
        </p>

        {/* Error */}
        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

        {/* Success */}
        {success && (
          <div style={styles.success}>
            {success}
          </div>
        )}

        <form onSubmit={handleRegister}>

          {/* Username */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              Username
            </label>

            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
              required
              style={styles.input}
            />
          </div>

          {/* Email */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              Email
            </label>

            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
              style={styles.input}
            />
          </div>

          {/* Password */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              Password
            </label>

            <div style={styles.passwordBox}>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                required
                style={styles.passwordInput}
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword(!showPassword)
                }
                style={styles.showButton}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              Confirm Password
            </label>

            <div style={styles.passwordBox}>
              <input
                type={
                  showConfirmPassword
                    ? "text"
                    : "password"
                }
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value
                  )
                }
                required
                style={styles.passwordInput}
              />

              <button
                type="button"
                onClick={() =>
                  setShowConfirmPassword(
                    !showConfirmPassword
                  )
                }
                style={styles.showButton}
              >
                {showConfirmPassword
                  ? "Hide"
                  : "Show"}
              </button>
            </div>
          </div>

          {/* Register Button */}
          <button
            type="submit"
            disabled={loading}
            style={styles.registerButton}
          >
            {loading
              ? "Creating Account..."
              : "Create Account"}
          </button>

        </form>

        {/* Login Section */}
        <div style={styles.loginSection}>
          <p style={styles.loginText}>
            Already have an account?
          </p>

          <button
            type="button"
            onClick={() => navigate("/login")}
            style={styles.loginButton}
          >
            Sign In
          </button>
        </div>

      </div>
    </div>
  );
}

/* =====================================================
   STYLES
===================================================== */

const styles = {

  page: {
    minHeight: "100vh",
    width: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f4f7fb",
    padding: "30px",
    boxSizing: "border-box",
  },

  card: {
    width: "430px",
    maxWidth: "100%",
    backgroundColor: "#ffffff",
    padding: "40px",
    borderRadius: "14px",
    boxShadow: "0 8px 25px rgba(0, 0, 0, 0.08)",
    boxSizing: "border-box",
    border: "1px solid #e5e7eb",
  },

  logo: {
    width: "65px",
    height: "65px",
    margin: "0 auto 15px",
    borderRadius: "50%",
    backgroundColor: "#eaf2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "32px",
  },

  title: {
    textAlign: "center",
    margin: "0",
    fontSize: "30px",
    fontWeight: "700",
    color: "#1e293b",
  },

  subtitle: {
    textAlign: "center",
    marginTop: "8px",
    marginBottom: "30px",
    color: "#64748b",
    fontSize: "15px",
  },

  formGroup: {
    marginBottom: "20px",
  },

  label: {
    display: "block",
    marginBottom: "8px",
    fontSize: "15px",
    fontWeight: "600",
    color: "#334155",
  },

  input: {
    width: "100%",
    height: "48px",
    padding: "0 14px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    fontSize: "15px",
    boxSizing: "border-box",
    outline: "none",
    backgroundColor: "#ffffff",
    color: "#1e293b",
  },

  passwordBox: {
    display: "flex",
    height: "48px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    overflow: "hidden",
    backgroundColor: "#ffffff",
  },

  passwordInput: {
    flex: "1",
    padding: "0 14px",
    border: "none",
    outline: "none",
    fontSize: "15px",
    minWidth: "0",
    color: "#1e293b",
  },

  showButton: {
    border: "none",
    borderLeft: "1px solid #e2e8f0",
    backgroundColor: "#f8fafc",
    padding: "0 14px",
    cursor: "pointer",
    fontWeight: "600",
    color: "#2563eb",
  },

  registerButton: {
    width: "100%",
    height: "48px",
    border: "none",
    borderRadius: "8px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    fontSize: "16px",
    fontWeight: "600",
    cursor: "pointer",
    marginTop: "5px",
  },

  loginSection: {
    textAlign: "center",
    marginTop: "28px",
  },

  loginText: {
    margin: "0 0 12px",
    color: "#64748b",
    fontSize: "14px",
  },

  loginButton: {
    width: "100%",
    height: "45px",
    border: "1px solid #2563eb",
    borderRadius: "8px",
    backgroundColor: "#ffffff",
    color: "#2563eb",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
  },

  error: {
    padding: "12px",
    marginBottom: "20px",
    borderRadius: "8px",
    backgroundColor: "#fef2f2",
    color: "#b91c1c",
    fontSize: "14px",
    border: "1px solid #fecaca",
  },

  success: {
    padding: "12px",
    marginBottom: "20px",
    borderRadius: "8px",
    backgroundColor: "#f0fdf4",
    color: "#15803d",
    fontSize: "14px",
    border: "1px solid #bbf7d0",
  },
};

export default Register;