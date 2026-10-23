import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { LoyaltyAccount, CalendarItem, AlertProposal } from '../types';
import { ShieldCheck, AlertTriangle, Clock, CheckCircle2, ArrowRight } from 'lucide-react';

interface Props {
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<Props> = ({ onNavigate }) => {
  const [accounts, setAccounts] = useState<LoyaltyAccount[]>([]);
  const [calendar, setCalendar] = useState<CalendarItem[]>([]);
  const [alerts, setAlerts] = useState<AlertProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [accs, cal, alts] = await Promise.all([
        api.getAccounts(),
        api.getCalendar(),
        api.getAlerts()
      ]);
      setAccounts(accs);
      setCalendar(cal);
      setAlerts(alts);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading LoyaltyGuard dashboard metrics...</div>;
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <p className="font-semibold">Error loading dashboard:</p>
        <p className="text-sm">{error}</p>
        <button onClick={loadData} className="mt-3 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700">
          Retry
        </button>
      </div>
    );
  }

  const expiringIn7Days = calendar.filter(c => c.days_left >= 0 && c.days_left <= 7);
  const uncheckedAccounts = accounts.filter(a => a.status === 'unchecked');
  const pendingApprovals = alerts.filter(a => a.status === 'pending');

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Tracked Programs</span>
            <ShieldCheck className="w-5 h-5 text-blue-600" />
          </div>
          <div className="mt-2 text-3xl font-bold text-gray-900">{accounts.length}</div>
          <p className="mt-1 text-xs text-gray-500">Active loyalty & voucher accounts</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Expiring in 7 Days</span>
            <Clock className="w-5 h-5 text-amber-500" />
          </div>
          <div className="mt-2 text-3xl font-bold text-amber-600">{expiringIn7Days.length}</div>
          <p className="mt-1 text-xs text-gray-500">Batches needing immediate user attention</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Unchecked Accounts</span>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div className="mt-2 text-3xl font-bold text-red-600">{uncheckedAccounts.length}</div>
          <p className="mt-1 text-xs text-gray-500">Portal auth errors or stale data</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Pending Approvals</span>
            <CheckCircle2 className="w-5 h-5 text-purple-600" />
          </div>
          <div className="mt-2 text-3xl font-bold text-purple-600">{pendingApprovals.length}</div>
          <p className="mt-1 text-xs text-gray-500">Human-in-the-loop alert gates</p>
        </div>
      </div>

      {/* Pending Approvals Callout */}
      {pendingApprovals.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-purple-900">
                Action Required: {pendingApprovals.length} Pending Alert Proposal{pendingApprovals.length > 1 ? 's' : ''}
              </h3>
              <p className="text-sm text-purple-700 mt-0.5">
                LoyaltyGuard AI requires explicit human approval before alerts can be dispatched.
              </p>
            </div>
            <button
              onClick={() => onNavigate('alerts')}
              className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm font-medium transition"
            >
              Review & Approve <ArrowRight className="w-4 h-4 ml-1.5" />
            </button>
          </div>
        </div>
      )}

      {/* 7-Day Expiring Summary Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-base font-semibold text-gray-900">Expiring in Next 7 Days (Strict Window)</h2>
          <button
            onClick={() => onNavigate('calendar')}
            className="text-xs text-blue-600 hover:underline font-medium"
          >
            View Full Calendar &rarr;
          </button>
        </div>
        {expiringIn7Days.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">
            No loyalty points or gift cards expiring within the next 7 days.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 text-xs uppercase font-semibold">
              <tr>
                <th className="px-5 py-3">Program</th>
                <th className="px-5 py-3">Batch ID</th>
                <th className="px-5 py-3">Expiring Amount</th>
                <th className="px-5 py-3">Expiry Date</th>
                <th className="px-5 py-3">Days Left</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {expiringIn7Days.map(item => (
                <tr key={`${item.account_id}-${item.batch_id}`} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-900">{item.account_display_name}</td>
                  <td className="px-5 py-3 text-gray-500 font-mono text-xs">{item.batch_id}</td>
                  <td className="px-5 py-3 font-semibold text-amber-700">
                    {item.amount.toLocaleString()} {item.unit}
                  </td>
                  <td className="px-5 py-3 text-gray-700">{item.expiry_date}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                      {item.days_left === 0 ? 'Today' : `${item.days_left}d left`}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    {item.is_stale ? (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">Stale</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Verified</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
