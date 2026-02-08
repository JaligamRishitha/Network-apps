/**
 * Login Page
 * Requirement 7.1 - Login form with role selection
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import logger from '../utils/logger';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    logger.userAction('Login form submitted', { username }, 'LOGIN');

    try {
      await login(username, password);
      logger.info('Login successful, redirecting to dashboard', { username }, 'LOGIN');
      navigate('/');
    } catch (err: any) {
      logger.error('Login failed', err, 'LOGIN');
      setError(err.response?.data?.detail || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const demoUsers = [
    { username: 'engineer', password: 'engineer123', role: 'Maintenance Engineer' },
    { username: 'manager', password: 'manager123', role: 'Store Manager' },
    { username: 'finance', password: 'finance123', role: 'Finance Officer' },
    { username: 'admin', password: 'admin123', role: 'Admin' },
  ];

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f0f2f5'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '40px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        width: '400px'
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: '24px' }}>SAP ERP</h1>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px' }}>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
              required
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
              required
            />
          </div>

          {error && (
            <div style={{
              padding: '12px 16px',
              marginBottom: '16px',
              borderRadius: '4px',
              backgroundColor: error.toLowerCase().includes('expired') ? '#fff2e8' : '#fff1f0',
              border: error.toLowerCase().includes('expired') ? '1px solid #ffbb96' : '1px solid #ffa39e',
              color: error.toLowerCase().includes('expired') ? '#d4380d' : '#cf1322',
              fontSize: '14px',
            }}>
              {error.toLowerCase().includes('expired') && <span style={{ marginRight: '8px' }}>&#9888;</span>}
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#1890ff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{ marginTop: '24px' }}>
          <h4>Demo Users:</h4>
          <ul style={{ fontSize: '12px', color: '#666' }}>
            {demoUsers.map((u) => (
              <li key={u.username}>
                <strong>{u.username}</strong> / {u.password} ({u.role})
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Login;
