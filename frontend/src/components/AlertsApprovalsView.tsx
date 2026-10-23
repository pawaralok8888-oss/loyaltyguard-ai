import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AlertProposal } from '../types';
import { CheckCircle, XCircle, Send, AlertTriangle, Clock, RefreshCw } from 'lucide-react';

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
      setMessage({ text: `Alert #${id} rejected. It will never be dispatched.`, type: 'success' });
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
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">Pending Review</span>;
      case 'approved':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">Approved</span>;
      case 'sent':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">Sent (In-App)</span>;
      case 'rejected':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">Rejected</span>;
      case 'failed':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">Delivery Failed</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Alerts & Human Approval Gates</h2>
          <p className="text-sm text-gray-500">Auditable human review queue. No notifications send without operator approval.</p>
        </div>
        <button
          onClick={loadAlerts}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded text-sm ${
            message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex border-b border-gray-200 space-x-6 text-sm">
        {['all', 'pending', 'approved', 'sent', 'rejected', 'failed'].map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`pb-3 font-medium capitalize transition ${
              filter === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Proposals List */}
      {loading ? (
        <div className="p-12 text-center text-gray-500">Loading alerts queue...</div>
      ) : alerts.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-500">
          No alert proposals found for filter "{filter}".
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map(alt => (
            <div key={alt.id} className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-bold text-gray-900">Proposal #{alt.id}</span>
                    {getStatusBadge(alt.status)}
                    <span className="text-xs text-gray-400 font-mono">threshold: {alt.threshold_days} days</span>
                  </div>
                  <div className="mt-1 text-base font-semibold text-gray-900">
                    {alt.amount.toLocaleString()} {alt.unit} expiring on {alt.expiry_date}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2">
                  {alt.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(alt.id)}
                        disabled={actioningId === alt.id}
                        className="inline-flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-medium disabled:opacity-50 transition"
                      >
                        <CheckCircle className="w-3.5 h-3.5 mr-1" /> Approve
                      </button>
                      <button
                        onClick={() => handleReject(alt.id)}
                        disabled={actioningId === alt.id}
                        className="inline-flex items-center px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded text-xs font-medium disabled:opacity-50 transition"
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                      </button>
                    </>
                  )}

                  {(alt.status === 'approved' || alt.status === 'failed') && (
                    <button
                      onClick={() => handleSend(alt.id)}
                      disabled={actioningId === alt.id}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:opacity-50 transition"
                    >
                      <Send className="w-3.5 h-3.5 mr-1" /> {alt.status === 'failed' ? 'Retry Send' : 'Send Alert (In-App)'}
                    </button>
                  )}

                  {alt.status === 'sent' && (
                    <button
                      onClick={() => handleSend(alt.id)}
                      disabled={actioningId === alt.id}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-200 text-gray-600 hover:bg-gray-50 rounded text-xs font-medium transition"
                      title="Test idempotency: calling send again returns the existing event without re-sending"
                    >
                      Test Send (Idempotent)
                    </button>
                  )}
                </div>
              </div>

              {/* Dedupe Key & Auditable Timestamps */}
              <div className="bg-gray-50 rounded p-3 text-xs text-gray-600 space-y-1 font-mono">
                <div>
                  <span className="font-semibold text-gray-700">Dedupe Key:</span> {alt.dedupe_key}
                </div>
                <div className="flex space-x-6 text-gray-500">
                  <span>Created: {new Date(alt.created_at).toLocaleString()}</span>
                  {alt.approved_at && <span className="text-blue-600">Approved: {new Date(alt.approved_at).toLocaleString()}</span>}
                  {alt.sent_at && <span className="text-green-600">Sent: {new Date(alt.sent_at).toLocaleString()}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
