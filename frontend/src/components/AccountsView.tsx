import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { LoyaltyAccount } from '../types';
import { RefreshCw, Plus, CheckCircle, AlertTriangle, ExternalLink, HelpCircle } from 'lucide-react';
import { ProgramBadge, EmptyAccountsIllustration } from './Illustrations';

interface Props {
  onCheckCompleted?: () => void;
}

export const AccountsView: React.FC<Props> = ({ onCheckCompleted }) => {
  const [accounts, setAccounts] = useState<LoyaltyAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingId, setCheckingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // New account form state
  const [providerCode, setProviderCode] = useState('shop_rewards');
  const [externalId, setExternalId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [creating, setCreating] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAccounts();
      setAccounts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckNow = async (accountId: number) => {
    try {
      setCheckingId(accountId);
      await api.checkAccount(accountId);
      await loadAccounts();
      if (onCheckCompleted) onCheckCompleted();
    } catch (err: any) {
      alert(`Check failed: ${err.message}`);
    } finally {
      setCheckingId(null);
    }
  };

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName || !externalId) return;

    try {
      setCreating(true);
      await api.createAccount({
        user_id: 1, // Default synthetic demo user
        provider_code: providerCode,
        external_mock_id: externalId,
        display_name: displayName
      });
      setDisplayName('');
      setExternalId('');
      setShowAddModal(false);
      await loadAccounts();
    } catch (err: any) {
      alert(`Failed to add account: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm">Loading synthetic loyalty accounts...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">Loyalty & Gift Card Accounts</h2>
          <p className="text-xs text-slate-500 mt-0.5">Manage tracked synthetic loyalty programs and partner portals.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition duration-150 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 mr-1.5" /> Add Synthetic Account
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs shadow-xs">
          {error}
        </div>
      )}

      {/* Accounts Table Card */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        {accounts.length === 0 ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
            <EmptyAccountsIllustration className="w-20 h-20" />
            <div className="text-sm font-semibold text-slate-700">No accounts tracked yet</div>
            <p className="text-xs text-slate-500 max-w-sm">
              Click "Add Synthetic Account" above to link a loyalty card, frequent flyer program, or gift card.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[700px]">
              <thead className="bg-slate-50/80 border-b border-slate-200/60 text-slate-500 uppercase font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3.5">Program / Display Name</th>
                  <th className="px-5 py-3.5">Provider</th>
                  <th className="px-5 py-3.5">Mock ID</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Last Checked</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {accounts.map(acc => (
                  <tr key={acc.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-3">
                        <ProgramBadge providerCode={acc.provider_code} displayName={acc.display_name} />
                        <div>
                          <div className="font-semibold text-slate-900 text-sm">{acc.display_name}</div>
                          {acc.last_error && (
                            <div className="text-[11px] text-rose-600 mt-0.5 flex items-center">
                              <AlertTriangle className="w-3 h-3 mr-1 flex-shrink-0" />
                              <span className="truncate max-w-xs">{acc.last_error}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-[11px] bg-slate-100 text-slate-700 px-2 py-1 rounded-md border border-slate-200/60">
                        {acc.provider_code}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono text-[11px] text-slate-600">{acc.external_mock_id}</td>
                    <td className="px-5 py-4">
                      {acc.status === 'verified' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                          <CheckCircle className="w-3.5 h-3.5 mr-1" /> Verified
                        </span>
                      ) : !acc.last_checked_at ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-50 text-slate-600 border border-slate-200">
                          <HelpCircle className="w-3.5 h-3.5 mr-1" /> Never checked
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Unchecked/failed
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-500 font-mono">
                      {acc.last_checked_at ? new Date(acc.last_checked_at).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => handleCheckNow(acc.id)}
                        disabled={checkingId === acc.id}
                        className="inline-flex items-center px-3 py-1.5 border border-slate-200 shadow-xs text-xs font-semibold rounded-lg text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 mr-1.5 text-slate-500 ${checkingId === acc.id ? 'animate-spin text-indigo-600' : ''}`} />
                        {checkingId === acc.id ? 'Checking...' : 'Check now'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in duration-150">
            <h3 className="text-base font-bold text-slate-900 mb-1">Add Synthetic Loyalty Account</h3>
            <p className="text-xs text-slate-500 mb-4">Connect a mock external program to test balance checks and alert logic.</p>
            <form onSubmit={handleCreateAccount} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Provider Code</label>
                <select
                  value={providerCode}
                  onChange={e => setProviderCode(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="shop_rewards">shop_rewards (Points)</option>
                  <option value="fly_miles">fly_miles (Points)</option>
                  <option value="gift_hub">gift_hub (INR Currency)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. My Premium Shopping Club"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  required
                  className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">External Mock ID</label>
                <input
                  type="text"
                  placeholder="e.g. tc1_account, tc3_account, tc4_account"
                  value={externalId}
                  onChange={e => setExternalId(e.target.value)}
                  required
                  className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <p className="text-[11px] text-slate-500 mt-1">Pre-configured fixtures: tc1_account, tc3_account, tc4_account, demo_gift_01.</p>
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs disabled:opacity-50 transition"
                >
                  {creating ? 'Adding...' : 'Save Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
