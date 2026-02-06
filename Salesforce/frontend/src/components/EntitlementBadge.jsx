export default function EntitlementBadge({ verified }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold text-green-700 bg-green-50">
        Verified
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold text-red-700 bg-red-50">
      Not Verified
    </span>
  );
}
