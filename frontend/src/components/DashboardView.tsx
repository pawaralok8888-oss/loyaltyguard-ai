import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { LoyaltyAccount, CalendarItem, AlertProposal } from '../types';
import { ShieldCheck, AlertTriangle, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { HeroWalletIllustration, ProgramBadge } from './Illustrations';

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
    return (
      <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm">Loading LoyaltyGuard metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 space-y-2 shadow-xs">
        <p className="font-semibold text-sm">Error loading dashboard:</p>
        <p className="text-xs">{error}</p>
        <button
          onClick={loadData}
          className="mt-2 px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const expiringIn7Days = calendar.filter(c => c.days_left >= 0 && c.days_left <= 7);
  const uncheckedFailedAccounts = accounts.filter(a => a.status === 'unchecked' && !!a.last_checked_at);
  const neverCheckedAccounts = accounts.filter(a => !a.last_checked_at);
  const pendingApprovals = alerts.filter(a => a.status === 'pending');

  return (
    <div className="space-y-6">
      {/* Dashboard Hero Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-indigo-950 text-white rounded-2xl p-6 sm:p-8 shadow-sm border border-indigo-700/40 relative overflow-hidden">
        {/* Subtle background glow circles */}
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none"></div>
        <div className="absolute -bottom-12 left-1/3 w-40 h-40 bg-teal-400/10 rounded-full blur-xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse"></span>
              <span>Synthetic data demo</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Never lose a point again
            </h2>
            <p className="text-sm text-indigo-100/90 leading-relaxed">
              Automated balance tracking and expiration sentinel for synthetic loyalty cards and voucher portals. Every alert proposal requires human verification before dispatch.
            </p>
          </div>

          <div className="flex-shrink-0 self-center sm:self-auto">
            <HeroWalletIllustration className="w-36 h-28 sm:w-44 sm:h-32 drop-shadow-md" />
          </div>
        </div>
      </div>

      {/* Metrics Row — Consistent calm fintech cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {/* 1. Tracked Programs */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-xs hover:shadow-sm transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Tracked Programs</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{accounts.length}</div>
          <p className="mt-1 text-xs text-slate-500">Active loyalty & voucher accounts</p>
        </div>

        {/* 2. Expiring in 7 Days */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-xs hover:shadow-sm transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Expiring in 7 Days</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-amber-600">{expiringIn7Days.length}</div>
          <p className="mt-1 text-xs text-slate-500">Batches needing immediate user attention</p>
        </div>

        {/* 3. Unchecked / Failed */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-xs hover:shadow-sm transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Unchecked / Failed</span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold tracking-tight text-rose-600">{uncheckedFailedAccounts.length}</span>
            {neverCheckedAccounts.length > 0 && (
              <span className="text-xs text-slate-500 font-normal">({neverCheckedAccounts.length} never checked)</span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">Failed or stale checks</p>
        </div>

        {/* 4. Pending Approvals */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200/80 shadow-xs hover:shadow-sm transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Pending Approvals</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-indigo-600">{pendingApprovals.length}</div>
          <p className="mt-1 text-xs text-slate-500">Human-in-the-loop alert gates</p>
        </div>
      </div>

      {/* Pending Approvals Callout Card */}
      {pendingApprovals.length > 0 && (
        <div className="bg-white border-l-4 border-l-indigo-600 border border-slate-200/80 rounded-xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></span>
              <h3 className="text-sm font-bold text-slate-900">
                Action Required: {pendingApprovals.length} Pending Alert Proposal{pendingApprovals.length > 1 ? 's' : ''}
              </h3>
            </div>
            <p className="text-xs text-slate-600">
              LoyaltyGuard AI requires explicit human operator sign-off before outgoing messages are simulated.
            </p>
          </div>
          <button
            onClick={() => onNavigate('alerts')}
            className="inline-flex items-center justify-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition shadow-xs whitespace-nowrap self-start sm:self-auto"
          >
            Review & Approve <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </button>
        </div>
      )}

      {/* 7-Day Expiring Summary Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Expiring in Next 7 Days (Critical Window)</h3>
            <p className="text-xs text-slate-500">Batches that will forfeit within the 7-day alert threshold</p>
          </div>
          <button
            onClick={() => onNavigate('calendar')}
            className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold inline-flex items-center space-x-1"
          >
            <span>View Full Calendar</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {expiringIn7Days.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No loyalty points or voucher cards expiring within the next 7 days.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[600px]">
              <thead className="bg-slate-50/80 border-b border-slate-200/60 text-slate-500 uppercase font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3">Program</th>
                  <th className="px-5 py-3">Batch ID</th>
                  <th className="px-5 py-3">Expiring Amount</th>
                  <th className="px-5 py-3">Expiry Date</th>
                  <th className="px-5 py-3">Days Left</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {expiringIn7Days.map(item => (
                  <tr key={`${item.account_id}-${item.batch_id}`} className="hover:bg-slate-50/60 transition">
                    <td className="px-5 py-3.5 font-medium text-slate-900">
                      <div className="flex items-center space-x-2.5">
                        <ProgramBadge providerCode={item.provider_code} displayName={item.account_display_name} size="sm" />
                        <span>{item.account_display_name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 font-mono text-[11px]">{item.batch_id}</td>
                    <td className="px-5 py-3.5 font-bold text-amber-700 text-sm">
                      {item.amount.toLocaleString()} {item.unit}
                    </td>
                    <td className="px-5 py-3.5 text-slate-700 font-mono">{item.expiry_date}</td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200/80">
                        {item.days_left === 0 ? 'Today' : `${item.days_left}d left`}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      {item.is_stale ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          Stale
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                          Verified
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
