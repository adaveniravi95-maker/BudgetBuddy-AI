import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL;

function Profile() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [newEmail, setNewEmail] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const [emailMessage, setEmailMessage] = useState("");
  const [emailError, setEmailError] = useState("");

  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  // =====================================================
  // LOAD PROFILE
  // =====================================================

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const response = await fetch(
        `${API}/profile/`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        navigate("/login");
        return;
      }

      const data = await response.json();

      setUsername(data.username || "");
      setEmail(data.email || "");
      setNewEmail(data.email || "");
    } catch (error) {
      console.error("Profile error:", error);
      setMessage("Unable to load profile.");
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // UPDATE EMAIL
  // =====================================================

  const handleUpdateEmail = async (e) => {
    e.preventDefault();

    setEmailMessage("");
    setEmailError("");

    if (!newEmail.trim()) {
      setEmailError("Email is required.");
      return;
    }

    if (!newEmail.includes("@")) {
      setEmailError("Please enter a valid email address.");
      return;
    }

    const token = localStorage.getItem("access_token");

    try {
      const response = await fetch(
        `${API}/profile/`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            email: newEmail.trim(),
          }),
        }
      );

      const data = await response.json();

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        navigate("/login");
        return;
      }

      if (!response.ok) {
        setEmailError(
          data.error || "Unable to update email."
        );
        return;
      }

      setEmail(data.email || newEmail.trim());
      setNewEmail(data.email || newEmail.trim());

      setEmailMessage(
        "Email updated successfully!"
      );
    } catch (error) {
      console.error("Email update error:", error);

      setEmailError(
        "Unable to connect to the server."
      );
    }
  };

  // =====================================================
  // CHANGE PASSWORD
  // =====================================================

 const handleChangePassword = async (e) => {
  e.preventDefault();

  setPasswordMessage("");
  setPasswordError("");

  if (!currentPassword || !newPassword || !confirmPassword) {
    setPasswordError("Please fill all password fields.");
    return;
  }

  if (newPassword !== confirmPassword) {
    setPasswordError("New passwords do not match.");
    return;
  }

  if (newPassword.length < 8) {
    setPasswordError(
      "New password must be at least 8 characters."
    );
    return;
  }

  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch(
      `${API}/change-password/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          old_password: currentPassword,
          new_password: newPassword,
        }),
      }
    );

    const data = await response.json();

    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      navigate("/login");
      return;
    }

    if (!response.ok) {
      setPasswordError(
        data.message || "Unable to change password."
      );
      return;
    }

    setPasswordMessage(
      "Password changed successfully!"
    );

    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  } catch (error) {
    console.error("Password error:", error);

    setPasswordError(
      "Unable to connect to the server."
    );
  }
};

  // =====================================================
  // LOGOUT
  // =====================================================

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    navigate("/login");
  };

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <h2>Loading Profile...</h2>
        </div>
      </div>
    );
  }

  // =====================================================
  // UI
  // =====================================================

  return (
    <div style={styles.page}>
      <div style={styles.card}>

        {/* HEADER */}

        <div style={styles.header}>
          <div>
            <h1>My Profile</h1>

            <p>
              View and manage your BudgetBuddy account.
            </p>
          </div>

          <button
            style={styles.backButton}
            onClick={() => navigate("/dashboard")}
          >
            Back to Dashboard
          </button>
        </div>

        {/* MESSAGE */}

        {message && (
          <div style={styles.message}>
            {message}
          </div>
        )}

        {/* AVATAR */}

        <div style={styles.avatar}>
          👤
        </div>

        {/* ACCOUNT INFORMATION */}

        <h2>Account Information</h2>

        <div style={styles.profileInfo}>

          <div style={styles.infoBox}>
            <h3>Username</h3>

            <p>
              {username || "Not available"}
            </p>
          </div>

          <div style={styles.infoBox}>
            <h3>Email</h3>

            <p>
              {email || "Not available"}
            </p>
          </div>

        </div>

        {/* UPDATE EMAIL */}

        <div style={styles.emailSection}>

          <h2>Update Email</h2>

          <p>
            Update the email address associated
            with your BudgetBuddy account.
          </p>

          {emailMessage && (
            <div style={styles.success}>
              {emailMessage}
            </div>
          )}

          {emailError && (
            <div style={styles.error}>
              {emailError}
            </div>
          )}

          <form onSubmit={handleUpdateEmail}>

            <div style={styles.formGroup}>

              <label>
                New Email
              </label>

              <input
                type="email"
                value={newEmail}
                onChange={(e) =>
                  setNewEmail(e.target.value)
                }
                placeholder="Enter new email"
                style={styles.input}
                required
              />

            </div>

            <button
              type="submit"
              style={styles.emailButton}
            >
              Update Email
            </button>

          </form>

        </div>

        {/* CHANGE PASSWORD */}

        <div style={styles.passwordSection}>

          <h2>Change Password</h2>

          <p>
            Update your password to keep your
            account secure.
          </p>

          {passwordMessage && (
            <div style={styles.success}>
              {passwordMessage}
            </div>
          )}

          {passwordError && (
            <div style={styles.error}>
              {passwordError}
            </div>
          )}

          <form onSubmit={handleChangePassword}>

            {/* CURRENT PASSWORD */}

            <div style={styles.formGroup}>

              <label>
                Current Password
              </label>

              <input
                type="password"
                value={currentPassword}
                onChange={(e) =>
                  setCurrentPassword(e.target.value)
                }
                placeholder="Enter current password"
                style={styles.input}
                required
              />

            </div>

            {/* NEW PASSWORD */}

            <div style={styles.formGroup}>

              <label>
                New Password
              </label>

              <input
                type="password"
                value={newPassword}
                onChange={(e) =>
                  setNewPassword(e.target.value)
                }
                placeholder="Enter new password"
                style={styles.input}
                required
              />

            </div>

            {/* CONFIRM PASSWORD */}

            <div style={styles.formGroup}>

              <label>
                Confirm New Password
              </label>

              <input
                type="password"
                value={confirmPassword}
                onChange={(e) =>
                  setConfirmPassword(e.target.value)
                }
                placeholder="Confirm new password"
                style={styles.input}
                required
              />

            </div>

            <button
              type="submit"
              style={styles.passwordButton}
            >
              Change Password
            </button>

          </form>

        </div>

        {/* ACTION BUTTONS */}

        <div style={styles.actions}>

          <button
            style={styles.dashboardButton}
            onClick={() => navigate("/dashboard")}
          >
            Go to Dashboard
          </button>

          <button
            style={styles.logoutButton}
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </div>
    </div>
  );
}

// =====================================================
// STYLES
// =====================================================

const styles = {
  page: {
    minHeight: "100vh",
    background:
      "linear-gradient(135deg, #eff6ff, #f5f3ff)",
    padding: "40px 20px",
    boxSizing: "border-box",
  },

  card: {
    maxWidth: "850px",
    margin: "0 auto",
    background: "#ffffff",
    padding: "35px",
    borderRadius: "20px",
    boxShadow:
      "0 10px 30px rgba(0, 0, 0, 0.10)",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    marginBottom: "30px",
  },

  backButton: {
    padding: "10px 18px",
    border: "none",
    borderRadius: "10px",
    background: "#2563eb",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  },

  message: {
    background: "#fef3c7",
    color: "#92400e",
    padding: "12px",
    borderRadius: "10px",
    marginBottom: "20px",
  },

  avatar: {
    width: "110px",
    height: "110px",
    borderRadius: "50%",
    background: "#dbeafe",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "50px",
    margin: "0 auto 30px",
  },

  profileInfo: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "20px",
    marginTop: "20px",
  },

  infoBox: {
    padding: "22px",
    borderRadius: "15px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
  },

  emailSection: {
    marginTop: "35px",
    padding: "25px",
    borderRadius: "15px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
  },

  passwordSection: {
    marginTop: "35px",
    padding: "25px",
    borderRadius: "15px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
  },

  formGroup: {
    marginBottom: "18px",
  },

  input: {
    width: "100%",
    padding: "12px",
    marginTop: "7px",
    borderRadius: "8px",
    border: "1px solid #cbd5e1",
    boxSizing: "border-box",
    fontSize: "15px",
  },

  emailButton: {
    padding: "12px 20px",
    border: "none",
    borderRadius: "10px",
    background: "#2563eb",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  },

  passwordButton: {
    padding: "12px 20px",
    border: "none",
    borderRadius: "10px",
    background: "#7c3aed",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  },

  success: {
    background: "#dcfce7",
    color: "#166534",
    padding: "12px",
    borderRadius: "10px",
    marginBottom: "20px",
  },

  error: {
    background: "#fee2e2",
    color: "#b91c1c",
    padding: "12px",
    borderRadius: "10px",
    marginBottom: "20px",
  },

  actions: {
    display: "flex",
    gap: "15px",
    marginTop: "30px",
    flexWrap: "wrap",
  },

  dashboardButton: {
    padding: "12px 20px",
    border: "none",
    borderRadius: "10px",
    background: "#22c55e",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  },

  logoutButton: {
    padding: "12px 20px",
    border: "none",
    borderRadius: "10px",
    background: "#ef4444",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  },
};

export default Profile;