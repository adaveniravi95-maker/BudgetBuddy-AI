import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL;

function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();

    setMessage("");
    setError("");
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
        setError(
          data.username?.[0] ||
          data.email?.[0] ||
          data.password?.[0] ||
          data.detail ||
          "Registration failed."
        );
        return;
      }

      setMessage("Registration successful! Please login.");

      setUsername("");
      setEmail("");
      setPassword("");

      setTimeout(() => {
        navigate("/login");
      }, 1500);

    } catch (error) {
      console.error("Registration error:", error);
      setError("Unable to connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#f5f5f5",
        padding: "20px",
      }}
    >
      <div
        style={{
          width: "400px",
          maxWidth: "100%",
          padding: "30px",
          backgroundColor: "white",
          borderRadius: "12px",
          boxShadow: "0 4px 15px rgba(0, 0, 0, 0.1)",
        }}
      >
        <h1 style={{ textAlign: "center" }}>
          📝 Register
        </h1>

        <p style={{ textAlign: "center" }}>
          Create your BudgetBuddy account
        </p>

        {error && (
          <div
            style={{
              padding: "12px",
              marginBottom: "15px",
              borderRadius: "6px",
              backgroundColor: "#fee2e2",
              color: "#b91c1c",
            }}
          >
            {error}
          </div>
        )}

        {message && (
          <div
            style={{
              padding: "12px",
              marginBottom: "15px",
              borderRadius: "6px",
              backgroundColor: "#dcfce7",
              color: "#166534",
            }}
          >
            {message}
          </div>
        )}

        <form onSubmit={handleRegister}>

          {/* USERNAME */}

          <label>
            <strong>Username</strong>
          </label>

          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            required
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "6px",
              marginBottom: "15px",
              boxSizing: "border-box",
            }}
          />

          {/* EMAIL */}

          <label>
            <strong>Email</strong>
          </label>

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter email"
            required
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "6px",
              marginBottom: "15px",
              boxSizing: "border-box",
            }}
          />

          {/* PASSWORD */}

          <label>
            <strong>Password</strong>
          </label>

          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            required
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "6px",
              marginBottom: "20px",
              boxSizing: "border-box",
            }}
          />

          {/* REGISTER BUTTON */}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Registering..." : "Register"}
          </button>

        </form>

        <p
          style={{
            textAlign: "center",
            marginTop: "20px",
          }}
        >
          Already have an account?
        </p>

        <button
          type="button"
          onClick={() => navigate("/login")}
          style={{
            width: "100%",
            padding: "10px",
            cursor: "pointer",
          }}
        >
          Go to Login
        </button>

      </div>
    </div>
  );
}

export default Register;
