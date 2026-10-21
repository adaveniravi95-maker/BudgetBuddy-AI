import React, { useEffect, useState } from "react";
import { api } from "../api";

function Profile() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadProfile();
    }, []);

    async function loadProfile() {
        try {
            setLoading(true);
            setError("");

            const data = await api("/auth/me");
            setUser(data);
        } catch (err) {
            setError(err.message || "Unable to load profile.");
        } finally {
            setLoading(false);
        }
    }

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

                    <button
                        className="profile-retry-btn"
                        onClick={loadProfile}
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="profile-page">

            <section className="profile-hero">
                <div className="profile-hero-content">
                    <div className="profile-eyebrow">
                        👤 BUDDY PROFILE
                    </div>

                    <h1>My Profile</h1>

                    <p>
                        Manage and view your BudgetBuddy account information.
                    </p>
                </div>

                <div className="profile-avatar">
                    {user?.full_name
                        ? user.full_name.charAt(0).toUpperCase()
                        : "U"}
                </div>
            </section>

            <section className="profile-grid">

                <div className="profile-main-card">

                    <div className="profile-card-header">
                        <div>
                            <h2>Personal Information</h2>
                            <p>Your registered BudgetBuddy account details.</p>
                        </div>

                        <span className="profile-status">
                            ● Active Account
                        </span>
                    </div>

                    <div className="profile-info-grid">

                        <div className="profile-info-item">
                            <span className="profile-info-label">
                                Full Name
                            </span>

                            <div className="profile-info-value">
                                <span className="profile-info-icon">
                                    👤
                                </span>

                                <strong>
                                    {user?.full_name || "Not available"}
                                </strong>
                            </div>
                        </div>

                        <div className="profile-info-item">
                            <span className="profile-info-label">
                                Email Address
                            </span>

                            <div className="profile-info-value">
                                <span className="profile-info-icon">
                                    ✉️
                                </span>

                                <strong>
                                    {user?.email || "Not available"}
                                </strong>
                            </div>
                        </div>

                        <div className="profile-info-item">
                            <span className="profile-info-label">
                                Account ID
                            </span>

                            <div className="profile-info-value">
                                <span className="profile-info-icon">
                                    🆔
                                </span>

                                <strong>
                                    #{user?.id ?? "N/A"}
                                </strong>
                            </div>
                        </div>

                        <div className="profile-info-item">
                            <span className="profile-info-label">
                                Account Role
                            </span>

                            <div className="profile-info-value">
                                <span className="profile-info-icon">
                                    🎓
                                </span>

                                <strong>
                                    {user?.role
                                        ? user.role.charAt(0).toUpperCase() +
                                          user.role.slice(1)
                                        : "Student"}
                                </strong>
                            </div>
                        </div>

                    </div>
                </div>

                <div className="profile-side-card">

                    <div className="profile-side-icon">
                        🎓
                    </div>

                    <h2>Student Account</h2>

                    <p>
                        BudgetBuddy is designed to help students manage
                        income, expenses, budgets and savings goals in one
                        place.
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

           

        </div>
    );
}

export default Profile;