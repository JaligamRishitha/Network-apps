/**
 * PM Workflow Screen 2: Procurement & Material Planning
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

interface PurchaseOrder {
  po_number: string;
  order_number: string;
  po_type: string;
  vendor_id: string;
  total_value: number;
  delivery_date: string;
  status: string;
  created_at: string;
}

interface DocumentFlowEntry {
  flow_id: string;
  document_type: string;
  document_number: string;
  transaction_date: string;
  user_id: string;
  status: string;
  related_document: string | null;
}

const PMWorkflowScreen2: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const navigate = useNavigate();
  
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [documentFlow, setDocumentFlow] = useState<DocumentFlowEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreatePO, setShowCreatePO] = useState(false);
  
  // Form state
  const [poType, setPoType] = useState<string>('material');
  const [vendorId, setVendorId] = useState<string>('');
  const [totalValue, setTotalValue] = useState<string>('');
  const [deliveryDate, setDeliveryDate] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [orderNumber]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load purchase orders
      const posResponse = await api.get(`/pm-workflow/orders/${orderNumber}/purchase-orders`);
      setPurchaseOrders(posResponse.data);
      
      // Load procurement document flow
      const flowResponse = await api.get(`/pm-workflow/orders/${orderNumber}/procurement-flow`);
      setDocumentFlow(flowResponse.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await api.post('/pm-workflow/purchase-orders', {
        order_number: orderNumber,
        po_type: poType,
        vendor_id: vendorId,
        total_value: parseFloat(totalValue),
        delivery_date: new Date(deliveryDate).toISOString(),
        created_by: 'current_user' // TODO: Get from auth context
      });
      
      // Reset form
      setShowCreatePO(false);
      setVendorId('');
      setTotalValue('');
      setDeliveryDate('');
      
      // Reload data
      await loadData();
    } catch (error) {
      console.error('Error creating PO:', error);
      alert('Failed to create purchase order');
    }
  };

  const handleUpdatePOStatus = async (poNumber: string, newStatus: string) => {
    try {
      await api.put(`/pm-workflow/purchase-orders/${poNumber}/status`, {
        status: newStatus,
        updated_by: 'current_user' // TODO: Get from auth context
      });
      
      await loadData();
    } catch (error) {
      console.error('Error updating PO status:', error);
      alert('Failed to update PO status');
    }
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Screen 2: Procurement & Material Planning</h1>
        <p className="text-gray-600">Order: {orderNumber}</p>
      </div>

      {/* Create PO Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Purchase Orders</h2>
          <button
            onClick={() => setShowCreatePO(!showCreatePO)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {showCreatePO ? 'Cancel' : 'Create PO'}
          </button>
        </div>

        {showCreatePO && (
          <form onSubmit={handleCreatePO} className="mb-6 p-4 bg-gray-50 rounded">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">PO Type</label>
                <select
                  value={poType}
                  onChange={(e) => setPoType(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  required
                >
                  <option value="material">Material</option>
                  <option value="service">Service</option>
                  <option value="combined">Combined</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Vendor ID</label>
                <input
                  type="text"
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Total Value</label>
                <input
                  type="number"
                  step="0.01"
                  value={totalValue}
                  onChange={(e) => setTotalValue(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Delivery Date</label>
                <input
                  type="date"
                  value={deliveryDate}
                  onChange={(e) => setDeliveryDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              className="mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Create Purchase Order
            </button>
          </form>
        )}

        {/* PO List */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">PO Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delivery Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchaseOrders.map((po) => (
                <tr key={po.po_number}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{po.po_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm capitalize">{po.po_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{po.vendor_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">${po.total_value.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {new Date(po.delivery_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded ${
                      po.status === 'delivered' ? 'bg-green-100 text-green-800' :
                      po.status === 'ordered' ? 'bg-blue-100 text-blue-800' :
                      po.status === 'partially_delivered' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {po.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <select
                      value={po.status}
                      onChange={(e) => handleUpdatePOStatus(po.po_number, e.target.value)}
                      className="px-2 py-1 border rounded text-xs"
                    >
                      <option value="created">Created</option>
                      <option value="ordered">Ordered</option>
                      <option value="partially_delivered">Partially Delivered</option>
                      <option value="delivered">Delivered</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {purchaseOrders.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No purchase orders yet. Create one to get started.
            </div>
          )}
        </div>
      </div>

      {/* Document Flow Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Procurement Document Flow</h2>
        
        <div className="space-y-3">
          {documentFlow.map((entry) => (
            <div key={entry.flow_id} className="flex items-start p-3 bg-gray-50 rounded">
              <div className="flex-shrink-0 w-32">
                <span className="text-xs font-medium text-gray-500">
                  {new Date(entry.transaction_date).toLocaleString()}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                    {entry.document_type}
                  </span>
                  <span className="text-sm font-medium">{entry.document_number}</span>
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Status: {entry.status} | User: {entry.user_id}
                </div>
              </div>
            </div>
          ))}
          
          {documentFlow.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No procurement activities yet.
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="mt-6 flex justify-between">
        <button
          onClick={() => navigate(`/pm-workflow/screen1/${orderNumber}`)}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          ← Back to Screen 1
        </button>
        <button
          onClick={() => navigate(`/pm-workflow/screen3/${orderNumber}`)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Continue to Screen 3 →
        </button>
      </div>
    </div>
  );
};

export default PMWorkflowScreen2;
