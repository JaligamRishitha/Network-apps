/**
 * SAP S/4HANA Home Page - My Home Dashboard
 * Based on SAP Fiori Launchpad pattern
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ticketsApi } from '../services/api';
import '../styles/sap-theme.css';

interface ToDo {
  id: string;
  title: string;
  type: string;
  priority: string;
  dueDate: string;
  status: string;
}

const Home: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [todos, setTodos] = useState<ToDo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('tasks');

  useEffect(() => {
    loadTodos();
  }, []);

  const loadTodos = async () => {
    try {
      const response = await ticketsApi.list({ status: 'open', limit: 10 });
      const tickets = response.data.tickets || [];
      setTodos(tickets.map((t: any) => ({
        id: t.ticket_id,
        title: t.title,
        type: t.ticket_type,
        priority: t.priority,
        dueDate: t.created_at,
        status: t.status
      })));
    } catch (error) {
      console.error('Failed to load todos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentDate = () => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const now = new Date();
    return `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}${getOrdinalSuffix(now.getDate())}`;
  };

  const getOrdinalSuffix = (day: number) => {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
      case 1: return 'st';
      case 2: return 'nd';
      case 3: return 'rd';
      default: return 'th';
    }
  };

  const appTiles = [
    { title: 'Sales Processing', subtitle: 'Internal Sales', color: '#0070f2', icon: '📊', path: '/sales' },
    { title: 'My Business Role Assignment', subtitle: 'OLM - Internal SAP Tools', color: '#e0008a', icon: '👤', path: '/profile' },
    { title: 'My Business Role Assignment', subtitle: 'ISM - Internal SAP Tools', color: '#f58b00', icon: '👥', path: '/profile' },
    { title: 'Customer Return Processing', subtitle: 'Internal Sales', color: '#7c2e9e', icon: '↩️', path: '/returns' },
    { title: 'Customer and Products', subtitle: 'Internal Sales', color: '#107e3e', icon: '🏢', path: '/customers' },
    { title: 'Employee Situation Handling', subtitle: 'Internal Sales', color: '#c14000', icon: '👔', path: '/employees' },
  ];

  return (
    <div style={{ backgroundColor: '#f7f7f7', minHeight: '100vh' }}>
      {/* Hero Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0070f2 0%, #0040a0 100%)',
        padding: '32px 40px',
        color: 'white',
        marginBottom: '24px'
      }}>
        <div style={{ fontSize: '14px', marginBottom: '8px', opacity: 0.9 }}>
          {getCurrentDate()}
        </div>
        <h1 style={{ margin: 0, fontSize: '32px', fontWeight: 300 }}>
          Hi {user?.username || 'User'}!
        </h1>
        <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
          <button 
            className="sap-toolbar-button"
            style={{ backgroundColor: 'white', color: '#0070f2', border: 'none' }}
          >
            + Add Content
          </button>
          <button 
            className="sap-toolbar-button"
            style={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}
          >
            Action
          </button>
          <button 
            className="sap-toolbar-button"
            style={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}
            onClick={() => navigate('/settings')}
          >
            My Home Settings
          </button>
        </div>
      </div>

      <div style={{ padding: '0 40px' }}>
        {/* To Dos Section */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 400 }}>To Dos</h2>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: '#6a6d70' }}>🔄 1 min. ago</span>
              <button 
                className="sap-toolbar-button"
                style={{ padding: '4px 12px', fontSize: '13px' }}
                onClick={loadTodos}
              >
                Show More
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ 
            borderBottom: '2px solid #e5e5e5',
            marginBottom: '16px',
            display: 'flex',
            gap: '24px'
          }}>
            <div 
              onClick={() => setSelectedTab('tasks')}
              style={{
                padding: '12px 0',
                borderBottom: selectedTab === 'tasks' ? '3px solid #0070f2' : '3px solid transparent',
                color: selectedTab === 'tasks' ? '#0070f2' : '#32363a',
                fontWeight: selectedTab === 'tasks' ? 600 : 400,
                cursor: 'pointer',
                marginBottom: '-2px'
              }}
            >
              Tasks ({todos.length})
            </div>
            <div 
              onClick={() => setSelectedTab('situations')}
              style={{
                padding: '12px 0',
                borderBottom: selectedTab === 'situations' ? '3px solid #0070f2' : '3px solid transparent',
                color: selectedTab === 'situations' ? '#0070f2' : '#32363a',
                fontWeight: selectedTab === 'situations' ? 600 : 400,
                cursor: 'pointer',
                marginBottom: '-2px'
              }}
            >
              Situations (0)
            </div>
          </div>

          {/* To Do Cards */}
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
              Loading...
            </div>
          ) : todos.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
              No pending tasks
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {todos.slice(0, 3).map((todo) => (
                <div 
                  key={todo.id}
                  className="sap-fiori-card"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/tickets/${todo.id}`)}
                >
                  <div className="sap-fiori-card-content">
                    <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div style={{ 
                        width: '40px', 
                        height: '40px', 
                        backgroundColor: '#fff3e0',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginRight: '12px',
                        fontSize: '20px'
                      }}>
                        ⚠️
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>
                          {todo.title}
                        </div>
                        <div style={{ fontSize: '12px', color: '#6a6d70' }}>
                          {todo.type}
                        </div>
                      </div>
                    </div>
                    <div style={{ fontSize: '13px', marginBottom: '12px' }}>
                      Priority: <span className={`sap-status ${
                        todo.priority === 'high' ? 'error' :
                        todo.priority === 'medium' ? 'warning' : 'info'
                      }`}>
                        {todo.priority.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button 
                        className="sap-toolbar-button"
                        style={{ flex: 1, padding: '6px 12px', fontSize: '13px' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/tickets/${todo.id}`);
                        }}
                      >
                        View Details
                      </button>
                      <button 
                        className="sap-toolbar-button"
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          // Handle action
                        }}
                      >
                        Action
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pages Section */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: 400 }}>Pages</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '16px' }}>
            {appTiles.map((tile, index) => (
              <div
                key={index}
                onClick={() => navigate(tile.path)}
                style={{
                  backgroundColor: tile.color,
                  color: 'white',
                  padding: '24px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  minHeight: '120px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ fontSize: '28px', marginBottom: '8px' }}>{tile.icon}</div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>
                    {tile.title}
                  </div>
                  <div style={{ fontSize: '12px', opacity: 0.9 }}>
                    {tile.subtitle}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Apps Section */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 400 }}>Apps</h2>
            <button 
              className="sap-toolbar-button"
              style={{ padding: '4px 12px', fontSize: '13px' }}
            >
              🔍 Add Apps
            </button>
          </div>

          <div style={{ 
            borderBottom: '1px solid #e5e5e5',
            marginBottom: '16px',
            display: 'flex',
            gap: '24px'
          }}>
            {['Favourites', 'Most Used', 'Recently Used', 'Recommended'].map((tab) => (
              <div 
                key={tab}
                style={{
                  padding: '12px 0',
                  color: '#32363a',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                {tab}
              </div>
            ))}
          </div>

          <div style={{ padding: '20px', textAlign: 'center', color: '#6a6d70' }}>
            No apps configured yet
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
