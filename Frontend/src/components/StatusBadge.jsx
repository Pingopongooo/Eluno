export default function StatusBadge({ status }) {
  const colors = {
    "Order Placed": "bg-emerald-100 text-emerald-800",
    "Lens Procurement": "bg-blue-100 text-blue-800",
    "Coating": "bg-amber-100 text-amber-800",
    "Edging & Fitting": "bg-purple-100 text-purple-800",
    "QC Failed": "bg-red-100 text-red-800",
    "Ready for Pickup": "bg-teal-100 text-teal-800",
    "Delivered": "bg-gray-100 text-gray-800"
  };

  const colorClass = colors[status] || "bg-gray-100 text-gray-800";

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {status}
    </span>
  );
}