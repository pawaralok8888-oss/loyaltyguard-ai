# Evidence — Test Results & Agent Traces

This folder contains the evidence artifacts for the four official test cases (TC1–TC4),
the full pytest output, and exported agent traces.

---

## Files

| File | Description |
|------|-------------|
| `test_output.txt` | Full pytest output: **32 passed, 0 warnings** (Python 3.11.9) |
| `traces/tc1_trace.json` | Agent trace for TC1 (7-day expiry, success path, 6 steps) |
| `traces/tc3_trace.json` | Agent trace for TC3 (login failure, 2 steps, no retry) |

---

## TC1 — 7-Day Expiry Detection

| Field | Value |
|-------|-------|
| **Test function** | `test_tc1_seven_day_expiry` in `backend/tests/test_official_tc1_tc4.py` |
| **Input** | Account `tc1_account` on provider `shop_rewards`, 250 points expiring 2026-10-28 |
| **Frozen clock** | 2026-10-21T00:00:00+05:30 (Oct 28 − Oct 21 = 7 days → within window) |
| **Expected** | Exactly 1 `pending` alert proposal for 250 points, expiry date 2026-10-28, threshold_days=7. Status must be `pending` — NOT auto-sent. `sent_at` and `approved_at` must both be `None`. Account status must be `verified`. |
| **Actual** | ✅ All assertions pass |
| **Proof** | `test_output.txt` line `test_tc1_seven_day_expiry PASSED`; `traces/tc1_trace.json` shows 6-step agent flow: fetch → validate → compute_expiries → propose_alert → verify_recheck (status: verified) → explain |

### Agent trace summary (TC1)

| Step | Tool | Decision |
|------|------|----------|
| 1 | `fetch_portal` | Retrieve balance from mock portal |
| 2 | `validate_payload` | Pydantic schema + unit consistency check |
| 3 | `compute_expiries` | 1 batch within 7-day window |
| 4 | `propose_alert` | Deduplicated pending proposal created |
| 5 | `verify_recheck` | Post-run re-read → `verified` |
| 6 | `explain` | Final briefing: outcome=success, verification=verified |

---

## TC2 — Unchanged Balance / Deduplication

| Field | Value |
|-------|-------|
| **Test function** | `test_tc2_unchanged_balance_deduplication` in `backend/tests/test_official_tc1_tc4.py` |
| **Input** | Same `tc1_account` fixture as TC1 (250 points, 2026-10-28), run check **twice** on the same session |
| **Expected** | After the second check run, there must still be **exactly 1** alert proposal — NOT 2. The proposal ID must match the first run. Dedupe key uniqueness (DB UNIQUE constraint on `dedupe_key`) prevents duplication. |
| **Actual** | ✅ All assertions pass |
| **Proof** | `test_output.txt` line `test_tc2_unchanged_balance_deduplication PASSED` |

### Additional: Restart-surviving dedupe

| Field | Value |
|-------|-------|
| **Test function** | `test_tc2_dedupe_survives_real_process_restart` in `backend/tests/test_official_tc1_tc4.py` |
| **Input** | Same account, but uses a **file-backed SQLite DB**. First check creates proposal. Engine and session are **completely disposed**. A fresh engine and session are created (simulating a process restart). Second check runs. |
| **Expected** | Still exactly 1 proposal after the second run on the new engine/session. The `dedupe_key` value must be identical. |
| **Actual** | ✅ All assertions pass |
| **Proof** | `test_output.txt` line `test_tc2_dedupe_survives_real_process_restart PASSED` |

---

## TC3 — Login Failure (HTTP 401)

| Field | Value |
|-------|-------|
| **Test function** | `test_tc3_login_failure` in `backend/tests/test_official_tc1_tc4.py` |
| **Input** | Account `tc3_account` on provider `shop_rewards` with scenario override `login_fail` → mock portal returns HTTP 401. Account starts as `verified` with an existing balance snapshot. |
| **Expected** | Check run `outcome` must be `failed`, `error_code` must be `LOGIN_FAILED`. Account status must revert to `unchecked`. `last_error` must contain `LOGIN_FAILED`. The existing balance snapshot must be marked `is_stale=True`. No new snapshot must be created. No retry is attempted for 401 (spec rule). |
| **Actual** | ✅ All assertions pass |
| **Proof** | `test_output.txt` line `test_tc3_login_failure PASSED`; `traces/tc3_trace.json` shows 2-step agent flow: fetch → mark_unchecked (LOGIN_FAILED, no retry) |

### Agent trace summary (TC3)

| Step | Tool | Decision |
|------|------|----------|
| 1 | `fetch_portal` | Portal returns HTTP 401 Unauthorized |
| 2 | `mark_unchecked` | No retry for 401. Account marked unchecked, error recorded |

---

## TC4 — Partial Expiry

| Field | Value |
|-------|-------|
| **Test function** | `test_tc4_partial_expiry` in `backend/tests/test_official_tc1_tc4.py` |
| **Input** | Account `demo_shop_01` with fixture data: batch_A = 300 points expiring 2026-10-25, batch_B = 900 points expiring 2026-12-31. Total balance = 1200. |
| **Frozen clock** | 2026-10-21 (Oct 25 − Oct 21 = 4 days → within window; Dec 31 − Oct 21 = 71 days → outside window) |
| **Expected** | Both batches stored in `reward_batches` (300 + 900). Exactly 1 alert proposal for the **expiring** 300 points on 2026-10-25 (NOT 1200). Proposal status = `pending`. Total balance snapshot retains the full 1200. |
| **Actual** | ✅ All assertions pass |
| **Proof** | `test_output.txt` line `test_tc4_partial_expiry PASSED` |

---

## How to reproduce

```powershell
cd "path\to\loyaltyguard-ai"
.\backend\venv\Scripts\python.exe -m pytest backend\tests\ -v
```

All 32 tests should produce:
```
============================= 32 passed in 14.22s =============================
```

---

## How traces are generated

The `backend/scripts/export_tc_traces.py` script queries the `agent_traces` table after a test-mode check run and exports the step-by-step agent decision trace as JSON. Each trace entry includes:

- `step`: Sequential step number
- `tool_name`: Which agent tool was invoked
- `decision_type`: `policy=fallback` (deterministic) or `policy=llm`
- `explanation`: Human-readable rationale for the decision
- `input`/`output`: Redacted input/output payloads
- `timestamp`: When the step executed
