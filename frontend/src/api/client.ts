import { LoyaltyAccount, CalendarItem, AlertProposal, CheckRun, AgentTrace } from '../types';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const data = await res.json();
      errorDetail = data.detail || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Accounts
  getAccounts: () => fetchJson<LoyaltyAccount[]>('/api/accounts'),
  createAccount: (data: { user_id: number; provider_code: string; external_mock_id: string; display_name: string }) =>
    fetchJson<LoyaltyAccount>('/api/accounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),
  checkAccount: (accountId: number) =>
    fetchJson<CheckRun>(`/api/accounts/${accountId}/check`, { method: 'POST' }),

  // Calendar & Expiries
  getCalendar: () => fetchJson<CalendarItem[]>('/api/calendar'),
  getExpiries: (days: number = 7) => fetchJson<any[]>(`/api/expiries?days=${days}`),

  // Alerts & Approvals
  getAlerts: (status?: string) =>
    fetchJson<AlertProposal[]>(status ? `/api/alerts?status=${status}` : '/api/alerts'),
  approveAlert: (id: number) => fetchJson<AlertProposal>(`/api/alerts/${id}/approve`, { method: 'POST' }),
  rejectAlert: (id: number) => fetchJson<AlertProposal>(`/api/alerts/${id}/reject`, { method: 'POST' }),
  sendAlert: (id: number) =>
    fetchJson<{ status: string; is_newly_sent: boolean; proposal: AlertProposal; notification_event: any }>(
      `/api/alerts/${id}/send`,
      { method: 'POST' }
    ),

  // Runs & Traces
  getRuns: () => fetchJson<CheckRun[]>('/api/runs'),
  getTraces: (checkRunId?: number) =>
    fetchJson<AgentTrace[]>(checkRunId ? `/api/traces?check_run_id=${checkRunId}` : '/api/traces'),

  // Health
  getHealth: () => fetchJson<{ status: string; clock_utc: string; clock_local: string }>('/health')
};
