export default function Commerce() {
  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Commerce</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            <button className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500">
              Store
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="card p-8">
          <div className="flex items-start space-x-8">
            {/* Illustration */}
            <div className="flex-shrink-0">
              <div className="relative w-72 h-72">
                {/* Background circle */}
                <div className="absolute inset-0 bg-blue-100 rounded-full"></div>

                {/* Phone illustration */}
                <div className="absolute top-8 left-8 w-24 h-40 bg-white rounded-lg shadow-lg border border-gray-200">
                  <div className="p-2">
                    <div className="w-full h-4 bg-gray-200 rounded mb-2"></div>
                    <div className="w-3/4 h-3 bg-gray-100 rounded mb-4"></div>
                    <div className="space-y-2">
                      <div className="flex space-x-1">
                        <div className="w-8 h-8 bg-blue-200 rounded"></div>
                        <div className="w-8 h-8 bg-green-200 rounded"></div>
                      </div>
                    </div>
                  </div>
                  <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2">
                    <div className="px-4 py-1 bg-green-500 rounded text-white text-xs">Pay Now</div>
                  </div>
                </div>

                {/* Character */}
                <div className="absolute bottom-4 right-8">
                  <svg viewBox="0 0 80 100" className="w-20 h-24">
                    {/* Astro character */}
                    <ellipse cx="40" cy="90" rx="15" ry="5" fill="#8B4513" opacity="0.3" />
                    <path d="M30 85 Q40 70, 50 85" fill="#8B4513" />
                    <circle cx="40" cy="50" r="25" fill="#FFF" stroke="#333" strokeWidth="2" />
                    <circle cx="35" cy="45" r="5" fill="#333" />
                    <circle cx="45" cy="45" r="5" fill="#333" />
                    <path d="M35 58 Q40 63, 45 58" stroke="#333" strokeWidth="2" fill="none" />
                    <circle cx="30" cy="40" r="3" fill="#87CEEB" />
                    <circle cx="50" cy="40" r="3" fill="#87CEEB" />
                  </svg>
                </div>

                {/* Tree */}
                <div className="absolute bottom-0 left-4">
                  <svg viewBox="0 0 40 60" className="w-10 h-16">
                    <rect x="17" y="40" width="6" height="20" fill="#8B4513" />
                    <polygon points="20,0 40,40 0,40" fill="#228B22" />
                    <polygon points="20,10 35,35 5,35" fill="#32CD32" />
                  </svg>
                </div>

                {/* Bird */}
                <div className="absolute top-12 right-12">
                  <svg viewBox="0 0 20 20" className="w-6 h-6 text-orange-500">
                    <path fill="currentColor" d="M10 2 Q15 5, 18 8 Q15 8, 12 10 Q15 12, 18 12 Q15 15, 10 18 Q5 15, 2 12 Q5 12, 8 10 Q5 8, 2 8 Q5 5, 10 2" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 pt-8">
              <h2 className="text-3xl font-bold text-gray-900 italic mb-4">
                Introducing Commerce GPT
              </h2>
              <p className="text-lg text-gray-600 mb-2">
                Power Commerce everywhere with AI + Data + CRM.
              </p>
              <p className="text-lg text-gray-600 mb-6">
                If you're interested, let us know and we'll reach out to you.
              </p>

              <button className="btn-primary text-lg px-6 py-2.5">
                I'm Interested
              </button>

              <div className="mt-8 pt-8 border-t">
                <p className="text-sm text-gray-500 italic">
                  "54% of revenue is expected to come from digital channels by 2024"
                </p>
                <a href="#" className="text-sm text-sf-blue-500 hover:underline">
                  -Salesforce State of Commerce
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
