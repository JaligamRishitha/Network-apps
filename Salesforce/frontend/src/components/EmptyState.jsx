export default function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon = 'contact',
}) {
  const illustrations = {
    contact: (
      <svg viewBox="0 0 200 150" className="w-48 h-36">
        <circle cx="100" cy="70" r="50" fill="#E8DAEF" />
        <rect x="70" y="50" width="60" height="40" rx="4" fill="white" stroke="#D7BDE2" />
        <circle cx="85" cy="65" r="8" fill="#D7BDE2" />
        <rect x="98" y="58" width="25" height="4" rx="2" fill="#D7BDE2" />
        <rect x="98" y="66" width="18" height="3" rx="1" fill="#E8DAEF" />
        <path d="M160 40 Q165 35, 170 38" stroke="#A569BD" strokeWidth="2" fill="none" />
      </svg>
    ),
    lead: (
      <svg viewBox="0 0 200 150" className="w-48 h-36">
        <circle cx="100" cy="70" r="50" fill="#D4E6F1" />
        <rect x="60" y="45" width="80" height="50" rx="4" fill="white" stroke="#85C1E9" />
        <rect x="70" y="55" width="15" height="30" rx="2" fill="#85C1E9" />
        <rect x="90" y="65" width="15" height="20" rx="2" fill="#AED6F1" />
        <rect x="110" y="50" width="15" height="35" rx="2" fill="#5DADE2" />
        <path d="M145 30 Q150 25, 155 28" stroke="#3498DB" strokeWidth="2" fill="none" />
      </svg>
    ),
    opportunity: (
      <svg viewBox="0 0 200 150" className="w-48 h-36">
        <circle cx="100" cy="70" r="50" fill="#FADBD8" />
        <rect x="60" y="45" width="80" height="50" rx="4" fill="white" stroke="#F5B7B1" />
        <rect x="70" y="55" width="60" height="8" rx="2" fill="#F5B7B1" />
        <rect x="70" y="68" width="45" height="6" rx="2" fill="#FADBD8" />
        <rect x="70" y="80" width="30" height="6" rx="2" fill="#FADBD8" />
        <circle cx="150" cy="35" r="8" fill="#E74C3C" opacity="0.3" />
      </svg>
    ),
    account: (
      <svg viewBox="0 0 200 150" className="w-48 h-36">
        <circle cx="100" cy="70" r="50" fill="#D5D8DC" />
        <rect x="70" y="50" width="60" height="40" rx="4" fill="white" stroke="#ABB2B9" />
        <rect x="85" y="45" width="30" height="8" rx="2" fill="#ABB2B9" />
        <rect x="78" y="60" width="20" height="15" fill="#D5D8DC" />
        <rect x="102" y="60" width="20" height="15" fill="#D5D8DC" />
        <rect x="78" y="78" width="44" height="4" rx="1" fill="#ABB2B9" />
        <path d="M155 55 Q160 50, 165 53" stroke="#7F8C8D" strokeWidth="2" fill="none" />
      </svg>
    ),
    case: (
      <svg viewBox="0 0 200 150" className="w-48 h-36">
        <circle cx="100" cy="70" r="50" fill="#FDEDEC" />
        <rect x="65" y="45" width="70" height="50" rx="4" fill="white" stroke="#F5B7B1" />
        <rect x="75" y="55" width="50" height="4" rx="2" fill="#F5B7B1" />
        <rect x="75" y="63" width="40" height="3" rx="1" fill="#FADBD8" />
        <rect x="75" y="70" width="35" height="3" rx="1" fill="#FADBD8" />
        <circle cx="145" cy="35" r="6" fill="#E91E63" />
        <path d="M142 35 L145 38 L150 32" stroke="white" strokeWidth="2" fill="none" />
      </svg>
    ),
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {illustrations[icon] || illustrations.contact}
      <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-gray-500 text-center max-w-sm">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 btn-primary"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
