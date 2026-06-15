import { useState, useEffect } from 'react';
import { fetchOrders, updateOrderStatus, markQCFailed, deleteOrder } from '../services/api';
import { Trash2, X } from 'lucide-react';
import StatusBadge from './StatusBadge';
import RiskBadge from './RiskBadge';
import SLACountdown from './SLACountdown';

// -------------------------------------------------------------------
// STATE MACHINE: Defines allowed next statuses for each current status
// -------------------------------------------------------------------
const STATUS_TRANSITIONS = {
  "Order Placed":      ["Coating"],
  "Lens Procurement":  ["Coating"],
  "Coating":           ["Edging & Fitting", "QC Failed"],
  "Edging & Fitting":  ["Ready for Pickup", "QC Failed"],
  "QC Failed":         ["Coating"],
  "Ready for Pickup":  ["Delivered"],
  "Delivered":         []
};

// -------------------------------------------------------------------
// MODAL COMPONENT: Appears when staff selects a new status
// Collects optional reason before confirming the status change
// -------------------------------------------------------------------
function StatusUpdateModal({ order, newStatus, onConfirm, onCancel }) {
  const [reason, setReason] = useState('');
  const isQCFail = newStatus === "QC Failed";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Confirm Status Update</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Order info */}
        <div className="bg-gray-50 rounded-md p-3 mb-4">
          <p className="text-sm text-gray-600">
            <span className="font-medium">Order #{order.id}</span> — {order.customer_name}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Moving from <span className="font-medium text-gray-700">{order.status}</span> → <span className={`font-medium ${isQCFail ? 'text-red-600' : 'text-blue-600'}`}>{newStatus}</span>
          </p>
        </div>

        {/* Reason input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {isQCFail
              ? "QC Failure Reason *"
              : `Notes on the ${order.status} stage (optional)`}
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder={
              isQCFail
                ? "Describe the QC failure e.g. air bubble on left lens coating..."
                : "Leave blank if no delays or issues at this stage..."
            }
            rows={3}
            className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
          {isQCFail && !reason.trim() && (
            <p className="text-xs text-red-500 mt-1">Please describe the QC failure before confirming.</p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onCancel}
            className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(reason)}
            disabled={isQCFail && !reason.trim()}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium text-white transition-colors
              ${isQCFail
                ? 'bg-red-600 hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            Confirm Update
          </button>
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------------
// SUMMARY CARDS: Shows aggregate stats at the top of the dashboard
// -------------------------------------------------------------------
function SummaryCards({ orders }) {
  const total = orders.length;
  const highRisk = orders.filter(o => o.breach_risk_score === 'High').length;
  const breached = orders.filter(o => new Date(o.sla_deadline) < new Date()).length;

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <p className="text-sm text-gray-500">Active Orders</p>
        <p className="text-2xl font-bold text-gray-900">{total}</p>
      </div>
      <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
        <p className="text-sm text-gray-500">High Risk</p>
        <p className="text-2xl font-bold text-orange-600">{highRisk}</p>
      </div>
      <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
        <p className="text-sm text-gray-500">SLA Breached</p>
        <p className="text-2xl font-bold text-red-600">{breached}</p>
      </div>
    </div>
  );
}

// -------------------------------------------------------------------
// MAIN DASHBOARD COMPONENT
// -------------------------------------------------------------------
export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [filterStatus, setFilterStatus] = useState('');
  const [filterLensType, setFilterLensType] = useState('');
  const [filterLocation, setFilterLocation] = useState('');

  // Modal state
  const [pendingChange, setPendingChange] = useState(null); 
  // pendingChange = { order, newStatus } when modal is open, null when closed

  const loadOrders = async () => {
    try {
      const data = await fetchOrders();
      setOrders(data);
    } catch (error) {
      console.error("Failed to load orders", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
    const interval = setInterval(loadOrders, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // When staff selects a new status from the dropdown, open the modal
  const handleStatusSelect = (order, newStatus) => {
    if (newStatus === order.status) return; // No change, do nothing
    setPendingChange({ order, newStatus });
  };

  // When staff confirms the modal (with or without a reason)
  const handleConfirm = async (reason) => {
    if (!pendingChange) return;
    const { order, newStatus } = pendingChange;

    try {
      const payload = {
        status: newStatus,
        reason: reason || '',
        changed_by: "Store Staff"
      };

      if (newStatus === "QC Failed") {
        // Use the dedicated QC fail endpoint which triggers AI background task
        await markQCFailed(order.id, payload);
      } else {
        await updateOrderStatus(order.id, payload);
      }

      setPendingChange(null);
      loadOrders();
    } catch (error) {
      alert("Failed to update status. Please try again.");
      console.error(error);
    }
  };

  const handleDelete = async (orderId) => {
    if (window.confirm(`Cancel Order #${orderId}? This cannot be undone.`)) {
      try {
        await deleteOrder(orderId);
        loadOrders();
      } catch (error) {
        alert("Failed to delete order.");
        console.error(error);
      }
    }
  };

  // -------------------------------------------------------------------
  // FILTERING LOGIC
  // -------------------------------------------------------------------
  const uniqueStatuses = [...new Set(orders.map(o => o.status))].sort();
  const uniqueLensTypes = [...new Set(orders.map(o => o.lens_type_name))].sort();
  const uniqueLocations = [...new Set(orders.map(o => o.store_location))].sort();

  const filteredOrders = orders.filter(order => {
    const matchStatus   = !filterStatus   || order.status === filterStatus;
    const matchLens     = !filterLensType || order.lens_type_name === filterLensType;
    const matchLocation = !filterLocation || order.store_location === filterLocation;
    return matchStatus && matchLens && matchLocation;
  });

  if (loading) return <div className="p-8 text-center text-gray-500">Loading Orders...</div>;

  return (
    <div>
      {/* Summary cards */}
      <SummaryCards orders={orders} />

      <div className="bg-white rounded-lg shadow overflow-hidden">
        
        {/* Header + Filters */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h3 className="text-lg font-medium text-gray-900">
              Active Orders
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({filteredOrders.length} of {orders.length})
              </span>
            </h3>

            {/* Filter dropdowns */}
            <div className="flex flex-wrap gap-3">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                {uniqueStatuses.map(s => <option key={s} value={s}>{s}</option>)}
              </select>

              <select
                value={filterLensType}
                onChange={(e) => setFilterLensType(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Lens Types</option>
                {uniqueLensTypes.map(l => <option key={l} value={l}>{l}</option>)}
              </select>

              <select
                value={filterLocation}
                onChange={(e) => setFilterLocation(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Locations</option>
                {uniqueLocations.map(l => <option key={l} value={l}>{l}</option>)}
              </select>

              {/* Clear filters button — only shows if any filter is active */}
              {(filterStatus || filterLensType || filterLocation) && (
                <button
                  onClick={() => { setFilterStatus(''); setFilterLensType(''); setFilterLocation(''); }}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="overflow-x-auto">
          {filteredOrders.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {orders.length === 0 ? "No active orders." : "No orders match the selected filters."}
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lens Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SLA Remaining</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Predicted Delivery</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Risk</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredOrders.map((order) => {
                  const allowedNext = STATUS_TRANSITIONS[order.status] || [];

                  return (
                    <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-4 text-sm font-medium text-gray-900">#{order.id}</td>
                      
                      <td className="px-4 py-4 text-sm text-gray-900">{order.customer_name}</td>
                      
                      <td className="px-4 py-4 text-sm text-gray-500">{order.lens_type_name}</td>
                      
                      <td className="px-4 py-4 text-sm text-gray-500">{order.store_location}</td>

                      {/* SLA Remaining — always against the original hard SLA deadline */}
                      <td className="px-4 py-4">
                        <SLACountdown deadline={order.sla_deadline} />
                      </td>

                      {/* Predicted Delivery — AI updated, may differ from SLA if failures occurred */}
                      <td className="px-4 py-4">
                        <SLACountdown deadline={order.predicted_delivery_date || order.sla_deadline} />
                      </td>

                      <td className="px-4 py-4">
                        <StatusBadge status={order.status} />
                      </td>

                      <td className="px-4 py-4">
                        <div>
                          <RiskBadge score={order.breach_risk_score} />
                          {order.breach_risk_reason && (
                            <p className="text-xs text-gray-400 mt-1 max-w-xs truncate" title={order.breach_risk_reason}>
                              {order.breach_risk_reason}
                            </p>
                          )}
                        </div>
                      </td>

                      {/* Action column */}
                      <td className="px-4 py-4">
                        <div className="flex items-center space-x-2">
                          {allowedNext.length > 0 ? (
                            <select
                              value=""
                              onChange={(e) => {
                                if (e.target.value) handleStatusSelect(order, e.target.value);
                              }}
                              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-blue-500 focus:border-blue-500 bg-white"
                            >
                              <option value="">Move to...</option>
                              {allowedNext.map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                            </select>
                          ) : (
                            <span className="text-xs text-gray-400 italic">No actions</span>
                          )}

                          {order.status !== "Ready for Pickup" && order.status !== "Delivered" && (
                            <button
                              onClick={() => handleDelete(order.id)}
                              className="text-red-400 hover:text-red-600 transition-colors"
                              title="Cancel & Delete Order"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal — renders on top of everything when pendingChange is set */}
      {pendingChange && (
        <StatusUpdateModal
          order={pendingChange.order}
          newStatus={pendingChange.newStatus}
          onConfirm={handleConfirm}
          onCancel={() => setPendingChange(null)}
        />
      )}
    </div>
  );
}
