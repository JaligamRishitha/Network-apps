/**
 * PM Workflow Home/Landing Page
 * Provides overview and order search functionality
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PMWorkflowNav from '../components/PMWorkflowNav';
import '../styles/sap-theme.css';

interface Order {
  order_number: string;
  order_type: string;
  status: string;
  priority: string;
  equipment_id?: string;
  functional_location?: string;
  created_at: string;
}

const PMWorkflowHome: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRecentOrders();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = orders.filter(order =>
        order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.equipment_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.functional_location?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredOrders(filtered);
    } else {
      setFilteredOrders(orders);
    }
  }, [searchTerm, orders]);

  const loadRecentOrders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/pm-workflow/orders/recent', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOrders(data);
        setFilteredOrders(data);
      }
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'created': '#666',
      'planned': '#0070f2',
      'released': '#107e3e',
      'in_progress': '#e9730c',
      'confirmed': '#0a6ed1',
      'teco': '#107e3e'
    };
    return colors[status.toLowerCase()] || '#666';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      'low': '#107e3e',
      'normal': '#0070f2',
      'high': '#e9730c',
      'urgent': '#bb0000'
    };
    return colors[priority.toLowerCase()] || '#666';
  };

  return (
    <div className="sap-page">
      <PMWorkflowNav />
      
      <div className="sap-container" style={{ padding: '24px' }}>
        {/* Header */}
        <div className="sap-object-page-header" style={{ marginBottom: '32px' }}>
          <h1 className="sap-object-page-title">PM Workflow - 6-Screen Maintenance Process</h1>
          <p className="sap-object-page-subtitle">
            Streamlined maintenance workflow from planning to completion
          </p>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <div 
            className="sap-panel" 
            style={{ cursor: 'pointer', transition: 'all 0.2s' }}
            onClick={() => navigate('/pm-workflow/screen1')}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,112,242,0.2)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '';
              e.currentTarget.style.transform = '';
            }}
          >
            <div className="sap-panel-content" style={{ textAlign: 'center', padding: '24px' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div>
              <h3 style={{ marginBottom: '8px' }}>Create New Order</h3>
              <p style={{ fontSize: '12px', color: '#666' }}>Start a new maintenance order</p>
            </div>
          </div>

          <div 
            className="sap-panel" 
            style={{ cursor: 'pointer', transition: 'all 0.2s' }}
            onClick={() => navigate('/pm-workflow/screen3')}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,112,242,0.2)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '';
              e.currentTarget.style.transform = '';
            }}
          >
            <div className="sap-panel-content" style={{ textAlign: 'center', padding: '24px' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>✅</div>
              <h3 style={{ marginBottom: '8px' }}>Release Orders</h3>
              <p style={{ fontSize: '12px', color: '#666' }}>Release orders for execution</p>
            </div>
          </div>

          <div 
            className="sap-panel" 
            style={{ cursor: 'pointer', transition: 'all 0.2s' }}
            onClick={() => navigate('/pm-workflow/screen4')}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,112,242,0.2)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '';
              e.currentTarget.style.transform = '';
            }}
          >
            <div className="sap-panel-content" style={{ textAlign: 'center', padding: '24px' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>📦</div>
              <h3 style={{ marginBottom: '8px' }}>Material Receipt</h3>
              <p style={{ fontSize: '12px', color: '#666' }}>Post goods receipts</p>
            </div>
          </div>
        </div>

        {/* Order Search */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Order Search</h3>
          </div>
          <div className="sap-panel-content">
            <div className="sap-form-group">
              <label className="sap-label">Search by Order Number, Equipment, or Location</label>
              <input
                type="text"
                className="sap-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Enter search term..."
              />
            </div>
          </div>
        </div>

        {/* Recent Orders */}
        <div className="sap-panel">
          <div className="sap-panel-header">
            <h3>Recent Orders</h3>
            <button className="sap-button" onClick={loadRecentOrders}>
              Refresh
            </button>
          </div>
          <div className="sap-panel-content">
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
            ) : filteredOrders.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                No orders found. Create a new order to get started.
              </div>
            ) : (
              <table className="sap-table">
                <thead>
                  <tr>
                    <th>Order Number</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Equipment</th>
                    <th>Location</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.order_number}>
                      <td>
                        <strong>{order.order_number}</strong>
                      </td>
                      <td>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          backgroundColor: order.order_type === 'breakdown' ? '#fff3cd' : '#e3f2fd',
                          color: order.order_type === 'breakdown' ? '#856404' : '#0070f2'
                        }}>
                          {order.order_type}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          backgroundColor: getStatusColor(order.status) + '20',
                          color: getStatusColor(order.status)
                        }}>
                          {order.status}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          backgroundColor: getPriorityColor(order.priority) + '20',
                          color: getPriorityColor(order.priority)
                        }}>
                          {order.priority}
                        </span>
                      </td>
                      <td>{order.equipment_id || '-'}</td>
                      <td>{order.functional_location || '-'}</td>
                      <td>{new Date(order.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="sap-button sap-button-transparent"
                          onClick={() => {
                            // Navigate to appropriate screen based on status
                            if (order.status === 'created' || order.status === 'planned') {
                              navigate(`/pm-workflow/screen2/${order.order_number}`);
                            } else if (order.status === 'released' || order.status === 'in_progress') {
                              navigate(`/pm-workflow/screen5/${order.order_number}`);
                            } else {
                              navigate(`/pm-workflow/screen6/${order.order_number}`);
                            }
                          }}
                        >
                          Open
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Workflow Overview */}
        <div className="sap-panel" style={{ marginTop: '24px' }}>
          <div className="sap-panel-header">
            <h3>Workflow Overview</h3>
          </div>
          <div className="sap-panel-content">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
              {[
                { num: 1, name: 'Planning', desc: 'Create & plan orders' },
                { num: 2, name: 'Procurement', desc: 'Order materials' },
                { num: 3, name: 'Release', desc: 'Validate & release' },
                { num: 4, name: 'Receipt', desc: 'Receive materials' },
                { num: 5, name: 'Execution', desc: 'Perform work' },
                { num: 6, name: 'Completion', desc: 'Close & settle' }
              ].map((screen) => (
                <div key={screen.num} style={{
                  padding: '16px',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '24px', fontWeight: 600, color: '#0070f2', marginBottom: '4px' }}>
                    {screen.num}
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>
                    {screen.name}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666' }}>
                    {screen.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PMWorkflowHome;
