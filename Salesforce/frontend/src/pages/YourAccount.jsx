export default function YourAccount() {
  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Your Account</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            <button className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500">
              Your Account
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="card p-12 text-center max-w-2xl mx-auto">
          {/* Illustration */}
          <div className="mb-8">
            <svg viewBox="0 0 200 150" className="w-48 h-36 mx-auto">
              {/* Background shapes */}
              <path d="M40 100 L80 60 L120 80 L160 40 L180 60 L180 130 L20 130 Z" fill="#E3F2FD" />

              {/* Compass/navigation icon */}
              <circle cx="100" cy="70" r="35" fill="white" stroke="#90CAF9" strokeWidth="2" />
              <circle cx="100" cy="70" r="25" fill="#E3F2FD" />
              <path d="M100 50 L105 70 L100 90 L95 70 Z" fill="#1976D2" />
              <circle cx="100" cy="70" r="5" fill="#1976D2" />

              {/* Clouds */}
              <ellipse cx="50" cy="45" rx="15" ry="8" fill="#E3F2FD" />
              <ellipse cx="60" cy="42" rx="12" ry="7" fill="#E3F2FD" />
              <ellipse cx="150" cy="50" rx="18" ry="9" fill="#E3F2FD" />
              <ellipse cx="162" cy="47" rx="14" ry="8" fill="#E3F2FD" />

              {/* Mountains */}
              <path d="M0 130 L40 90 L70 110 L100 75 L130 105 L160 80 L200 130 Z" fill="#BBDEFB" opacity="0.5" />
            </svg>
          </div>

          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            You haven't subscribed yet
          </h2>

          <p className="text-gray-600 mb-8">
            When you subscribe, you can manage your plan, licenses<br />
            and billing information right here.
          </p>

          <button className="btn-primary text-lg px-8 py-3">
            Buy Now
          </button>

          {/* Additional Info */}
          <div className="mt-12 pt-8 border-t">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Current Plan Details</h3>
            <div className="text-left max-w-md mx-auto space-y-3">
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">Plan Type</span>
                <span className="font-medium">Starter Trial</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">Days Remaining</span>
                <span className="font-medium">29 days</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">Users</span>
                <span className="font-medium">1 of 1</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-500">Data Storage</span>
                <span className="font-medium">1 GB</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
