import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="dashboard-layout">
        <div className="sidebar" style={{ pointerEvents: 'none' }}>
          <div className="sidebar-brand">
            <div className="skeleton" style={{ width: 34, height: 34, borderRadius: 10 }} />
            <div className="skeleton" style={{ width: 100, height: 16 }} />
          </div>
          <div className="sidebar-nav" style={{ padding: '16px 12px' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton" style={{ height: 40, marginBottom: 6, borderRadius: 10 }} />
            ))}
          </div>
        </div>
        <div className="main-content">
          <div className="main-header">
            <div className="skeleton" style={{ width: 120, height: 18 }} />
            <div className="skeleton" style={{ width: 80, height: 32, borderRadius: 10 }} />
          </div>
          <div className="main-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 32 }}>
              {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 18 }} />)}
            </div>
            <div className="skeleton" style={{ height: 180, borderRadius: 18, marginBottom: 24 }} />
            <div className="skeleton" style={{ height: 140, borderRadius: 18 }} />
          </div>
        </div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return children;
}
