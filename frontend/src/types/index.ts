export interface LoyaltyAccount {
  id: number;
  user_id: number;
  provider_code: string;
  external_mock_id: string;
  display_name: string;
  status: 'verified' | 'unchecked';
  last_checked_at: string | null;
  last_error: string | null;
}

export interface CalendarItem {
  account_id: number;
  account_display_name: string;
  provider_code: string;
  batch_id: string;
  amount: number;
  unit: string;
  expiry_date: string;
  days_left: number;
  status: string;
  is_stale: boolean;
  source_reference: string;
}

export interface AlertProposal {
  id: number;
  user_id: number;
  loyalty_account_id: number;
  reward_batch_id: number | null;
  threshold_days: number;
  expiry_date: string;
  amount: number;
  unit: string;
  status: 'pending' | 'approved' | 'rejected' | 'sent' | 'failed';
  dedupe_key: string;
  created_at: string;
  approved_at: string | null;
  sent_at: string | null;
}

export interface CheckRun {
  id: number;
  loyalty_account_id: number;
  started_at: string;
  finished_at: string | null;
  outcome: string;
  error_code: string | null;
  verification_status: string | null;
  evidence_json: string | null;
}

export interface AgentTrace {
  id: number;
  check_run_id: number | null;
  tool_name: string;
  decision_type: string;
  explanation: string;
  input_redacted_json: string | null;
  output_redacted_json: string | null;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  clock_utc: string;
  clock_local: string;
  environment: string;
  planner_mode?: string;
  llm_provider?: string;
}
