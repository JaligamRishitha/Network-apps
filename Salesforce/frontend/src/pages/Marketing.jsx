import { ChevronDownIcon } from '@heroicons/react/24/outline';

export default function Marketing() {
  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Marketing</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            <button className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500">
              Marketing
            </button>
            <button className="py-2 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 flex items-center">
              List Emails
              <ChevronDownIcon className="w-3 h-3 ml-1" />
            </button>
          </nav>
        </div>
      </div>

      {/* Hero Banner */}
      <div className="p-6">
        <div className="relative rounded-lg overflow-hidden bg-gradient-to-r from-orange-400 via-orange-300 to-green-600 min-h-[400px]">
          {/* Mountains illustration */}
          <div className="absolute inset-0">
            <svg viewBox="0 0 1200 400" className="w-full h-full" preserveAspectRatio="xMidYMid slice">
              <defs>
                <linearGradient id="sky" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#87CEEB" />
                  <stop offset="100%" stopColor="#E0F4FF" />
                </linearGradient>
              </defs>
              <rect fill="url(#sky)" width="1200" height="400" />
              {/* Mountains */}
              <path d="M0 400 L200 200 L400 350 L600 150 L800 300 L1000 180 L1200 400 Z" fill="#228B22" opacity="0.3" />
              <path d="M0 400 L150 250 L350 380 L550 200 L750 320 L950 220 L1200 400 Z" fill="#228B22" opacity="0.5" />
              <path d="M0 400 L100 300 L300 400 L500 280 L700 380 L900 300 L1100 380 L1200 400 Z" fill="#228B22" />
              {/* Hills */}
              <ellipse cx="100" cy="420" rx="150" ry="80" fill="#32CD32" />
              <ellipse cx="1100" cy="420" rx="180" ry="100" fill="#32CD32" />
              {/* Plants */}
              <path d="M150 350 Q155 330, 160 350 M155 350 L155 370" stroke="#006400" strokeWidth="3" fill="none" />
              <path d="M165 355 Q170 335, 175 355 M170 355 L170 370" stroke="#006400" strokeWidth="3" fill="none" />
            </svg>
          </div>

          {/* Content */}
          <div className="relative z-10 flex flex-col items-center justify-center h-full py-16 px-8 text-center">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Activate powerful marketing<br />tools and boost sales
            </h2>
            <p className="text-lg text-gray-700 max-w-2xl mb-6">
              Accelerate lead generation with impactful campaigns and use analytics to refine
              your marketing strategy. There's no additional cost for these marketing tools; you
              just need to activate them.
            </p>
            <button className="btn-primary text-lg px-8 py-3">
              Activate Marketing →
            </button>
          </div>
        </div>

        {/* Additional Feature Section */}
        <div className="mt-8 grid grid-cols-2 gap-8">
          <div className="card p-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Send emails with ease</h3>
            <p className="text-gray-600 mb-4">
              Create engaging email campaigns directly from your CRM without any coding knowledge.
            </p>
            <button className="text-sf-blue-500 font-medium hover:underline">
              Learn more →
            </button>
          </div>

          <div className="card p-6">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Email Templates</h4>
                <p className="text-sm text-gray-500">Pre-built designs to get started quickly</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
