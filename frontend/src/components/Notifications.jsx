import React, { useEffect, useState } from "react";
import { api } from "../api";

function Notifications() {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [markingRead, setMarkingRead] = useState(null);
    const [deleting, setDeleting] = useState(null);

    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    const loadNotifications = async (showRefresh = false) => {
        try {
            if (showRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }

            setError("");

            const [notificationData, countData] = await Promise.all([
                api("/notifications"),
                api("/notifications/unread-count"),
            ]);

            setNotifications(
                Array.isArray(notificationData)
                    ? notificationData
                    : []
            );

            let count = 0;

            if (typeof countData === "number") {
                count = countData;
            } else if (
                typeof countData?.unread_count === "number"
            ) {
                count = countData.unread_count;
            } else if (
                typeof countData?.count === "number"
            ) {
                count = countData.count;
            }

            setUnreadCount(count);
        } catch (err) {
            setError(
                err.message ||
                "Unable to load notifications."
            );
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadNotifications();
    }, []);

    useEffect(() => {
        if (!message && !error) {
            return;
        }

        const timer = setTimeout(() => {
            setMessage("");
            setError("");
        }, 3000);

        return () => clearTimeout(timer);
    }, [message, error]);

    const markAsRead = async (notificationId) => {
        try {
            setMarkingRead(notificationId);
            setError("");
            setMessage("");

            await api(
                `/notifications/${notificationId}/read`,
                {
                    method: "PUT",
                }
            );

            await loadNotifications();

            setMessage(
                "Notification marked as read."
            );
        } catch (err) {
            setError(
                err.message ||
                "Unable to mark notification as read."
            );
        } finally {
            setMarkingRead(null);
        }
    };

    const deleteNotification = async (notificationId) => {
        try {
            setDeleting(notificationId);
            setError("");
            setMessage("");

            await api(
                `/notifications/${notificationId}`,
                {
                    method: "DELETE",
                }
            );

            await loadNotifications();

            setMessage(
                "Notification deleted."
            );
        } catch (err) {
            setError(
                err.message ||
                "Unable to delete notification."
            );
        } finally {
            setDeleting(null);
        }
    };

    const isRead = (notification) => {
        return (
            notification.is_read === true ||
            notification.read === true
        );
    };

    const getNotificationTitle = (notification) => {
        return (
            notification.title ||
            notification.notification_type ||
            "BudgetBuddy Notification"
        );
    };

    const getNotificationMessage = (notification) => {
        return (
            notification.message ||
            notification.content ||
            notification.description ||
            "You have a new notification."
        );
    };

    const formatDateTime = (value) => {
        if (!value) {
            return "Recently";
        }

        const parsedDate = new Date(value);

        if (Number.isNaN(parsedDate.getTime())) {
            return value;
        }

        return parsedDate.toLocaleString(
            "en-IN",
            {
                dateStyle: "medium",
                timeStyle: "short",
            }
        );
    };

    const getNotificationType = (notification) => {
        const title = getNotificationTitle(
            notification
        ).toLowerCase();

        if (title.includes("exceeded")) {
            return "danger";
        }

        if (
            title.includes("almost") ||
            title.includes("warning")
        ) {
            return "warning";
        }

        return "info";
    };

    return (
        <div className="notifications-page">

            {/* ==================================================
                HERO
            ================================================== */}

            <section className="notifications-hero">

                <div className="notifications-hero-content">

                    <div className="notifications-eyebrow">
                        <span className="notifications-eyebrow-icon">
                            🔔
                        </span>

                        BUDGETBUDDY ALERTS
                    </div>

                    <h1>Notifications</h1>

                    <p>
                        Stay updated with important reminders,
                        budget alerts and financial activity.
                    </p>

                </div>

                <button
                    className="notifications-refresh-btn"
                    onClick={() =>
                        loadNotifications(true)
                    }
                    disabled={refreshing}
                >
                    <span className="refresh-icon">
                        ↻
                    </span>

                    {refreshing
                        ? "Refreshing..."
                        : "Refresh"}
                </button>

            </section>


            {/* ==================================================
                TOAST MESSAGES
            ================================================== */}

            {message && (
                <div className="notification-toast success">
                    <span>✓</span>
                    {message}
                </div>
            )}

            {error && (
                <div className="notification-toast error">
                    <span>⚠</span>
                    {error}
                </div>
            )}


            {/* ==================================================
                SUMMARY CARDS
            ================================================== */}

            <section className="notification-summary-grid">

                <div className="notification-summary-card total-card">

                    <div className="notification-summary-icon">
                        🔔
                    </div>

                    <div className="notification-summary-content">

                        <span className="notification-summary-label">
                            Total Notifications
                        </span>

                        <strong>
                            {notifications.length}
                        </strong>

                        <small>
                            All your alerts
                        </small>

                    </div>

                </div>


                <div className="notification-summary-card unread-card">

                    <div className="notification-summary-icon">
                        🔵
                    </div>

                    <div className="notification-summary-content">

                        <span className="notification-summary-label">
                            Unread
                        </span>

                        <strong>
                            {unreadCount}
                        </strong>

                        <small>
                            Need your attention
                        </small>

                    </div>

                </div>


                <div className="notification-summary-card read-card">

                    <div className="notification-summary-icon">
                        ✓
                    </div>

                    <div className="notification-summary-content">

                        <span className="notification-summary-label">
                            Read
                        </span>

                        <strong>
                            {Math.max(
                                notifications.length -
                                unreadCount,
                                0
                            )}
                        </strong>

                        <small>
                            Already reviewed
                        </small>

                    </div>

                </div>

            </section>


            {/* ==================================================
                NOTIFICATIONS SECTION
            ================================================== */}

            <section className="notifications-section">

                <div className="notifications-section-header">

                    <div>
                        <div className="section-mini-label">
                            YOUR ALERT CENTER
                        </div>

                        <h2>
                            Your Notifications
                        </h2>

                        <p>
                            Review your latest BudgetBuddy
                            alerts and reminders.
                        </p>
                    </div>

                    {unreadCount > 0 && (
                        <div className="unread-badge">
                            <span className="unread-dot"></span>
                            {unreadCount} unread
                        </div>
                    )}

                </div>


                {/* ==================================================
                    LOADING
                ================================================== */}

                {loading ? (

                    <div className="notifications-empty-state">

                        <div className="notification-state-icon loading-state">
                            ⏳
                        </div>

                        <h3>
                            Loading notifications...
                        </h3>

                        <p>
                            Please wait while we fetch
                            your latest alerts.
                        </p>

                    </div>

                ) : notifications.length === 0 ? (

                    /* ==================================================
                       EMPTY
                    ================================================== */

                    <div className="notifications-empty-state">

                        <div className="notification-state-icon empty-state">
                            🔕
                        </div>

                        <h3>
                            You're all caught up
                        </h3>

                        <p>
                            There are no notifications
                            waiting for you right now.
                        </p>

                        <span className="empty-state-hint">
                            New budget alerts will appear
                            here automatically when needed.
                        </span>

                    </div>

                ) : (

                    /* ==================================================
                       NOTIFICATION LIST
                    ================================================== */

                    <div className="notification-list">

                        {notifications.map(
                            (notification) => {

                                const read =
                                    isRead(notification);

                                const type =
                                    getNotificationType(
                                        notification
                                    );

                                return (
                                    <article
                                        key={
                                            notification.id
                                        }
                                        className={`
                                            notification-card
                                            ${read
                                                ? "read"
                                                : "unread"
                                            }
                                            notification-${type}
                                        `}
                                    >

                                        {/* LEFT ICON */}

                                        <div className="notification-icon-column">

                                            <div className="notification-card-icon">
                                                {read
                                                    ? "✓"
                                                    : type ===
                                                      "danger"
                                                    ? "!"
                                                    : "🔔"}
                                            </div>

                                            {!read && (
                                                <span className="notification-connection-line"></span>
                                            )}

                                        </div>


                                        {/* MAIN CONTENT */}

                                        <div className="notification-card-content">

                                            <div className="notification-card-top">

                                                <div className="notification-heading">

                                                    <div className="notification-title-row">

                                                        <h3>
                                                            {getNotificationTitle(
                                                                notification
                                                            )}
                                                        </h3>

                                                        {!read && (
                                                            <span className="new-badge">
                                                                NEW
                                                            </span>
                                                        )}

                                                        {read && (
                                                            <span className="read-badge">
                                                                READ
                                                            </span>
                                                        )}

                                                    </div>

                                                    <p>
                                                        {getNotificationMessage(
                                                            notification
                                                        )}
                                                    </p>

                                                </div>

                                            </div>


                                            {/* BOTTOM ROW */}

                                            <div className="notification-card-bottom">

                                                <div className="notification-date">
                                                    <span>
                                                        🕐
                                                    </span>

                                                    {formatDateTime(
                                                        notification.created_at
                                                    )}
                                                </div>


                                                <div className="notification-actions">

                                                    {!read && (
                                                        <button
                                                            className="notification-action-btn read-btn"
                                                            onClick={() =>
                                                                markAsRead(
                                                                    notification.id
                                                                )
                                                            }
                                                            disabled={
                                                                markingRead ===
                                                                notification.id
                                                            }
                                                        >
                                                            {markingRead ===
                                                            notification.id
                                                                ? "Marking..."
                                                                : "✓ Mark as Read"}
                                                        </button>
                                                    )}

                                                    {read && (
                                                        <span className="read-status">
                                                            ✓ Read
                                                        </span>
                                                    )}

                                                    <button
                                                        className="notification-action-btn delete-btn"
                                                        onClick={() =>
                                                            deleteNotification(
                                                                notification.id
                                                            )
                                                        }
                                                        disabled={
                                                            deleting ===
                                                            notification.id
                                                        }
                                                    >
                                                        {deleting ===
                                                        notification.id
                                                            ? "Deleting..."
                                                            : "🗑 Delete"}
                                                    </button>

                                                </div>

                                            </div>

                                        </div>

                                    </article>
                                );
                            }
                        )}

                    </div>
                )}

            </section>

        </div>
    );
}

export default Notifications;