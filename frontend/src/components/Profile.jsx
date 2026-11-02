import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { authAPI } from "../api/api";

function Profile() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [profileError, setProfileError] = useState("");
    const [profileMessage, setProfileMessage] = useState("");
    const [isSavingProfile, setIsSavingProfile] = useState(false);
    const [password, setPassword] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });
    const [passwordError, setPasswordError] = useState("");
    const [passwordMessage, setPasswordMessage] = useState("");
    const [isChangingPassword, setIsChangingPassword] = useState(false);

    useEffect(() => {
        let isMounted = true;

        authAPI.getProfile()
            .then(({ data }) => {
                if (isMounted) setUser(data);
            })
            .catch((err) => {
                if (isMounted) {
                    setError(
                        err.response?.data?.detail
                        || "Unable to load your profile. Please try again."
                    );
                }
            })
            .finally(() => {
                if (isMounted) setLoading(false);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const handleProfileChange = (event) => {
        const { name, value } = event.target;
        setUser((currentUser) => ({ ...currentUser, [name]: value }));
    };

    const handleSaveProfile = async (event) => {
        event.preventDefault();
        setProfileError("");
        setProfileMessage("");
        setIsSavingProfile(true);

        try {
            const { data } = await authAPI.updateProfile({
                first_name: user.first_name,
                last_name: user.last_name,
                email: user.email,
                phone: user.phone,
                college: user.college,
            });
            setUser(data);
            setProfileMessage("Profile updated successfully.");
        } catch (err) {
            const responseData = err.response?.data;
            const detail = responseData?.detail
                || Object.entries(responseData || {})
                    .map(([field, messages]) => `${field}: ${[].concat(messages).join(" ")}`)
                    .join(" ");
            setProfileError(detail || "Unable to save your profile. Please try again.");
        } finally {
            setIsSavingProfile(false);
        }
    };

    const handlePasswordChange = (event) => {
        const { name, value } = event.target;
        setPassword((currentPassword) => ({ ...currentPassword, [name]: value }));
    };

    const handleChangePassword = async (event) => {
        event.preventDefault();
        setPasswordError("");
        setPasswordMessage("");

        if (password.new_password !== password.confirm_password) {
            setPasswordError("New passwords do not match.");
            return;
        }

        setIsChangingPassword(true);
        try {
            await authAPI.changePassword({
                current_password: password.current_password,
                new_password: password.new_password,
            });
            setPassword({ current_password: "", new_password: "", confirm_password: "" });
            setPasswordMessage("Password updated successfully.");
        } catch (err) {
            const responseData = err.response?.data;
            const detail = responseData?.detail
                || Object.entries(responseData || {})
                    .map(([field, messages]) => `${field}: ${[].concat(messages).join(" ")}`)
                    .join(" ");
            setPasswordError(detail || "Unable to change your password. Please try again.");
        } finally {
            setIsChangingPassword(false);
        }
    };

    if (loading) {
        return (
            <div className="profile-page">
                <div className="profile-loading">
                    <div className="profile-loading-icon">👤</div>
                    <h2>Loading your profile...</h2>
                    <p>Please wait while we fetch your account information.</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="profile-page">
                <div className="profile-error">
                    <div className="profile-error-icon">⚠️</div>
                    <h2>Unable to load profile</h2>
                    <p>{error}</p>
                    <Link to="/dashboard" className="btn-primary">Back to dashboard</Link>
                </div>
            </div>
        );
    }

    const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ");

    return (
        <div className="profile-page profile-settings-page">

            <section className="profile-hero">
                <div className="profile-hero-content">
                    <div className="profile-eyebrow">
                        👤 BUDDY PROFILE
                    </div>

                    <h1>My Profile</h1>

                    <p>
                        Manage your personal information and account security.
                    </p>
                    <Link to="/dashboard" className="profile-back-link">Back to dashboard</Link>
                </div>

                <div className="profile-avatar">
                    {fullName
                        ? fullName.charAt(0).toUpperCase()
                        : "U"}
                </div>
            </section>

            <section className="profile-grid">

                <div className="profile-main-card">

                    <div className="profile-card-header">
                        <div>
                            <h2>Personal Information</h2>
                            <p>Update your contact details and student information.</p>
                        </div>

                        <span className="profile-status">
                            ● Active Account
                        </span>
                    </div>

                    {profileError && <p className="profile-feedback profile-feedback-error" role="alert">{profileError}</p>}
                    {profileMessage && <p className="profile-feedback profile-feedback-success" role="status">{profileMessage}</p>}

                    <form className="profile-settings-form" onSubmit={handleSaveProfile}>
                        <div className="form-group">
                            <label htmlFor="profile-username">Username</label>
                            <input id="profile-username" value={user?.username || ""} readOnly />
                        </div>
                        <div className="form-group">
                            <label htmlFor="profile-email">Email address</label>
                            <input id="profile-email" name="email" type="email" value={user?.email || ""} onChange={handleProfileChange} required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="profile-first-name">First name</label>
                            <input id="profile-first-name" name="first_name" value={user?.first_name || ""} onChange={handleProfileChange} maxLength={150} />
                        </div>
                        <div className="form-group">
                            <label htmlFor="profile-last-name">Last name</label>
                            <input id="profile-last-name" name="last_name" value={user?.last_name || ""} onChange={handleProfileChange} maxLength={150} />
                        </div>
                        <div className="form-group">
                            <label htmlFor="profile-phone">Phone</label>
                            <input id="profile-phone" name="phone" type="tel" value={user?.phone || ""} onChange={handleProfileChange} maxLength={15} />
                        </div>
                        <div className="form-group">
                            <label htmlFor="profile-college">College</label>
                            <input id="profile-college" name="college" value={user?.college || ""} onChange={handleProfileChange} maxLength={150} />
                        </div>
                        <div className="profile-settings-actions">
                            <span className="profile-role-label">
                                Account role: <strong>{user?.role || "student"}</strong>
                            </span>
                            <button className="btn-primary" type="submit" disabled={isSavingProfile}>
                                {isSavingProfile ? "Saving..." : "Save profile"}
                            </button>
                        </div>
                    </form>
                </div>

                <div className="profile-side-card">

                    <div className="profile-side-icon">
                        🎓
                    </div>

                    <h2>{user?.role === "admin" ? "Administrator Account" : "Student Account"}</h2>

                    <p>
                        {user?.role === "admin"
                            ? "This account has the administrator role configured for BudgetBuddy."
                            : "BudgetBuddy helps students manage income, expenses, budgets and savings goals in one place."}
                    </p>

                    <div className="profile-role-box">
                        <span>Current Role</span>

                        <strong>
                            {user?.role
                                ? user.role.charAt(0).toUpperCase() +
                                  user.role.slice(1)
                                : "Student"}
                        </strong>
                    </div>

                </div>

            </section>

            <section className="profile-security-card">

                <div className="profile-security-icon">
                    🔐
                </div>

                <div className="profile-security-content">
                    <h2>Account & Security</h2>

                    <p>
                        Your account is protected using authenticated
                        BudgetBuddy access. Only your own financial data is
                        available through your account.
                    </p>

                    <div className="security-items">

                        <div className="security-item">
                            <span>🔑</span>
                            <div>
                                <strong>Authenticated Access</strong>
                                <small>
                                    Your account requires secure login.
                                </small>
                            </div>
                        </div>

                        <div className="security-item">
                            <span>🛡️</span>
                            <div>
                                <strong>Private Financial Data</strong>
                                <small>
                                    Your transactions and financial records
                                    are user-specific.
                                </small>
                            </div>
                        </div>

                        <div className="security-item">
                            <span>✅</span>
                            <div>
                                <strong>Account Status</strong>
                                <small>
                                    Your BudgetBuddy account is active.
                                </small>
                            </div>
                        </div>

                    </div>
                </div>

            </section>

            <section className="profile-password-card">
                <div>
                    <h2>Change password</h2>
                    <p>Enter your current password to set a new one.</p>
                </div>
                {passwordError && <p className="profile-feedback profile-feedback-error" role="alert">{passwordError}</p>}
                {passwordMessage && <p className="profile-feedback profile-feedback-success" role="status">{passwordMessage}</p>}
                <form className="profile-settings-form" onSubmit={handleChangePassword}>
                    <div className="form-group">
                        <label htmlFor="current-password">Current password</label>
                        <input id="current-password" name="current_password" type="password" autoComplete="current-password" value={password.current_password} onChange={handlePasswordChange} required />
                    </div>
                    <div className="form-group">
                        <label htmlFor="new-password">New password</label>
                        <input id="new-password" name="new_password" type="password" autoComplete="new-password" value={password.new_password} onChange={handlePasswordChange} required />
                    </div>
                    <div className="form-group">
                        <label htmlFor="confirm-password">Confirm new password</label>
                        <input id="confirm-password" name="confirm_password" type="password" autoComplete="new-password" value={password.confirm_password} onChange={handlePasswordChange} required />
                    </div>
                    <div className="profile-settings-actions">
                        <button className="btn-primary" type="submit" disabled={isChangingPassword}>
                            {isChangingPassword ? "Updating..." : "Update password"}
                        </button>
                    </div>
                </form>
            </section>

        </div>
    );
}

export default Profile;