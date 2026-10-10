import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notificationsAPI } from '../api/api';
import {
  Wallet,
  LogOut,
  User as UserIcon,
  ShieldCheck,
  UserCheck,
  Bell,
  Check,
  CheckCheck,
  AlertTriangle,
  Sparkles,
  Info,
  Clock,
  Trash2,
  UserPlus,
  BarChart3,
  Coins,
  FileText,
  Sun,
  Moon,
} from 'lucide-react';
import { useTheme } from '../context/useTheme';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const activeSection = location.hash.slice(1) || 'overview';

  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isLoadingNotifs, setIsLoadingNotifs] = useState(false);
  const [notificationPosition, setNotificationPosition] = useState({});

  const dropdownRef = useRef(null);

  const positionNotificationDropdown = useCallback(() => {
    const anchor = dropdownRef.current?.getBoundingClientRect();
    if (!anchor) return;

    const desktop = window.innerWidth >= 768;
    const sidebarWidth = desktop ? 255 : 0;
    const width = desktop
      ? Math.min(390, window.innerWidth - sidebarWidth - 32)
      : Math.min(360, window.innerWidth - 24);
    const height = Math.min(460, window.innerHeight - 24);
    const left = desktop
      ? Math.min(sidebarWidth + 16, window.innerWidth - width - 12)
      : Math.min(Math.max(12, anchor.right - width), window.innerWidth - width - 12);
    let top = anchor.bottom + 12;

    if (top + height > window.innerHeight - 12) {
      top = anchor.top - height - 12;
    }

    top = Math.min(Math.max(12, top), window.innerHeight - height - 12);
    setNotificationPosition({ position: 'fixed', left, top, width, maxHeight: height });
  }, []);

  const fetchUnreadCount = async () => {
    if (!isAuthenticated) return;
    try {
      const res = await notificationsAPI.getUnreadCount();
      setUnreadCount(res.data.unread_count || 0);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  };

  const fetchNotifications = async () => {
    if (!isAuthenticated) return;
    setIsLoadingNotifs(true);
    try {
      const res = await notificationsAPI.getNotifications();
      setNotifications(res.data || []);
      const unread = (res.data || []).filter((n) => !n.is_read).length;
      setUnreadCount(unread);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setIsLoadingNotifs(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchUnreadCount();
      const interval = setInterval(fetchUnreadCount, 30000); // 30s poll
      const handleRefresh = () => {
        fetchUnreadCount();
        if (isNotifOpen) fetchNotifications();
      };
      window.addEventListener('notifications:refresh', handleRefresh);

      return () => {
        clearInterval(interval);
        window.removeEventListener('notifications:refresh', handleRefresh);
      };
    }
  }, [isAuthenticated, isNotifOpen]);

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsNotifOpen(false);
      }
    };
    if (isNotifOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isNotifOpen]);

  useEffect(() => {
    if (!isNotifOpen) return undefined;

    const reposition = () => positionNotificationDropdown();
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    return () => {
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    };
  }, [isNotifOpen, positionNotificationDropdown]);

  const toggleNotifications = () => {
    if (!isNotifOpen) {
      positionNotificationDropdown();
      fetchNotifications();
    }
    setIsNotifOpen(!isNotifOpen);
  };

  const handleMarkAsRead = async (id, e) => {
    e?.stopPropagation();
    try {
      await notificationsAPI.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const handleDeleteNotification = async (id, e) => {
    e?.stopPropagation();
    try {
      await notificationsAPI.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      fetchUnreadCount();
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'budget_alert':
        return <AlertTriangle size={16} className="text-amber-500" />;
      case 'goal_milestone':
        return <Sparkles size={16} className="text-indigo-500" />;
      default:
        return <Info size={16} className="text-blue-500" />;
    }
  };

  const renderThemeSwitch = () => (
    <div className="theme-switch" role="group" aria-label="Color theme">
      <button
        type="button"
        className={`theme-switch-option ${theme === 'light' ? 'active' : ''}`}
        aria-pressed={theme === 'light'}
        onClick={() => setTheme('light')}
      >
        <Sun size={15} />
        <span>Light</span>
      </button>
      <button
        type="button"
        className={`theme-switch-option ${theme === 'dark' ? 'active' : ''}`}
        aria-pressed={theme === 'dark'}
        onClick={() => setTheme('dark')}
      >
        <Moon size={15} />
        <span>Dark</span>
      </button>
    </div>
  );

  return (
    <header className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon-wrapper">
            <Wallet className="brand-icon" size={22} />
          </div>
          <span className="brand-text">
            Budget<span className="brand-highlight">Buddy</span>
          </span>
          {!isAuthenticated && <span className="brand-tagline">Plan &nbsp;•&nbsp; Track &nbsp;•&nbsp; Grow</span>}
        </Link>

        <nav className="navbar-nav">
          {isAuthenticated ? (
            <div className="nav-authenticated">
              <nav className="sidebar-links" aria-label="Main navigation">
                <Link to="/dashboard#overview" className={`sidebar-link ${activeSection === 'overview' ? 'active' : ''}`}>
                  <Wallet size={16} />
                  <span>Dashboard</span>
                </Link>
                <Link to="/dashboard#incomes" className={`sidebar-link ${activeSection === 'incomes' ? 'active' : ''}`}>
                  <UserCheck size={16} />
                  <span>Income</span>
                </Link>
                <Link to="/dashboard#expenses" className={`sidebar-link ${activeSection === 'expenses' ? 'active' : ''}`}>
                  <ShieldCheck size={16} />
                  <span>Expenses</span>
                </Link>
                <Link to="/dashboard#budgets" className={`sidebar-link ${activeSection === 'budgets' ? 'active' : ''}`}>
                  <Clock size={16} />
                  <span>Budget</span>
                </Link>
                <Link to="/dashboard#savings" className={`sidebar-link ${activeSection === 'savings' ? 'active' : ''}`}>
                  <Sparkles size={16} />
                  <span>Savings</span>
                </Link>
                <Link to="/dashboard#reports" className={`sidebar-link ${activeSection === 'reports' ? 'active' : ''}`}>
                  <FileText size={16} />
                  <span>Reports</span>
                </Link>
              </nav>
              {/* Notification Bell Dropdown */}
              <div className="notif-bell-container" ref={dropdownRef}>
                <button
                  onClick={toggleNotifications}
                  className={`btn-notif-bell ${unreadCount > 0 ? 'has-unread' : ''}`}
                  title="Notifications"
                  aria-label="Notifications"
                >
                  <Bell size={18} />
                  {unreadCount > 0 && (
                    <span className="notif-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
                  )}
                </button>

                {isNotifOpen && (
                  <div className="notif-dropdown" style={notificationPosition}>
                    <div className="notif-header">
                      <div className="notif-header-title">
                        <span className="font-semibold">Notifications</span>
                        {unreadCount > 0 && (
                          <span className="notif-pill-count">{unreadCount} new</span>
                        )}
                      </div>
                      {unreadCount > 0 && (
                        <button
                          onClick={handleMarkAllRead}
                          className="btn-notif-mark-all"
                          title="Mark all as read"
                        >
                          <CheckCheck size={14} />
                          <span>Mark all read</span>
                        </button>
                      )}
                    </div>

                    <div className="notif-body">
                      {isLoadingNotifs ? (
                        <div className="notif-loading">
                          <span className="spinner-sm"></span> Loading updates...
                        </div>
                      ) : notifications.length === 0 ? (
                        <div className="notif-empty">
                          <Bell size={28} className="notif-empty-icon" />
                          <p className="notif-empty-title">No notifications yet</p>
                          <p className="notif-empty-subtitle">
                            Budget limits and goal milestones will appear here.
                          </p>
                        </div>
                      ) : (
                        <div className="notif-list">
                          {notifications.map((n) => (
                            <div
                              key={n.id}
                              className={`notif-item ${!n.is_read ? 'notif-unread' : ''}`}
                              onClick={() => !n.is_read && handleMarkAsRead(n.id)}
                            >
                              <div className={`notif-icon-circle type-${n.notification_type}`}>
                                {getNotificationIcon(n.notification_type)}
                              </div>
                              <div className="notif-content">
                                <div className="notif-item-top">
                                  <span className="notif-title">{n.title}</span>
                                  <span className="notif-time">
                                    <Clock size={11} className="inline mr-1" />
                                    {formatTimestamp(n.created_at)}
                                  </span>
                                </div>
                                <p className="notif-message">{n.message}</p>
                                <div className="notif-actions">
                                  {!n.is_read ? (
                                    <button
                                      onClick={(e) => handleMarkAsRead(n.id, e)}
                                      className="btn-notif-action mark-read"
                                      title="Mark as read"
                                    >
                                      <Check size={12} />
                                      <span>Mark read</span>
                                    </button>
                                  ) : (
                                    <span className="notif-read-indicator">Read</span>
                                  )}
                                  <button
                                    onClick={(e) => handleDeleteNotification(n.id, e)}
                                    className="btn-notif-action delete"
                                    title="Delete notification"
                                  >
                                    <Trash2 size={12} />
                                  </button>
                                </div>
                              </div>
                              {!n.is_read && <span className="notif-dot-unread" />}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="user-profile-badge">
                <div className="avatar-circle">
                  <UserIcon size={16} />
                </div>
                <div className="user-info-text">
                  <span className="username">{user?.username}</span>
                  <span className={`role-pill role-${user?.role || 'student'}`}>
                    {user?.role === 'admin' ? (
                      <ShieldCheck size={12} className="inline mr-1" />
                    ) : (
                      <UserCheck size={12} className="inline mr-1" />
                    )}
                    {user?.role || 'Student'}
                  </span>
                </div>
              </div>

              <button onClick={handleLogout} className="btn-logout" title="Log Out">
                <LogOut size={16} />
                <span>Logout</span>
              </button>
              {renderThemeSwitch()}
            </div>
          ) : (
            <div className="nav-guest">
              <Link to="/login" className="guest-nav-item guest-nav-active">
                <UserIcon size={20} />
                <span>Login</span>
              </Link>
              <Link to="/register" className="guest-nav-item">
                <UserPlus size={20} />
                Register
              </Link>
              {renderThemeSwitch()}
              <div className="auth-rail-promo">
                <div className="promo-illustration">
                  <BarChart3 size={56} strokeWidth={1.8} />
                  <Coins size={30} strokeWidth={1.8} />
                </div>
                <strong>Better Money Habits</strong>
                <span>for a Brighter Future</span>
                <i />
              </div>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
