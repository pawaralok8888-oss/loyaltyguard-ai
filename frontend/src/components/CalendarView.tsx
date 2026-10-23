import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CalendarItem } from '../types';
import { Calendar, AlertCircle, ExternalLink, RefreshCw } from 'lucide-react';

export const CalendarView: React.FC = () => {
  const [items, setItems] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCalendar();
  }, []);

  const loadCalendar = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCalendar();
      setItems(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load points calendar');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading Points Calendar...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Points & Gift Cards Expiry Calendar</h2>
          <p className="text-sm text-gray-500">Chronological schedule of reward batches with days remaining.</p>
        </div>
        <button
          onClick={loadCalendar}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {items.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No active reward batches recorded yet. Run a check on your accounts to retrieve batches.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 text-xs uppercase font-semibold">
              <tr>
                <th className="px-5 py-3">Program</th>
                <th className="px-5 py-3">Batch ID</th>
                <th className="px-5 py-3">Batch Amount & Unit</th>
                <th className="px-5 py-3">Expiry Date</th>
                <th className="px-5 py-3">Days Left</th>
                <th className="px-5 py-3">Account Status</th>
                <th className="px-5 py-3">Data Freshness</th>
                <th className="px-5 py-3">Source Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map(item => {
                const isUrgent = item.days_left >= 0 && item.days_left <= 7;
                const isExpired = item.days_left < 0;

                return (
                  <tr key={`${item.account_id}-${item.batch_id}`} className="hover:bg-gray-50">
                    <td className="px-5 py-3.5 font-medium text-gray-900">
                      {item.account_display_name}
                      <span className="ml-1.5 text-xs text-gray-400 font-mono">({item.provider_code})</span>
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-gray-600">{item.batch_id}</td>
                    <td className="px-5 py-3.5 font-semibold text-gray-900">
                      {item.amount.toLocaleString()} {item.unit}
                    </td>
                    <td className="px-5 py-3.5 text-gray-700">{item.expiry_date}</td>
                    <td className="px-5 py-3.5">
                      {isExpired ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          Expired
                        </span>
                      ) : isUrgent ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                          {item.days_left === 0 ? 'Expiring Today' : `${item.days_left}d remaining`}
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                          {item.days_left}d remaining
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      {item.status === 'verified' ? (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                          Verified
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                          Unchecked
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      {item.is_stale ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                          <AlertCircle className="w-3 h-3 mr-1" /> Stale Data
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                          Fresh Snapshot
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-gray-500 max-w-xs truncate" title={item.source_reference}>
                      {item.source_reference ? (
                        <span className="inline-flex items-center">
                          {item.source_reference.split('?')[0]}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
