export default function RiskBadge({ score }) {
  if (!score) return <span className="text-xs text-gray-400 font-medium italic">Pending AI...</span>;

  const colors = {
    "Low": "bg-green-100 text-green-700",
    "Medium": "bg-yellow-100 text-yellow-700",
    "High": "bg-red-100 text-red-700 font-bold"
  };

  const colorClass = colors[score] || "bg-gray-100 text-gray-800";

  return (
    <span className={`px-2 py-1 rounded text-xs ${colorClass}`}>
      {score} Risk
    </span>
  );
}