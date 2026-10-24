import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AlertProposal } from '../types';
import { CheckCircle, XCircle, Send, AlertTriangle, Clock, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { EmptyAlertsIllustration } from './Illustrations';

export const AlertsApprovalsView: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertProposal[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const data = await api.getAlerts(filter === 'all' ? undefined : filter);
      setAlerts(data);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load alerts', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      setActioningId(id);
      await api.approveAlert(id);
      setMessage({ text: `Alert #${id} approved successfully. Ready to dispatch.`, type: 'success' });
      await loadAlerts();
    } catch (err: any) {
      setMessage({ text: `Approval failed: ${err.message}`, type: 'error' });
    } finally {
      setActioningId(null);
    }
  };

  const handleReject = async (id: number) => {
    try {
      setActioningId(id);
      await api.rejectAlert(id);
      setMessage({ text: `Alert #${id} rejected. It will not be dispatched.`, type: 'success' });
      await loadAlerts();
    } catch (err: any) {
      setMessage({ text: `Rejection failed: ${err.message}`, type: 'error' });
    } finally {
      setActioningId(null);
    }
  };

  const handleSend = async (id: number) => {
    try {
      setActioningId(id);
      const res = await api.sendAlert(id);
      if (res.is_newly_sent) {
        setMessage({ text: `Alert #${id} dispatched to in-app simulated channel!`, type: 'success' });
      } else {
        setMessage({ text: `Alert #${id} was already sent previously. Idempotent check succeeded.`, type: 'success' });
      }
      await loadAlerts();
    } catch (err: any) {
      setMessage({ text: `Send failed: ${err.message}`, type: 'error' });
    } finally {
      setActioningId(null);
    }
  };

  const getStatusBadge = (status: AlertProposal['status']) => {
    switch (status) {
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            <Clock className="w-3.5 h-3.5 mr-1" /> Pending Review
          </span>
        );
      case 'approved':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approved
          </span>
        );
      case 'sent':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
            <CheckCircle className="w-3.5 h-3.5 mr-1" /> Dispatched
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <XCircle className="w-3.5 h-3.5 mr-1" /> Rejected
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3.5 h-3.5 mr-1" /> Delivery Failed
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">Alerts & Human Approval Gates</h2>
          <p className="text-xs text-slate-500 mt-0.5">Auditable human review queue. No notifications dispatch without operator sign-off.</p>
        </div>
        <button
          onClick={loadAlerts}
          className="inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-xs transition self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-slate-500" /> Refresh Queue
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-medium shadow-xs ${
            message.type === 'success'
              ? 'bg-teal-50 border border-teal-200 text-teal-800'
              : 'bg-rose-50 border border-rose-200 text-rose-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-200/80 space-x-2 sm:space-x-6 text-xs sm:text-sm overflow-x-auto no-scrollbar">
        {['all', 'pending', 'approved', 'sent', 'rejected', 'failed'].map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`pb-3 font-semibold capitalize transition-colors duration-150 whitespace-nowrap ${
              filter === tab
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Proposals List */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm">Loading alerts queue...</span>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200/80 p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3 shadow-xs">
          <EmptyAlertsIllustration className="w-20 h-20" />
          <div className="text-sm font-semibold text-slate-700">No alert proposals found</div>
          <p className="text-xs text-slate-500 max-w-sm">
            There are currently no proposals matching filter "{filter}". Check your accounts to evaluate upcoming expirations.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map(alt => (
            <div
              key={alt.id}
              className="bg-white rounded-xl border border-slate-200/80 p-5 sm:p-6 shadow-xs hover:shadow-sm transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Proposal #{alt.id}</span>
                    {getStatusBadge(alt.status)}
                    <span className="text-[11px] text-slate-400 font-mono bg-slate-50 px-2 py-0.5 rounded border border-slate-200/60">
                      threshold: {alt.threshold_days}d
                    </span>
                  </div>

                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-bold tracking-tight text-slate-900">
                      {alt.amount.toLocaleString()}
                    </span>
                    <span className="text-sm font-semibold text-slate-600">{alt.unit}</span>
                    <span className="text-xs text-slate-400">forfeiting on</span>
                    <span className="text-xs font-mono font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      {alt.expiry_date}
                    </span>
                  </div>

                  <p className="text-xs text-slate-500">
                    Target: Loyalty Account #{alt.loyalty_account_id} • Created: {new Date(alt.created_at).toLocaleString()}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2 self-start sm:self-auto">
                  {alt.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(alt.id)}
                        disabled={actioningId === alt.id}
                        className="inline-flex items-center px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition"
                      >
                        <CheckCircle className="w-3.5 h-3.5 mr-1.5" /> Approve
                      </button>
                      <button
                        onClick={() => handleReject(alt.id)}
                        disabled={actioningId === alt.id}
                        className="inline-flex items-center px-3.5 py-2 bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition"
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1.5" /> Reject
                      </button>
                    </>
                  )}

                  {(alt.status === 'approved' || alt.status === 'failed') && (
                    <button
                      onClick={() => handleSend(alt.id)}
                      disabled={actioningId === alt.id}
                      className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition"
                    >
                      <Send className="w-3.5 h-3.5 mr-1.5" /> {alt.status === 'failed' ? 'Retry Send' : 'Send Alert (In-App)'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
