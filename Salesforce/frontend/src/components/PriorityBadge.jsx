export default function PriorityBadge({ priority }) {
  const config = {
    Critical: { bg: 'bg-red-100', text: 'text-red-800', dot: 'bg-red-500' },
    High: { bg: 'bg-orange-100', text: 'text-orange-800', dot: 'bg-orange-500' },
    Medium: { bg: 'bg-yellow-100', text: 'text-yellow-800', dot: 'bg-yellow-500' },
    Normal: { bg: 'bg-blue-100', text: 'text-blue-800', dot: 'bg-blue-500' },
    Low: { bg: 'bg-green-100', text: 'text-green-800', dot: 'bg-green-500' },
  };

  const { bg, text, dot } = config[priority] || config.Normal;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
      <span className={`w-2 h-2 rounded-full ${dot}`}></span>
      {priority}
    </span>
  );
}
