export default function SLACountdown({ deadline }) {
  if (!deadline) return <span className="text-gray-400">-</span>;

  const diff = new Date(deadline) - new Date();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);

  if (diff < 0) {
    return <span className="text-red-600 font-bold text-sm">Breached!</span>;
  }

  if (days > 0) {
    return <span className="text-gray-700 text-sm font-medium">{days}d {hours}h</span>;
  }

  return <span className="text-orange-600 font-bold text-sm">{hours}h remaining</span>;
}