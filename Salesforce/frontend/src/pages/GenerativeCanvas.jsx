export default function GenerativeCanvas() {
  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Generative Canvas</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            <button className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500">
              Generative Experience
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="card">
          <div className="p-8 text-center max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">
              Transform your data into interactive pages
            </h2>

            <p className="text-lg text-gray-600 mb-4">
              Welcome to Generative Experience, a preview feature that uses AI to engage with the data
              that matters most to you. Use plain language to ask AI for a custom view of your
              information, complete with interactive tables, charts, and graphs. Prepare for sales
              meetings, analyze opportunities, and quickly surface key insights.
            </p>

            <p className="text-gray-600 mb-8">
              Upgrade to a paid Starter or Pro Suite subscription to use Generative Experience.
            </p>

            <button className="btn-primary text-lg px-8 py-3">
              Upgrade
            </button>
          </div>

          {/* Feature Preview */}
          <div className="bg-gray-100 p-8 mt-4">
            <div className="max-w-4xl mx-auto relative">
              {/* Play button overlay */}
              <div className="absolute inset-0 flex items-center justify-center z-10">
                <button className="w-20 h-20 bg-gray-700 bg-opacity-80 rounded-full flex items-center justify-center hover:bg-opacity-90 transition-all">
                  <svg className="w-10 h-10 text-white ml-1" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </button>
              </div>

              {/* Preview cards */}
              <div className="flex justify-center space-x-4">
                <div className="w-48 h-48 bg-cyan-400 rounded-lg shadow-lg transform -rotate-3"></div>
                <div className="w-48 h-48 bg-pink-400 rounded-lg shadow-lg transform rotate-2 -mt-4"></div>
              </div>
              <div className="flex justify-center space-x-4 -mt-8">
                <div className="w-48 h-32 bg-yellow-400 rounded-lg shadow-lg transform rotate-1"></div>
                <div className="w-64 h-20 bg-cyan-500 rounded-lg shadow-lg transform -rotate-1 mt-8"></div>
              </div>
            </div>
          </div>

          {/* Features List */}
          <div className="p-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">
              What you can do with Generative Experience
            </h3>
            <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Interactive Charts</h4>
                <p className="text-sm text-gray-500">Generate visual reports from your data instantly</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Natural Language</h4>
                <p className="text-sm text-gray-500">Ask questions in plain English to get insights</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">AI-Powered</h4>
                <p className="text-sm text-gray-500">Let AI analyze patterns and surface key insights</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
