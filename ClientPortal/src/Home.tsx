import { useNavigate } from 'react-router-dom'

const services = [
  {
    title: 'Power Grid Monitoring',
    description: 'Real-time monitoring of power grid infrastructure, voltage levels, and load distribution across all connected substations.',
    icon: '🔌',
    color: 'from-blue-500 to-blue-700',
  },
  {
    title: 'Energy Usage Analytics',
    description: 'Comprehensive analytics dashboards showing energy consumption patterns, peak usage forecasting, and cost optimization insights.',
    icon: '📊',
    color: 'from-green-500 to-green-700',
  },
  {
    title: 'Outage Reporting',
    description: 'Report and track power outages in your area. Get real-time status updates and estimated restoration times from field crews.',
    icon: '🚨',
    color: 'from-amber-500 to-red-600',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const userStr = localStorage.getItem('client_user')
  const user = userStr ? JSON.parse(userStr) : null

  const handleLogout = () => {
    localStorage.removeItem('client_token')
    localStorage.removeItem('client_user')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <h1 className="text-xl font-bold text-gray-900">Client Portal</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.name || 'Client User'}</p>
              <p className="text-xs text-gray-500">{user?.account_name || 'Account'}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome */}
        <div className="mb-10">
          <h2 className="text-3xl font-bold text-gray-900">
            Welcome, {user?.name?.split(' ')[0] || 'User'}
          </h2>
          <p className="mt-2 text-gray-500 text-lg">
            Access your power services and manage your account.
          </p>
        </div>

        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {services.map((service) => (
            <div
              key={service.title}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden cursor-pointer group"
            >
              <div className={`h-2 bg-gradient-to-r ${service.color}`} />
              <div className="p-6">
                <div className="text-4xl mb-4">{service.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                  {service.title}
                </h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                  {service.description}
                </p>
                <div className="mt-4">
                  <span className="inline-flex items-center text-sm font-medium text-indigo-600 group-hover:text-indigo-700">
                    Open Service
                    <svg className="ml-1 w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-20 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-sm text-gray-400">
          Client Portal - Powered by Salesforce Integration Platform
        </div>
      </footer>
    </div>
  )
}
