# LoyaltyGuard AI — n8n Integration

Two n8n workflows automate the daily monitoring and notification delivery loop.
**No credentials or secrets are stored in these files.**

---

## Workflows

| File | Purpose |
|------|---------|
| `daily_monitor.json` | Runs a full loyalty account check at 06:00 every day |
| `approved_notifications.json` | Polls every 5 min, sends approved-but-unsent alerts (idempotent) |

### Key design constraints
- **n8n never approves alerts** — approval is strictly human-only via the UI.
- The `/api/alerts/{id}/send` endpoint is idempotent: calling it multiple times for
  the same proposal ID only sends once; subsequent calls return `is_newly_sent: false`.
- The shared secret is stored **only** in an n8n credential — never in workflow JSON.

---

## Import steps

1. Open your n8n instance (self-hosted or n8n.cloud).
2. Go to **Workflows → Import from file**.
3. Import `daily_monitor.json`.
4. Import `approved_notifications.json`.

---

## Credential setup

### 1. LoyaltyGuard Shared Secret (for daily_monitor)

The daily monitor POSTs to `/api/checks/run` with `X-Shared-Secret`.

1. In n8n go to **Credentials → New → HTTP Header Auth**.
2. Name it exactly: **`LoyaltyGuard Shared Secret`**
3. Set:
   - **Name**: `X-Shared-Secret`
   - **Value**: *(the value you set for `N8N_SHARED_SECRET` in your deployment env vars)*
4. Save. The workflow references this credential by name.

### 2. Base URL variable

The workflows use `$vars.LOYALTYGUARD_BASE_URL` (an n8n Variable, not a credential).

1. Go to **Settings → Variables → New Variable**.
2. Name: `LOYALTYGUARD_BASE_URL`
3. Value: `https://your-render-or-railway-url.com` (no trailing slash)

---

## Activating

1. Open `daily_monitor` workflow → click **Active** toggle.
2. Open `approved_notifications` workflow → click **Active** toggle.
3. To test immediately: open the workflow and click **Execute workflow** manually.

---

## Failure alerting

The `daily_monitor` workflow has an **IF failure** branch that logs the error.
To receive an email or Slack notification:

1. Add a **Send Email** or **Slack** node after `Log failure`.
2. Connect your email/Slack credential (n8n has built-in nodes for both).
3. No code changes required in LoyaltyGuard itself.

---

## Security notes

- The `/api/checks/run` bulk endpoint is protected by `X-Shared-Secret` header.
- `/mock/admin/*` endpoints are disabled in production (`MOCK_ADMIN_ENABLED=false`).
- n8n's approved_notifications workflow **reads** proposals; it does **not** approve them.
  There is no n8n route to the approve endpoint — approval is exclusively via the React UI.
