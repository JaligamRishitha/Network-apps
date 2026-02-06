import { useState, useEffect } from 'react';
import { serviceAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function ServiceManagement() {
  const [activeTab, setActiveTab] = useState('quotations');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      let response;
      if (activeTab === 'quotations') {
        response = await serviceAPI.listQuotations();
      } else if (activeTab === 'invoices') {
        response = await serviceAPI.listInvoices();
      } else if (activeTab === 'service-accounts') {
        response = await serviceAPI.listServiceAccounts();
      } else if (activeTab === 'warranty-extensions') {
        response = await serviceAPI.listWarrantyExtensions();
      } else if (activeTab === 'slas') {
        response = await serviceAPI.listSLAs();
      }
      setData(response.data.items || []);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRecord = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        account_id: parseInt(formData.account_id),
        title: formData.title,
        amount: parseFloat(formData.amount),
        tax_amount: parseFloat(formData.tax_amount || 0),
      };
      
      console.log('Sending payload:', payload);
      
      if (activeTab === 'quotations') {
        await serviceAPI.createQuotation(payload);
      } else if (activeTab === 'invoices') {
        const invoicePayload = {
          ...payload,
          description: formData.description,
          invoice_type: formData.invoice_type || 'Standard',
        };
        delete invoicePayload.title;
        console.log('Invoice payload:', invoicePayload);
        await serviceAPI.createInvoice(invoicePayload);
      } else if (activeTab === 'service-accounts') {
        await serviceAPI.createServiceAccount({
          account_id: parseInt(formData.account_id),
          warranty_status: formData.warranty_status || 'Active',
          service_level: formData.service_level || 'Silver',
        });
      } else if (activeTab === 'warranty-extensions') {
        await serviceAPI.createWarrantyExtension({
          service_account_id: parseInt(formData.service_account_id),
          extension_start_date: formData.extension_start_date,
          extension_end_date: formData.extension_end_date,
          extension_cost: parseFloat(formData.extension_cost || 0),
        });
      } else if (activeTab === 'slas') {
        await serviceAPI.createSLA({
          service_account_id: parseInt(formData.service_account_id),
          name: formData.name,
          response_time_hours: parseInt(formData.response_time_hours),
          resolution_time_hours: parseInt(formData.resolution_time_hours),
          uptime_percentage: parseFloat(formData.uptime_percentage || 99.9),
          support_hours: formData.support_hours || '24/7',
        });
      }
      toast.success('Record created successfully!');
      setShowForm(false);
      setFormData({});
      loadData();
    } catch (error) {
      console.error('Full error:', error);
      console.error('Error response:', error.response?.data);
      toast.error(error.response?.data?.detail || error.message || 'Failed to create record');
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Service Management</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + New
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="flex px-6">
          {[
            { id: 'quotations', label: 'Quotations' },
            { id: 'invoices', label: 'Invoices' },
            { id: 'service-accounts', label: 'Service Accounts' },
            { id: 'warranty-extensions', label: 'Warranty Extensions' },
            { id: 'slas', label: 'SLAs' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">Loading...</p>
          </div>
        ) : data.length === 0 ? (
          <div className="bg-white rounded-lg p-8 text-center">
            <p className="text-gray-500 mb-4">No records found</p>
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create First Record
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">ID</th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Details</th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Amount</th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.map((record) => (
                  <tr key={record.id} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{record.id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {activeTab === 'quotations' && record.quotation_number}
                      {activeTab === 'invoices' && record.invoice_number}
                      {activeTab === 'service-accounts' && `Account ${record.account_id}`}
                      {activeTab === 'warranty-extensions' && `Service Acc ${record.service_account_id}`}
                      {activeTab === 'slas' && record.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {activeTab === 'quotations' && `£${record.amount}`}
                      {activeTab === 'invoices' && `£${record.amount}`}
                      {activeTab === 'service-accounts' && record.service_level}
                      {activeTab === 'warranty-extensions' && `£${record.extension_cost}`}
                      {activeTab === 'slas' && `${record.response_time_hours}h`}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {activeTab === 'quotations' && record.status}
                      {activeTab === 'invoices' && record.status}
                      {activeTab === 'service-accounts' && record.warranty_status}
                      {activeTab === 'warranty-extensions' && record.status}
                      {activeTab === 'slas' && 'Active'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Create {activeTab}</h2>
            <form onSubmit={handleCreateRecord} className="space-y-4">
              {activeTab === 'quotations' && (
                <>
                  <input
                    type="number"
                    placeholder="Account ID"
                    value={formData.account_id || ''}
                    onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Title"
                    value={formData.title || ''}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Amount"
                    value={formData.amount || ''}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Tax Amount"
                    value={formData.tax_amount || ''}
                    onChange={(e) => setFormData({...formData, tax_amount: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </>
              )}
              {activeTab === 'invoices' && (
                <>
                  <input
                    type="number"
                    placeholder="Account ID"
                    value={formData.account_id || ''}
                    onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <select
                    value={formData.invoice_type || 'Standard'}
                    onChange={(e) => setFormData({...formData, invoice_type: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option>Standard</option>
                    <option>Proforma</option>
                    <option>Credit Note</option>
                  </select>
                  <input
                    type="number"
                    placeholder="Amount"
                    value={formData.amount || ''}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Tax Amount"
                    value={formData.tax_amount || ''}
                    onChange={(e) => setFormData({...formData, tax_amount: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </>
              )}
              {activeTab === 'service-accounts' && (
                <>
                  <input
                    type="number"
                    placeholder="Account ID"
                    value={formData.account_id || ''}
                    onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <select
                    value={formData.warranty_status || 'Active'}
                    onChange={(e) => setFormData({...formData, warranty_status: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option>Active</option>
                    <option>Expired</option>
                    <option>Extended</option>
                  </select>
                  <select
                    value={formData.service_level || 'Silver'}
                    onChange={(e) => setFormData({...formData, service_level: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option>Gold</option>
                    <option>Silver</option>
                    <option>Bronze</option>
                  </select>
                </>
              )}
              {activeTab === 'warranty-extensions' && (
                <>
                  <input
                    type="number"
                    placeholder="Service Account ID"
                    value={formData.service_account_id || ''}
                    onChange={(e) => setFormData({...formData, service_account_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="date"
                    placeholder="Start Date"
                    value={formData.extension_start_date || ''}
                    onChange={(e) => setFormData({...formData, extension_start_date: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="date"
                    placeholder="End Date"
                    value={formData.extension_end_date || ''}
                    onChange={(e) => setFormData({...formData, extension_end_date: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Cost"
                    value={formData.extension_cost || ''}
                    onChange={(e) => setFormData({...formData, extension_cost: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </>
              )}
              {activeTab === 'slas' && (
                <>
                  <input
                    type="number"
                    placeholder="Service Account ID"
                    value={formData.service_account_id || ''}
                    onChange={(e) => setFormData({...formData, service_account_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="text"
                    placeholder="SLA Name"
                    value={formData.name || ''}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Response Time (hours)"
                    value={formData.response_time_hours || ''}
                    onChange={(e) => setFormData({...formData, response_time_hours: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Resolution Time (hours)"
                    value={formData.resolution_time_hours || ''}
                    onChange={(e) => setFormData({...formData, resolution_time_hours: e.target.value})}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </>
              )}
              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setFormData({});
                  }}
                  className="flex-1 px-4 py-2 bg-gray-300 text-gray-900 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
