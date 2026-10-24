import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CalendarItem } from '../types';
import { RefreshCw, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { ProgramBadge, EmptyBatchesIllustration } from './Illustrations';

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
    return (
      <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm">Loading Points Calendar...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">Points & Gift Cards Expiry Calendar</h2>
          <p className="text-xs text-slate-500 mt-0.5">Chronological schedule of reward batches with days remaining.</p>
        </div>
        <button
          onClick={loadCalendar}
          className="inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-xs transition self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-slate-500" /> Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs shadow-xs">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        {items.length === 0 ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
            <EmptyBatchesIllustration className="w-20 h-20" />
            <div className="text-sm font-semibold text-slate-700">No active reward batches recorded</div>
            <p className="text-xs text-slate-500 max-w-sm">
              Run a check on your tracked accounts to query external portals and retrieve expiring point batches.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[750px]">
              <thead className="bg-slate-50/80 border-b border-slate-200/60 text-slate-500 uppercase font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3.5">Program</th>
                  <th className="px-5 py-3.5">Batch ID</th>
                  <th className="px-5 py-3.5">Batch Amount & Unit</th>
                  <th className="px-5 py-3.5">Expiry Date</th>
                  <th className="px-5 py-3.5">Days Left</th>
                  <th className="px-5 py-3.5">Account Status</th>
                  <th className="px-5 py-3.5">Data Freshness</th>
                  <th className="px-5 py-3.5">Source Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map(item => {
                  const isUrgent = item.days_left >= 0 && item.days_left <= 7;
                  const isExpired = item.days_left < 0;

                  return (
                    <tr key={`${item.account_id}-${item.batch_id}`} className="hover:bg-slate-50/60 transition">
                      <td className="px-5 py-3.5 font-medium text-slate-900">
                        <div className="flex items-center space-x-2.5">
                          <ProgramBadge providerCode={item.provider_code} displayName={item.account_display_name} size="sm" />
                          <span>{item.account_display_name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-[11px] text-slate-600">{item.batch_id}</td>
                      <td className="px-5 py-3.5 font-bold text-slate-900 text-sm">
                        {item.amount.toLocaleString()} <span className="font-medium text-xs text-slate-600">{item.unit}</span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-700 font-mono">{item.expiry_date}</td>
                      <td className="px-5 py-3.5">
                        {isExpired ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                            Expired
                          </span>
                        ) : isUrgent ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                            <Clock className="w-3 h-3 mr-1" />
                            {item.days_left === 0 ? 'Expiring Today' : `${item.days_left}d remaining`}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                            {item.days_left}d remaining
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        {item.status === 'verified' ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                            <CheckCircle className="w-3 h-3 mr-1" /> Verified
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <AlertTriangle className="w-3 h-3 mr-1" /> Unchecked
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        {item.is_stale ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <AlertTriangle className="w-3 h-3 mr-1" /> Stale Data
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                            <CheckCircle className="w-3 h-3 mr-1" /> Fresh Snapshot
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 font-mono text-[11px] text-slate-500 max-w-xs truncate" title={item.source_reference}>
                        {item.source_reference ? (
                          <span>{item.source_reference.split('?')[0]}</span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
