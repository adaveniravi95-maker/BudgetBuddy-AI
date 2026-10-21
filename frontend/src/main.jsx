import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import './styles.css';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';

const API =
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV
        ? "http://127.0.0.1:8000/api"
        : "https://budgetbuddy-student-finance-platform.onrender.com/api");

function api(path, options = {}) {
    const token = localStorage.getItem('token');
    const isForm = options.body instanceof URLSearchParams;

    return fetch(API + path, {
        ...options,
        headers: {
            ...(isForm ? {} : { 'Content-Type': 'application/json' }),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(options.headers || {})
        }
    }).then(async r => {
        const d = await r.json().catch(() => null);

        if (!r.ok) {
            let message = 'Request failed';

            if (Array.isArray(d?.detail)) {
                message = d.detail
                    .map(error => error.msg || 'Invalid input')
                    .join(', ');
            } else if (typeof d?.detail === 'string') {
                message = d.detail;
            } else if (typeof d?.message === 'string') {
                message = d.message;
            }

            throw new Error(message);
        }

        return d;
    });
}

function App() {
    const nav = useNavigate();

    const [login, setLogin] = useState(true);
    const [showPassword, setShowPassword] = useState(false);

    const [form, setForm] = useState({
        email: '',
        password: '',
        full_name: ''
    });

    const [msg, setMsg] = useState('');
    const [user, setUser] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');

        if (token) {
            api('/auth/me')
                .then(setUser)
                .catch(() => {
                    localStorage.removeItem('token');
                });
        }
    }, []);

    async function auth(e) {
        e.preventDefault();
        setMsg('');

        try {
            if (login) {
                const body = new URLSearchParams();
                body.append('username', form.email);
                body.append('password', form.password);

                const d = await api('/auth/login', {
                    method: 'POST',
                    body
                });

                localStorage.setItem('token', d.access_token);

                const loggedInUser = await api('/auth/me');

                setUser(loggedInUser);
                nav('/');
            } else {
                await api('/auth/register', {
                    method: 'POST',
                    body: JSON.stringify(form)
                });

                setMsg('Registration successful. Please login.');
                setLogin(true);
            }
        } catch (e) {
            setMsg(e.message);
        }
    }

    function logout() {
        localStorage.removeItem('token');
        setUser(null);
        setMsg('');
    }

    if (!user) {
        return (
            <main className="bb-auth-page">
                <section className="bb-auth-left">
                    <div className="bb-brand">
                        <div className="bb-logo">✦</div>
                        <div>
                            <h2>Budget<span>Buddy</span></h2>
                            <small>Smart Money. Brighter Future.</small>
                        </div>
                    </div>

                    <div className="bb-hero-content">
                        <span className="bb-eyebrow">
                            YOUR MONEY. YOUR FUTURE.
                        </span>

                        <h1>
                            Your Financial Goals,
                            <span> Our Priority.</span>
                        </h1>

                        <p>
                            Track your spending, save for your dreams,
                            and build a better tomorrow — one step at a time.
                        </p>

                        <div className="bb-features">
                            <div>
                                <span>◔</span>
                                <strong>Track</strong>
                                <small>Expenses</small>
                            </div>
                            <div>
                                <span>♧</span>
                                <strong>Save</strong>
                                <small>Smarter</small>
                            </div>
                            <div>
                                <span>◎</span>
                                <strong>Reach</strong>
                                <small>Goals</small>
                            </div>
                            <div>
                                <span>↗</span>
                                <strong>Build</strong>
                                <small>Your Future</small>
                            </div>
                        </div>
                    </div>

                    <div className="bb-hero-note">
                        Small steps today. Big dreams tomorrow.
                    </div>
                </section>

                <section className="bb-auth-right">
                    <div className="bb-login-card">
                        <div className="bb-card-brand">
                            <div className="bb-logo">✦</div>
                            <h2>Budget<span>Buddy</span></h2>
                        </div>

                        <h3>
                            {login
                                ? 'Welcome back, Student!'
                                : 'Create your account'}
                        </h3>

                        <p className="bb-subtitle">
                            {login
                                ? 'Log in to continue your financial journey.'
                                : 'Start building smarter money habits today.'}
                        </p>

                        <form onSubmit={auth}>
                            {!login && (
                                <label className="bb-field">
                                    Full Name
                                    <input
                                        type="text"
                                        placeholder="Enter your full name"
                                        required
                                        value={form.full_name}
                                        onChange={e =>
                                            setForm({
                                                ...form,
                                                full_name: e.target.value
                                            })
                                        }
                                    />
                                </label>
                            )}

                            <label className="bb-field">
                                Email Address
                                <input
                                    type="email"
                                    placeholder="Enter your email address"
                                    required
                                    value={form.email}
                                    onChange={e =>
                                        setForm({
                                            ...form,
                                            email: e.target.value
                                        })
                                    }
                                />
                            </label>

                            <label className="bb-field">
                                Password
                                <div className="bb-password">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        placeholder="Enter your password"
                                        required
                                        value={form.password}
                                        onChange={e =>
                                            setForm({
                                                ...form,
                                                password: e.target.value
                                            })
                                        }
                                    />

                                    <button
                                        type="button"
                                        className="bb-show-password"
                                        onClick={() =>
                                            setShowPassword(!showPassword)
                                        }
                                    >
                                        {showPassword ? 'Hide' : 'Show'}
                                    </button>
                                </div>
                            </label>

                            <div className="bb-security-note">
                                <span>✓ Secure student login</span>
                                <span>Smart money habits</span>
                            </div>

                            <button className="bb-submit" type="submit">
                                {login ? 'Log In  →' : 'Create Account  →'}
                            </button>
                        </form>

                        <div className="bb-switch">
                            {login
                                ? "Don't have an account?"
                                : 'Already have an account?'}

                            <button
                                type="button"
                                onClick={() => {
                                    setLogin(!login);
                                    setMsg('');
                                }}
                            >
                                {login ? 'Sign Up' : 'Log In'}
                            </button>
                        </div>

                        {msg && <p className="bb-status">{msg}</p>}
                    </div>
                </section>
            </main>
        );
    }

    return (
        <>
            <Dashboard user={user} onLogout={logout} />
            <Chatbot />
        </>
    );
}

createRoot(document.getElementById('root')).render(
    <BrowserRouter>
        <App />
    </BrowserRouter>
);
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
