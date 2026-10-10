import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Wallet, Lock, User, AlertCircle, CheckCircle2, ArrowRight, Eye, EyeOff } from 'lucide-react';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const { login, isAuthenticated, authError, setAuthError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If redirected after registration, show success message
  useEffect(() => {
    if (location.state?.registeredMessage) {
      setSuccessMessage(location.state.registeredMessage);
      if (location.state?.registeredUsername) {
        setUsername(location.state.registeredUsername);
      }
    }
    setAuthError(null);
  }, [location.state, setAuthError]);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const validate = () => {
    const errors = {};
    if (!username.trim()) {
      errors.username = 'Username or email is required';
    }
    if (!password) {
      errors.password = 'Password is required';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setSuccessMessage('');
    const result = await login(username.trim(), password);
    setIsSubmitting(false);

    if (result.success) {
      navigate('/dashboard', { replace: true });
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card auth-login-card">
        <div className="auth-header">
          <div className="auth-brand-mark">
            <Wallet size={25} />
          </div>
          <h2>Welcome to BudgetBuddy</h2>
          <p className="auth-subtitle">Sign in to access your financial dashboard</p>
        </div>

        {successMessage && (
          <div className="alert alert-success">
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
          </div>
        )}

        {authError && (
          <div className="alert alert-error">
            <AlertCircle size={18} />
            <span>{authError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username or Email</label>
            <div className="input-wrapper">
              <User size={18} className="input-icon" />
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (fieldErrors.username) setFieldErrors({ ...fieldErrors, username: null });
                }}
                placeholder="Enter username or email"
                className={fieldErrors.username ? 'input-error' : ''}
                autoComplete="username"
              />
            </div>
            {fieldErrors.username && <span className="field-error">{fieldErrors.username}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper" style={{ position: 'relative' }}>
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: null });
                }}
                placeholder="Enter your password"
                className={fieldErrors.password ? 'input-error' : ''}
                autoComplete="current-password"
                style={{ paddingRight: '2.5rem' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#64748b',
                  display: 'flex',
                  alignItems: 'center',
                  padding: 0,
                }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
          </div>

          <button type="submit" className="btn-primary btn-block" disabled={isSubmitting}>
            {isSubmitting ? (
              <span className="btn-spinner-text">
                <span className="spinner-sm"></span> Signing In...
              </span>
            ) : (
              <span className="btn-text-icon">
                Sign In <ArrowRight size={16} />
              </span>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
