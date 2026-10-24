# LoyaltyGuard AI — 3-Minute Demo Script

> **Prerequisites**: The app is deployed at `https://loyaltyguard-ai.onrender.com`.
> Render free tier may need ~30s to wake on first request.

---

## Minute 1: Dashboard & Accounts (0:00–1:00)

### 1.1 — Open the app

1. Navigate to **https://loyaltyguard-ai.onrender.com**
2. The **Dashboard** loads showing summary cards:
   - Total accounts (3 seeded)
   - Active alerts count
   - Last check run time
   - System health status

### 1.2 — View Accounts

1. Click the **Accounts** tab in the sidebar
2. Show the 3 seeded loyalty accounts:
   - **ShopRewards Club** (shop_rewards / points)
   - **FlyMiles SkyPass** (fly_miles / points)
   - **GiftHub INR Voucher Card** (gift_hub / INR)
3. Point out the `status` column — initially "unchecked" if no checks have run
4. Click **"Check Now"** on the ShopRewards account
5. Show the status update to "verified" and the `last_checked_at` timestamp

> **Talking point**: "Each account links to a synthetic mock portal. The agent fetches
> balance and batch data, validates it, and checks for expiring rewards."

---

## Minute 2: Alerts & Approval Flow (1:00–2:00)

### 2.1 — View the Alerts & Approvals screen

1. Click the **Alerts & Approvals** tab
2. Show any `pending` alert proposals created by the check run:
   - Expiring amount (e.g., "250 points")
   - Expiry date
   - Threshold (7 days)
   - Status: **pending**

### 2.2 — Approve an alert

1. Click **Approve** on a pending alert
2. Show the status change from `pending` → `approved`
3. Point out that `approved_at` is now populated

### 2.3 — Send notification (simulated)

1. With the alert now approved, use Swagger or the UI send button to trigger send
   - **Swagger**: POST `/api/alerts/{id}/send`
2. Show the response: `is_newly_sent: true`
3. Call send again to demonstrate **idempotency**: `is_newly_sent: false`

> **Talking point**: "The system never auto-approves. A human must click Approve.
> n8n polls for approved alerts and calls the idempotent send endpoint."

### 2.4 — Reject an alert (optional)

1. If there's a second pending alert, click **Reject**
2. Show status → `rejected`
3. Demonstrate that rejected alerts cannot be sent (400 error)

---

## Minute 3: Agent Activity & API Docs (2:00–3:00)

### 3.1 — View Agent Activity

1. Click the **Agent Activity** tab
2. Show the check run history with:
   - Outcome (success / failed)
   - Verification status (verified / mismatch / verification_failed)
   - Started and finished timestamps
3. Expand a check run to see the **agent trace** — step-by-step tool decisions:
   - `fetch_portal` → `validate_payload` → `compute_expiries` → `propose_alert` → `verify_recheck` → `explain`

> **Talking point**: "Every agent decision is traced and stored. The planner is
> deterministic by default. You can upgrade to an LLM planner with an API key."

### 3.2 — Show Points Calendar

1. Click the **Points Calendar** tab
2. Show the calendar view with expiring batches highlighted by urgency:
   - Days left, amount, unit, account name

### 3.3 — Show API Docs

1. Open **https://loyaltyguard-ai.onrender.com/docs** in a new tab
2. Briefly show the Swagger UI with all endpoints:
   - `/api/accounts`, `/api/checks/run`, `/api/alerts`, `/api/runs`, `/api/traces`
   - `/mock/providers/{provider}/accounts/{external_id}`

### 3.4 — Health check (wrap-up)

1. Open **https://loyaltyguard-ai.onrender.com/health**
2. Show `{"status": "healthy", "clock_utc": "...", "clock_local": "...", "environment": "production"}`

> **Closing**: "LoyaltyGuard AI is a fully deployed, tested (32/32 pytest), agentic
> system with human-in-the-loop approval, idempotent notifications, deterministic
> fallback planning, and full agent trace visibility. All data is synthetic."

---

## Quick API demo commands (if showing terminal)

```bash
# Health check
curl https://loyaltyguard-ai.onrender.com/health

# List accounts
curl https://loyaltyguard-ai.onrender.com/api/accounts

# Trigger bulk check (needs shared secret)
curl -X POST https://loyaltyguard-ai.onrender.com/api/checks/run \
  -H "X-Shared-Secret: YOUR_SECRET"

# List alerts
curl https://loyaltyguard-ai.onrender.com/api/alerts

# Approve alert
curl -X POST https://loyaltyguard-ai.onrender.com/api/alerts/1/approve

# Send notification (idempotent)
curl -X POST https://loyaltyguard-ai.onrender.com/api/alerts/1/send
```
