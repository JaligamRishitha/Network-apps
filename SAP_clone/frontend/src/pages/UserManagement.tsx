/**
 * User Management Page
 * Admin-only page to view, create, and manage users
 */
import React, { useState, useEffect } from 'react';
import { usersApi } from '../services/api';

interface User {
  username: string;
  roles: string[];
  created_at?: string;
  last_login?: string;
}

const AVAILABLE_ROLES = [
  { value: 'Maintenance_Engineer', label: 'Maintenance Engineer (PM)' },
  { value: 'Store_Manager', label: 'Store Manager (MM)' },
  { value: 'Finance_Officer', label: 'Finance Officer (FI)' },
  { value: 'Admin', label: 'Administrator' },
];

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState({
    username: '',
    password: '',
    roles: [] as string[],
  });
  const [passwordForm, setPasswordForm] = useState({
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await usersApi.list();
      setUsers(response.data.users);
    } catch (error: any) {
      console.error('Failed to load users:', error);
      if (error.response?.status === 403) {
        alert('Access denied. Admin role required.');
      } else {
        alert('Failed to load users');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (createForm.roles.length === 0) {
      alert('Please select at least one role');
      return;
    }

    try {
      await usersApi.create({
        username: createForm.username,
        password: createForm.password,
        roles: createForm.roles,
      });
      
      alert(`User '${createForm.username}' created successfully!`);
      setShowCreateModal(false);
      setCreateForm({ username: '', password: '', roles: [] });
      loadUsers();
    } catch (error: any) {
      console.error('Failed to create user:', error);
      alert(`Failed to create user: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    if (!selectedUser) return;

    try {
      await usersApi.changePassword(selectedUser, passwordForm.newPassword);
      alert(`Password changed successfully for user '${selectedUser}'`);
      setShowPasswordModal(false);
      setPasswordForm({ newPassword: '', confirmPassword: '' });
      setSelectedUser(null);
    } catch (error: any) {
      console.error('Failed to change password:', error);
      alert(`Failed to change password: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Are you sure you want to delete user '${username}'?`)) {
      return;
    }

    try {
      await usersApi.delete(username);
      alert(`User '${username}' deleted successfully`);
      loadUsers();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      alert(`Failed to delete user: ${error.response?.data?.detail || error.message}`);
    }
  };

  const toggleRole = (role: string) => {
    setCreateForm(prev => ({
      ...prev,
      roles: prev.roles.includes(role)
        ? prev.roles.filter(r => r !== role)
        : [...prev.roles, role],
    }));
  };

  const getRoleBadgeColor = (role: string): string => {
    const colors: Record<string, string> = {
      'Maintenance_Engineer': '#1890ff',
      'Store_Manager': '#fa8c16',
      'Finance_Officer': '#52c41a',
      'Admin': '#f5222d',
    };
    return colors[role] || '#666';
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>👥 User Management</h1>
            <p style={{ margin: '8px 0 0 0', color: '#666' }}>
              Manage system users, roles, and permissions (Admin only)
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '12px 24px',
              backgroundColor: '#1890ff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '14px',
            }}
          >
            + Create User
          </button>
        </div>
      </div>

      {/* Stats Card */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Users</div>
          <div style={{ fontSize: '28px', fontWeight: 600, color: '#1890ff' }}>
            {users.length}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Admins</div>
          <div style={{ fontSize: '28px', fontWeight: 600, color: '#f5222d' }}>
            {users.filter(u => u.roles.includes('Admin')).length}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Engineers</div>
          <div style={{ fontSize: '28px', fontWeight: 600, color: '#1890ff' }}>
            {users.filter(u => u.roles.includes('Maintenance_Engineer')).length}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Managers</div>
          <div style={{ fontSize: '28px', fontWeight: 600, color: '#fa8c16' }}>
            {users.filter(u => u.roles.includes('Store_Manager')).length}
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e8e8e8' }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>System Users</h2>
        
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>Loading users...</div>
        ) : users.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👥</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>No users found</div>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e8e8e8', backgroundColor: '#fafafa' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: '#666' }}>Username</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: '#666' }}>Roles</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: '#666' }}>Created</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '13px', fontWeight: 600, color: '#666' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.username} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '12px', fontSize: '14px', fontWeight: 500 }}>
                    {user.username}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {user.roles.map(role => (
                        <span
                          key={role}
                          style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            backgroundColor: getRoleBadgeColor(role),
                            color: 'white',
                            fontSize: '11px',
                            fontWeight: 600,
                          }}
                        >
                          {role.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '12px', fontSize: '13px', color: '#666' }}>
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                      <button
                        onClick={() => {
                          setSelectedUser(user.username);
                          setShowPasswordModal(true);
                        }}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#fa8c16',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: 500,
                        }}
                      >
                        Change Password
                      </button>
                      {user.username !== 'admin' && (
                        <button
                          onClick={() => handleDeleteUser(user.username)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#ff4d4f',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: 500,
                          }}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            width: '500px',
            maxHeight: '90vh',
            overflow: 'auto',
          }}>
            <h2 style={{ marginTop: 0 }}>👤 Create New User</h2>
            <form onSubmit={handleCreateUser}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>
                  Username
                </label>
                <input
                  type="text"
                  value={createForm.username}
                  onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                  required
                  placeholder="Enter username"
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  required
                  placeholder="Enter password"
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500, fontSize: '14px' }}>
                  Roles (select at least one)
                </label>
                {AVAILABLE_ROLES.map(role => (
                  <div key={role.value} style={{ marginBottom: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={createForm.roles.includes(role.value)}
                        onChange={() => toggleRole(role.value)}
                        style={{ marginRight: '8px' }}
                      />
                      <span style={{ fontSize: '14px' }}>{role.label}</span>
                    </label>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateForm({ username: '', password: '', roles: [] });
                  }}
                  style={{
                    padding: '10px 20px',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    backgroundColor: 'white',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#1890ff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 500,
                  }}
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            width: '400px',
          }}>
            <h2 style={{ marginTop: 0 }}>🔑 Change Password</h2>
            <p style={{ color: '#666', fontSize: '14px' }}>
              Changing password for user: <strong>{selectedUser}</strong>
            </p>
            <form onSubmit={handleChangePassword}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                  required
                  placeholder="Enter new password"
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  required
                  placeholder="Confirm new password"
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordForm({ newPassword: '', confirmPassword: '' });
                    setSelectedUser(null);
                  }}
                  style={{
                    padding: '10px 20px',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    backgroundColor: 'white',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#fa8c16',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 500,
                  }}
                >
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
