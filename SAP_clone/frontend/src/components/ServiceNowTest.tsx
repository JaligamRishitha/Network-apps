/**
 * ServiceNow API Test Component
 * Test the integration endpoints
 */
import React, { useState } from 'react';
import { passwordResetApi } from '../services/api';

const ServiceNowTest: React.FC = () => {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [ticketId, setTicketId] = useState('');

  const testListTickets = async () => {
    setLoading(true);
    try {
      const response = await passwordResetApi.listTickets();
      setResult(`✅ List Tickets Success:\n${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      setResult(`❌ List Tickets Error:\n${error.message}\n${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  const testGetTicket = async () => {
    if (!ticketId) {
      setResult('❌ Please enter a ticket ID');
      return;
    }
    setLoading(true);
    try {
      const response = await passwordResetApi.getTicket(ticketId);
      setResult(`✅ Get Ticket Success:\n${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      setResult(`❌ Get Ticket Error:\n${error.message}\n${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  const testUpdateStatus = async () => {
    if (!ticketId) {
      setResult('❌ Please enter a ticket ID');
      return;
    }
    setLoading(true);
    try {
      const response = await passwordResetApi.updateStatus(ticketId, 'in_progress');
      setResult(`✅ Update Status Success:\n${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      setResult(`❌ Update Status Error:\n${error.message}\n${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  const testResetPassword = async () => {
    if (!ticketId) {
      setResult('❌ Please enter a ticket ID');
      return;
    }
    setLoading(true);
    try {
      const response = await passwordResetApi.resetPassword(ticketId);
      setResult(`✅ Reset Password Success:\n${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      setResult(`❌ Reset Password Error:\n${error.message}\n${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px', margin: '20px' }}>
      <h3>ServiceNow API Test</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Enter Ticket ID for specific tests"
          value={ticketId}
          onChange={(e) => setTicketId(e.target.value)}
          style={{
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '300px',
            marginRight: '10px'
          }}
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          onClick={testListTickets}
          disabled={loading}
          style={{
            padding: '10px 15px',
            backgroundColor: '#1890ff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          Test List Tickets
        </button>
        
        <button
          onClick={testGetTicket}
          disabled={loading || !ticketId}
          style={{
            padding: '10px 15px',
            backgroundColor: '#52c41a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (loading || !ticketId) ? 'not-allowed' : 'pointer'
          }}
        >
          Test Get Ticket
        </button>
        
        <button
          onClick={testUpdateStatus}
          disabled={loading || !ticketId}
          style={{
            padding: '10px 15px',
            backgroundColor: '#fa8c16',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (loading || !ticketId) ? 'not-allowed' : 'pointer'
          }}
        >
          Test Update Status
        </button>
        
        <button
          onClick={testResetPassword}
          disabled={loading || !ticketId}
          style={{
            padding: '10px 15px',
            backgroundColor: '#f5222d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (loading || !ticketId) ? 'not-allowed' : 'pointer'
          }}
        >
          Test Reset Password
        </button>
      </div>

      {loading && <div style={{ color: '#1890ff', marginBottom: '10px' }}>Loading...</div>}
      
      {result && (
        <pre style={{
          backgroundColor: '#f5f5f5',
          padding: '15px',
          borderRadius: '4px',
          border: '1px solid #d9d9d9',
          whiteSpace: 'pre-wrap',
          fontSize: '12px',
          maxHeight: '400px',
          overflow: 'auto'
        }}>
          {result}
        </pre>
      )}
    </div>
  );
};

export default ServiceNowTest;
