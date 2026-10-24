# LoyaltyGuard AI — Deployment Guide

> **Status**: App is NOT yet deployed. Follow these steps exactly; report the URL when done.

---

## ✅ Pytest: 32/32 passed (Python 3.11.9, 0 warnings)

---

## Pre-deployment checklist

- [ ] `frontend/dist/` exists — run `npm run build` inside `frontend/` if not
- [ ] `.env.example` reviewed; real `.env` never committed
- [ ] `N8N_SHARED_SECRET` chosen (long random string, e.g. `openssl rand -hex 32`)
- [ ] Python 3.11 available on your local machine (confirmed: 3.11.9)

---

## Part A — Render (Primary)

### 1. Push to GitHub

```bash
# From loyaltyguard-ai/ root
git init            # if not already a repo
git add .
git commit -m "LoyaltyGuard AI — ready for deployment"
# Create a new GitHub repo, then:
git remote add origin https://github.com/YOUR_USER/loyaltyguard-ai.git
git push -u origin main
```

### 2. Create a Render Web Service

1. Go to [https://render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Render detects `render.yaml` automatically → click **Apply** to use it

Or set these manually if not using `render.yaml`:

| Setting | Value |
|---------|-------|
| **Environment** | Python |
| **Python version** | `3.11` |
| **Build command** | `pip install -r backend/requirements.txt && cd frontend && npm ci && npm run build` |
| **Start command** | `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Root directory** | *(leave blank — repo root)* |

### 3. Set Environment Variables in Render Dashboard

Go to **Environment → Environment Variables** and add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:///./loyaltyguard.db` (or Render Postgres URL) |
| `ENVIRONMENT` | `production` |
| `HOST` | `0.0.0.0` |
| `N8N_SHARED_SECRET` | *(your long random secret — keep secret)* |
| `PORTAL_BASE_URL` | `https://YOUR_APP_NAME.onrender.com` *(set after first deploy)* |
| `MOCK_ADMIN_ENABLED` | `false` |
| `LLM_PROVIDER` | `fallback` |

> ⚠️ `LLM_API_KEY` — leave blank unless you have a key and want LLM planning.

### 4. Add a Persistent Disk (SQLite persistence)

In Render → **Disks → Add Disk**:
- Mount path: `/opt/render/project/src`
- Size: 1 GB

> Skip if using PostgreSQL `DATABASE_URL` instead.

### 5. Deploy

Click **Manual Deploy → Deploy latest commit**. Watch the build log.

First boot will print:
```
[Seed] Created synthetic user: Demo Traveler (ID: 1)
[Seed] Added account: ShopRewards Club (shop_rewards)
[Seed] Added account: FlyMiles SkyPass (fly_miles)
[Seed] Added account: GiftHub INR Voucher Card (gift_hub)
```

### 6. Post-deploy: run smoke test

```bash
python smoke_test.py \
  --base-url https://YOUR_APP_NAME.onrender.com \
  --secret YOUR_N8N_SHARED_SECRET
```

Expected: `✅  All smoke tests PASSED`

---

## Part B — Railway (Backup)

### 1. Install Railway CLI (optional but convenient)

```bash
npm install -g @railway/cli
railway login
```

### 2. Create project

```bash
cd loyaltyguard-ai
railway init          # creates project
railway up            # deploys from current directory
```

Or via dashboard: [https://railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**

Railway detects `railway.toml` automatically.

### 3. Set Environment Variables

In Railway dashboard → **Variables** tab, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Railway provides this automatically if you add a Postgres plugin |
| `ENVIRONMENT` | `production` |
| `N8N_SHARED_SECRET` | *(your long random secret)* |
| `PORTAL_BASE_URL` | `https://YOUR_APP.up.railway.app` |
| `MOCK_ADMIN_ENABLED` | `false` |
| `LLM_PROVIDER` | `fallback` |

### 4. Add Postgres (optional, recommended for Railway)

In Railway → **New → Database → PostgreSQL** → copy the `DATABASE_URL` variable to your service.

### 5. Smoke test

```bash
python smoke_test.py \
  --base-url https://YOUR_APP.up.railway.app \
  --secret YOUR_N8N_SHARED_SECRET
```

---

## Part C — n8n Workflows (after deployment)

See `n8n/README.md` for full import and credential steps.

Quick summary:
1. Import `n8n/daily_monitor.json` and `n8n/approved_notifications.json`
2. Create an **HTTP Header Auth** credential named `LoyaltyGuard Shared Secret`
   with `X-Shared-Secret` = your `N8N_SHARED_SECRET` value
3. Create an n8n **Variable** `LOYALTYGUARD_BASE_URL` = your deployed URL
4. Activate both workflows

---

## Part D — Local smoke test (before deploying)

```bash
# Terminal 1 — start backend
cd "c:\Users\Admin\Downloads\Data P\loyaltyguard-ai\backend"
.\venv\Scripts\Activate.ps1
cd ..
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — smoke test local
python smoke_test.py --base-url http://127.0.0.1:8000 --secret YOUR_N8N_SHARED_SECRET
```

> Note: in local dev `MOCK_ADMIN_ENABLED` defaults to `true` (set in conftest),
> so the smoke test will report "Mock admin open (200) — ensure MOCK_ADMIN_ENABLED=false for production".
> That is expected locally.

---

## Summary of new files created in Phase 5

| File | Purpose |
|------|---------|
| `render.yaml` | Render auto-deploy config (Python 3.11 pinned) |
| `railway.toml` | Railway Nixpacks config (Python 3.11 + Node 20) |
| `.env.example` | All env vars documented (no real values) |
| `smoke_test.py` | Zero-dependency deployment smoke test |
| `n8n/daily_monitor.json` | Daily check run workflow |
| `n8n/approved_notifications.json` | Approved alert sender workflow |
| `n8n/README.md` | n8n import + credential steps |
| `backend/tests/test_phase5_deployment.py` | 8 deployment-readiness tests |
