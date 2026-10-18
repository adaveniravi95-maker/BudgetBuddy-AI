import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    const cleanUsername = username.trim();

    try {
      const res = await api.post('token/', {
        username: cleanUsername,
        password: password
      });

      // Save token in both keys to prevent 401 on GET requests
      localStorage.setItem('access_token', res.data.access);
      localStorage.setItem('token', res.data.access);
      localStorage.setItem('refresh_token', res.data.refresh);
      localStorage.setItem('username', cleanUsername);

      navigate('/');
    } catch (err) {
      console.error('Login error details:', err.response?.data);
      if (err.response?.status === 401) {
        setErrorMsg('Invalid Credentials: Enter your USERNAME (not email).');
      } else if (!err.response) {
        setErrorMsg('Cannot connect to backend server. Is Django running?');
      } else {
        setErrorMsg(`Login Failed: ${JSON.stringify(err.response.data)}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ backgroundColor: '#090d16', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'system-ui, sans-serif', padding: '20px' }}>
      <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', padding: '32px', borderRadius: '12px', width: '100%', maxWidth: '380px', boxShadow: '0 8px 24px rgba(0,0,0,0.5)' }}>
        <h2 style={{ margin: '0 0 8px', color: '#f8fafc', fontSize: '24px', fontWeight: 'bold' }}>BudgetBuddy Sign In</h2>
        <p style={{ margin: '0 0 20px', color: '#94a3b8', fontSize: '14px' }}>Enter your credentials to continue</p>

        {errorMsg && (
          <div style={{ backgroundColor: '#7f1d1d33', border: '1px solid #ef4444', color: '#fca5a5', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px', lineHeight: '1.4' }}>
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', color: '#cbd5e1', marginBottom: '6px', fontWeight: '600' }}>Username</label>
            <input
              type="text"
              required
              placeholder="e.g. admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#f8fafc', fontSize: '14px', boxSizing: 'border-box', outline: 'none' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', color: '#cbd5e1', marginBottom: '6px', fontWeight: '600' }}>Password</label>
            <input
              type="password"
              required
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#f8fafc', fontSize: '14px', boxSizing: 'border-box', outline: 'none' }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{ backgroundColor: '#2563eb', color: '#fff', padding: '12px', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer', marginTop: '4px', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Verifying...' : 'Sign In'}
          </button>
        </form>

        <p style={{ margin: '20px 0 0', textAlign: 'center', fontSize: '13px', color: '#94a3b8' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: '#38bdf8', textDecoration: 'none', fontWeight: '600' }}>Register here</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;