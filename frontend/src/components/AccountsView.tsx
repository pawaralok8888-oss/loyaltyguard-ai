import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { LoyaltyAccount } from '../types';
import { RefreshCw, Plus, CheckCircle, AlertTriangle, ExternalLink } from 'lucide-react';

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
    return <div className="p-8 text-center text-gray-500">Loading accounts...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header and Add Button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Loyalty & Gift Card Accounts</h2>
          <p className="text-sm text-gray-500">Manage tracked synthetic loyalty programs and partner portals.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition"
        >
          <Plus className="w-4 h-4 mr-1.5" /> Add Synthetic Account
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      {/* Accounts Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {accounts.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No loyalty accounts found. Click "Add Synthetic Account" to create one.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 text-xs uppercase font-semibold">
              <tr>
                <th className="px-5 py-3">Program / Display Name</th>
                <th className="px-5 py-3">Provider</th>
                <th className="px-5 py-3">Mock ID</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Last Checked</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {accounts.map(acc => (
                <tr key={acc.id} className="hover:bg-gray-50">
                  <td className="px-5 py-4">
                    <div className="font-semibold text-gray-900">{acc.display_name}</div>
                    {acc.last_error && (
                      <div className="text-xs text-red-600 mt-0.5 flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1 flex-shrink-0" />
                        {acc.last_error}
                      </div>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <span className="font-mono text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {acc.provider_code}
                    </span>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-gray-600">{acc.external_mock_id}</td>
                  <td className="px-5 py-4">
                    {acc.status === 'verified' ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle className="w-3.5 h-3.5 mr-1" /> Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Unchecked
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-xs text-gray-500">
                    {acc.last_checked_at ? new Date(acc.last_checked_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      onClick={() => handleCheckNow(acc.id)}
                      disabled={checkingId === acc.id}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${checkingId === acc.id ? 'animate-spin' : ''}`} />
                      {checkingId === acc.id ? 'Checking...' : 'Check now'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Synthetic Loyalty Account</h3>
            <form onSubmit={handleCreateAccount} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Provider Code</label>
                <select
                  value={providerCode}
                  onChange={e => setProviderCode(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="shop_rewards">shop_rewards (Points)</option>
                  <option value="fly_miles">fly_miles (Points)</option>
                  <option value="gift_hub">gift_hub (INR Currency)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. My Shopping Club Card"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  required
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">External Mock ID</label>
                <input
                  type="text"
                  placeholder="e.g. demo_shop_01 or new_account_id"
                  value={externalId}
                  onChange={e => setExternalId(e.target.value)}
                  required
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Pre-configured fixture IDs: demo_shop_01, tc1_account, demo_fly_01, demo_gift_01.</p>
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium disabled:opacity-50"
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
