import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home } from 'lucide-react';

const NotFound = () => {
  return (
    <div className="not-found-page">
      <div className="not-found-card">
        <AlertTriangle size={48} className="text-warning mb-4" />
        <h2>404 - Page Not Found</h2>
        <p className="text-muted mb-6">The page you are looking for does not exist.</p>
        <Link to="/" className="btn-primary inline-flex items-center gap-2">
          <Home size={18} />
          <span>Return Home</span>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
