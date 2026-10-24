# LoyaltyGuard AI — Screenshot Checklist

Every screenshot needed for the portfolio submission.
Take each screenshot from the **live deployed URL** (`https://loyaltyguard-ai.onrender.com`).

---

## React UI Screenshots

### 1. Dashboard
- [ ] **SS-01**: Dashboard view with summary cards (total accounts, active alerts, last check, health status)
- [ ] **SS-02**: Dashboard after at least one check run has completed (non-zero values)

### 2. Accounts
- [ ] **SS-03**: Accounts list showing all 3 seeded accounts with status column
- [ ] **SS-04**: Account with `status: unchecked` (before any check)
- [ ] **SS-05**: Account with `status: verified` and `last_checked_at` populated (after check)
- [ ] **SS-06**: "Check Now" button visible on an account row

### 3. Alerts & Approvals
- [ ] **SS-07**: Alerts list with at least one `pending` proposal (showing amount, unit, expiry date, threshold)
- [ ] **SS-08**: Alert detail showing the Approve and Reject buttons
- [ ] **SS-09**: Alert after approval — status changed to `approved`, `approved_at` populated
- [ ] **SS-10**: Alert after rejection — status changed to `rejected`
- [ ] **SS-11**: Alert after successful send — status `sent`, `sent_at` populated

### 4. Points Calendar
- [ ] **SS-12**: Calendar view showing expiring batches with days-left indicators
- [ ] **SS-13**: Calendar with at least one batch in the "urgent" zone (≤3 days)

### 5. Agent Activity
- [ ] **SS-14**: Check run history list (outcome, verification status, timestamps)
- [ ] **SS-15**: Expanded agent trace for a **success** check run (6-step flow)
- [ ] **SS-16**: Expanded agent trace for a **failed** check run (2-step flow, LOGIN_FAILED)
- [ ] **SS-17**: Verification status labels visible: `verified`, `mismatch`, or `verification_failed`

### 6. Empty / Loading / Error States
- [ ] **SS-18**: Empty state when no alerts exist (before first check run)
- [ ] **SS-19**: Loading spinner or skeleton while data is being fetched

---

## API & Backend Screenshots

### 7. Swagger UI
- [ ] **SS-20**: Full Swagger `/docs` page showing all endpoint groups
- [ ] **SS-21**: Expanded `POST /api/checks/run` endpoint with X-Shared-Secret header
- [ ] **SS-22**: Expanded `POST /api/alerts/{id}/approve` endpoint

### 8. Health Endpoint
- [ ] **SS-23**: Browser showing `/health` JSON response with `status: healthy`

### 9. Pytest Output
- [ ] **SS-24**: Terminal showing full `pytest -v` output — **32 passed, 0 warnings**

---

## Deployment & DevOps Screenshots

### 10. Render Dashboard
- [ ] **SS-25**: Render web service overview (service name, status, last deploy)
- [ ] **SS-26**: Render environment variables tab (keys visible, values hidden)
- [ ] **SS-27**: Render build log showing successful build completion
- [ ] **SS-28**: Render deploy log showing seed output and uvicorn startup

### 11. GitHub Repository
- [ ] **SS-29**: GitHub repo main page showing file tree and README rendering
- [ ] **SS-30**: GitHub repo showing the Mermaid architecture diagram rendered

---

## n8n Workflow Screenshots

### 12. n8n Workflows (if n8n is set up)
- [ ] **SS-31**: Daily monitor workflow canvas (Schedule → HTTP Request → IF → Log)
- [ ] **SS-32**: Approved notifications workflow canvas (Poll → GET → IF → Split → Send)
- [ ] **SS-33**: n8n credential setup for LoyaltyGuard Shared Secret

---

## Evidence Screenshots

### 13. Agent Traces
- [ ] **SS-34**: Contents of `evidence/traces/tc1_trace.json` in an editor or terminal
- [ ] **SS-35**: Contents of `evidence/traces/tc3_trace.json` in an editor or terminal

---

## Smoke Test
- [ ] **SS-36**: Terminal showing `smoke_test.py` output with all checks passed

---

## Summary

| Category | Count |
|----------|-------|
| React UI | 19 screenshots (SS-01 to SS-19) |
| API & Backend | 4 screenshots (SS-20 to SS-23) |
| Pytest | 1 screenshot (SS-24) |
| Deployment | 4 screenshots (SS-25 to SS-28) |
| GitHub | 2 screenshots (SS-29 to SS-30) |
| n8n | 3 screenshots (SS-31 to SS-33) |
| Evidence | 2 screenshots (SS-34 to SS-35) |
| Smoke Test | 1 screenshot (SS-36) |
| **Total** | **36 screenshots** |

> **Tip**: Use Windows `Win+Shift+S` for region screenshots or full-screen `Print Screen`.
> Save with descriptive names like `SS-01_dashboard.png`, `SS-07_pending_alert.png`, etc.
