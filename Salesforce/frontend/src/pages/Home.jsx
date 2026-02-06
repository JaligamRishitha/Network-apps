import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  UserGroupIcon,
  ChartBarSquareIcon,
  FolderIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/solid';
import { useAuth } from '../context/AuthContext';
import DashboardCard from '../components/DashboardCard';
import RecordFormModal from '../components/RecordFormModal';
import {
  leadsAPI,
  opportunitiesAPI,
  contactsAPI,
  casesAPI,
  dashboardAPI,
} from '../services/api';

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [leads, setLeads] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [casesByPriority, setCasesByPriority] = useState({});
  const [recentRecords, setRecentRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showWelcome, setShowWelcome] = useState(true);
  const [modalType, setModalType] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [leadsRes, oppsRes, contactsRes, casesRes, recentRes] = await Promise.all([
        leadsAPI.list({ page_size: 5, owner_id: user?.id }),
        opportunitiesAPI.list({ page_size: 5, owner_id: user?.id }),
        contactsAPI.list({ page_size: 5, owner_id: user?.id }),
        casesAPI.getByPriority(user?.id),
        dashboardAPI.getRecentRecords(10),
      ]);

      setLeads(leadsRes.data.items.map(l => ({
        id: l.id,
        name: l.full_name || `${l.first_name} ${l.last_name}`,
        subtitle: l.company,
        status: l.status,
      })));

      setOpportunities(oppsRes.data.items.map(o => ({
        id: o.id,
        name: o.name,
        subtitle: `$${o.amount?.toLocaleString() || 0}`,
        status: o.stage,
      })));

      setContacts(contactsRes.data.items.map(c => ({
        id: c.id,
        name: c.full_name || `${c.first_name} ${c.last_name}`,
        subtitle: c.account_name,
      })));

      setCasesByPriority(casesRes.data);
      setRecentRecords(recentRes.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRecord = async (objectType, data) => {
    const apis = {
      contact: contactsAPI,
      lead: leadsAPI,
      opportunity: opportunitiesAPI,
      case: casesAPI,
    };
    await apis[objectType].create(data);
    loadDashboardData();
  };

  const getRecordTypeIcon = (type) => {
    const icons = {
      contact: <UserGroupIcon className="w-5 h-5 text-purple-500" />,
      account: <FolderIcon className="w-5 h-5 text-indigo-500" />,
      lead: <ChartBarSquareIcon className="w-5 h-5 text-green-500" />,
      opportunity: <ChartBarSquareIcon className="w-5 h-5 text-yellow-500" />,
      case: <DocumentTextIcon className="w-5 h-5 text-pink-500" />,
    };
    return icons[type] || icons.contact;
  };

  const getPlural = (type) => {
    if (type === 'opportunity') return 'opportunities';
    return `${type}s`;
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Home</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button type="button" className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500">
              Home
            </button>
          </nav>
        </div>
      </div>

      {/* Welcome Section */}
      {showWelcome && (
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 mb-6">
          <div className="flex">
            <div className="flex-1">
              <button
                type="button"
                onClick={() => setShowWelcome(false)}
                className="text-gray-400 hover:text-gray-600 float-left mr-4"
              >
                <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Welcome, {user?.first_name || user?.username}
              </h2>
              <p className="text-gray-600 mb-4">
                Check out these suggestions to kick off your day.
              </p>
              <button type="button" className="text-sf-blue-500 hover:underline text-sm font-medium">
                View All Cards
              </button>
            </div>

            {/* Suggestion Cards */}
            <div className="flex space-x-4 ml-8">
              {/* Create First Contact */}
              <div className="bg-white rounded-lg p-4 w-56 shadow-sm relative">
                <button type="button" className="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
                  <XMarkIcon className="w-4 h-4" />
                </button>
                <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <h3 className="text-sf-blue-500 font-medium mb-2 hover:underline cursor-pointer" onClick={() => setModalType('contact')}>
                  Create your first contact
                </h3>
                <p className="text-sm text-gray-600">
                  Growing your sales starts with contacts. Let's walk through it.
                </p>
              </div>

              {/* Create First Lead */}
              <div className="bg-white rounded-lg p-4 w-56 shadow-sm relative">
                <button type="button" className="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
                  <XMarkIcon className="w-4 h-4" />
                </button>
                <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <h3 className="text-sf-blue-500 font-medium mb-2 hover:underline cursor-pointer" onClick={() => setModalType('lead')}>
                  Create your first lead
                </h3>
                <p className="text-sm text-gray-600">
                  Let us show you how easy it is to convert your leads into contacts, accounts, and opportunities.
                </p>
              </div>

              {/* Create First Deal */}
              <div className="bg-white rounded-lg p-4 w-56 shadow-sm relative">
                <button type="button" className="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
                  <XMarkIcon className="w-4 h-4" />
                </button>
                <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <h3 className="text-sf-blue-500 font-medium mb-2 hover:underline cursor-pointer" onClick={() => setModalType('opportunity')}>
                  Create your first deal
                </h3>
                <p className="text-sm text-gray-600">
                  Add an opportunity and see how easy it is to track stages as your deals move forward.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* My Leads */}
        <DashboardCard
          title="My Leads"
          icon={<ChartBarSquareIcon className="w-5 h-5 text-white" />}
          iconColor="bg-green-500"
          items={leads}
          objectType="lead"
          emptyTitle="Track progress as you qualify leads."
          emptyActionLabel="Add a Lead"
          onNewClick={() => setModalType('lead')}
          loading={loading}
        />

        {/* My Opportunities */}
        <DashboardCard
          title="My Opportunities"
          icon={<ChartBarSquareIcon className="w-5 h-5 text-white" />}
          iconColor="bg-yellow-500"
          items={opportunities}
          objectType="opportunity"
          emptyTitle="View your deals to keep them moving."
          emptyActionLabel="Add an Opportunity"
          onNewClick={() => setModalType('opportunity')}
          loading={loading}
        />

        {/* My Contacts */}
        <DashboardCard
          title="My Contacts"
          icon={<UserGroupIcon className="w-5 h-5 text-white" />}
          iconColor="bg-purple-500"
          items={contacts}
          objectType="contact"
          emptyTitle="Add contacts and see who is new."
          emptyActionLabel="Add a Contact"
          onNewClick={() => setModalType('contact')}
          loading={loading}
        />

        {/* Recent Records */}
        <div className="card">
          <div className="p-3 border-b flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Recent Records</h3>
            <button type="button" className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          <div className="divide-y max-h-64 overflow-auto">
            {recentRecords.length > 0 ? (
              recentRecords.map((record) => (
                <button
                  type="button"
                  key={`${record.record_type}-${record.record_id}`}
                  onClick={() => navigate(`/${getPlural(record.record_type)}/${record.record_id}`)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center mr-3">
                    {getRecordTypeIcon(record.record_type)}
                  </div>
                  <span className="text-sm text-sf-blue-500 hover:underline">
                    {record.record_name}
                  </span>
                </button>
              ))
            ) : (
              <div className="p-4 text-sm text-gray-500 text-center">
                No recent records
              </div>
            )}
          </div>
          {recentRecords.length > 0 && (
            <div className="p-2 border-t text-center">
              <button type="button" className="text-xs text-sf-blue-500 hover:underline">
                View All
              </button>
            </div>
          )}
        </div>

        {/* All New Cases By Priority */}
        <div className="card">
          <div className="p-3 border-b flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-pink-500 rounded-md flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-sm font-medium text-gray-900">All New Cases By Priority</span>
            </div>
            <button
              type="button"
              onClick={() => setModalType('case')}
              className="px-3 py-1 text-sm font-medium text-sf-blue-500 border border-sf-blue-500 rounded-md hover:bg-sf-blue-50"
            >
              New
            </button>
          </div>
          <div className="p-4">
            {Object.keys(casesByPriority).length > 0 ? (
              <div className="space-y-3">
                {['Critical', 'High', 'Medium', 'Low'].map((priority) => (
                  casesByPriority[priority] > 0 && (
                    <div key={priority} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{priority}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        priority === 'Critical' ? 'bg-red-100 text-red-800' :
                        priority === 'High' ? 'bg-orange-100 text-orange-800' :
                        priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {casesByPriority[priority]}
                      </span>
                    </div>
                  )
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No open cases</p>
              </div>
            )}
          </div>
        </div>

        {/* Make It Your Home */}
        <div className="card">
          <div className="p-3 border-b flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Make It Your Home</h3>
            <button type="button" className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          <div className="p-4 text-center">
            <p className="text-sm text-gray-600 mb-2">
              To replace a card, click its action menu and select <strong>Change Home Card</strong>.
              Use the filters on cards to personalize your view even more.
            </p>
            <div className="mt-4 p-3 bg-blue-50 rounded-lg inline-block">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 bg-sf-blue-500 rounded-full"></div>
                <div className="w-24 h-2 bg-gray-200 rounded"></div>
                <div className="w-6 h-6 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Record Form Modal */}
      <RecordFormModal
        isOpen={!!modalType}
        onClose={() => setModalType(null)}
        objectType={modalType}
        onSave={(data) => handleSaveRecord(modalType, data)}
      />
    </div>
  );
}
