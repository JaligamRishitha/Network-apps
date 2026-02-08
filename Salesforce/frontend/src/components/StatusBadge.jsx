export default function StatusBadge({ status }) {
  const config = {
    SUCCESS: { bg: 'bg-green-100', text: 'text-green-800', icon: '', label: 'Success' },
    COMPLETED: { bg: 'bg-green-100', text: 'text-green-800', icon: '', label: 'Completed' },
    VALIDATED: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '', label: 'Validated' },
    APPROVED: { bg: 'bg-green-100', text: 'text-green-800', icon: '', label: 'Approved' },
    DUPLICATE_DETECTED: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '', label: 'Duplicate' },
    PENDING: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '', label: 'Pending' },
    PARTS_UNAVAILABLE: { bg: 'bg-orange-100', text: 'text-orange-800', icon: '', label: 'Parts Unavailable' },
    TECHNICIAN_UNAVAILABLE: { bg: 'bg-orange-100', text: 'text-orange-800', icon: '', label: 'Tech Unavailable' },
    ENTITLEMENT_FAILED: { bg: 'bg-red-100', text: 'text-red-800', icon: '', label: 'Entitlement Failed' },
    REJECTED: { bg: 'bg-red-100', text: 'text-red-800', icon: '', label: 'Rejected' },
    FAILED: { bg: 'bg-red-100', text: 'text-red-800', icon: '', label: 'Failed' },
    ERROR: { bg: 'bg-red-100', text: 'text-red-800', icon: '', label: 'Error' },
    DISPATCHED: { bg: 'bg-indigo-100', text: 'text-indigo-800', icon: '', label: 'Dispatched' },
    IN_PROGRESS: { bg: 'bg-purple-100', text: 'text-purple-800', icon: '', label: 'In Progress' },
    SCHEDULED: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '', label: 'Scheduled' },
  };

  const { bg, text, icon, label } = config[status?.toUpperCase()] || config.PENDING;

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
      {icon} {label}
    </span>
  );
}
