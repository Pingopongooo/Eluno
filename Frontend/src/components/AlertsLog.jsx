import { useState, useEffect } from 'react';
import { BellRing, MailWarning } from 'lucide-react';
import { fetchAlerts } from '../services/api';

export default function AlertsLog() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts()
      .then(setAlerts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading Alerts...</div>;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center">
          <BellRing className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">AI Alerts History</h3>
        </div>
        <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {alerts.length} Total Alerts
        </span>
      </div>
      
      {alerts.length === 0 ? (
        <div className="p-8 text-center text-gray-500">No high-risk alerts have been generated yet.</div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {alerts.map((alert) => (
            <li key={alert.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <MailWarning className="h-6 w-6 text-orange-500" />
                </div>
                <div className="ml-4 w-full">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900 border-b pb-1">
                      Order #{alert.order_id} - {alert.alert_type.replace(/_/g, ' ')}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(alert.sent_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-100 whitespace-pre-wrap">
                    {alert.message}
                  </div>
                  <p className="mt-2 text-xs text-gray-400">
                    Sent to: {alert.email_sent_to}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}