#!/usr/bin/env python3
"""
LoyaltyGuard AI — Deployment smoke test.

Usage:
    # Against local dev server:
    python smoke_test.py --base-url http://127.0.0.1:8000 --secret YOUR_SECRET

    # Against deployed Render/Railway instance:
    python smoke_test.py --base-url https://your-app.onrender.com --secret YOUR_SECRET

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.
"""
import argparse
import sys
import json
import urllib.request
import urllib.error


def request(method: str, url: str, *, headers: dict = None, body: bytes = None):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else {}
    except Exception as exc:
        return 0, {"error": str(exc)}


def check(label: str, condition: bool, detail: str = ""):
    symbol = "✓" if condition else "✗"
    print(f"  {symbol}  {label}" + (f": {detail}" if detail else ""))
    return condition


def main():
    parser = argparse.ArgumentParser(description="LoyaltyGuard smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Deployed app base URL")
    parser.add_argument("--secret", required=True, help="N8N_SHARED_SECRET value")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    secret = args.secret
    passed = []

    print(f"\n🔍  LoyaltyGuard smoke test → {base}\n")

    # ── 1. Health check ───────────────────────────────────────────────────────
    print("1. Health check")
    status, body = request("GET", f"{base}/health")
    passed.append(check("GET /health returns 200", status == 200, f"got {status}"))
    passed.append(check("status=healthy in response", body.get("status") == "healthy", str(body.get("status"))))
    passed.append(check("clock_utc present", "clock_utc" in body))

    # ── 2. List accounts (seed should have populated these) ────────────────────
    print("\n2. Accounts (seed check)")
    status, body = request("GET", f"{base}/api/accounts")
    passed.append(check("GET /api/accounts returns 200", status == 200, f"got {status}"))
    account_count = len(body) if isinstance(body, list) else 0
    passed.append(check("At least 1 seeded account exists", account_count >= 1, f"found {account_count}"))

    account_id = body[0]["id"] if account_count > 0 else None

    # ── 3. Trigger bulk check run ──────────────────────────────────────────────
    print("\n3. Bulk check run (requires shared secret)")
    status, body = request(
        "POST",
        f"{base}/api/checks/run",
        headers={"X-Shared-Secret": secret, "Content-Type": "application/json"}
    )
    passed.append(check("POST /api/checks/run returns 200", status == 200, f"got {status}"))
    run_count = len(body) if isinstance(body, list) else 0
    passed.append(check("At least 1 check run returned", run_count >= 1, f"got {run_count}"))

    # ── 4. Reject bulk check without secret ────────────────────────────────────
    print("\n4. Bulk check without secret (must be refused)")
    status, _ = request("POST", f"{base}/api/checks/run")
    passed.append(check("POST /api/checks/run without secret returns 401", status == 401, f"got {status}"))

    # ── 5. List alerts ─────────────────────────────────────────────────────────
    print("\n5. Alert proposals")
    status, body = request("GET", f"{base}/api/alerts")
    passed.append(check("GET /api/alerts returns 200", status == 200, f"got {status}"))

    # ── 6. Mock admin blocked without flag ─────────────────────────────────────
    print("\n6. Mock admin surface (must be blocked in production)")
    status, _ = request(
        "POST",
        f"{base}/mock/admin/scenario",
        headers={"X-Shared-Secret": secret, "Content-Type": "application/json"},
        body=json.dumps({"provider": "shop_rewards", "external_id": "smoke_test", "scenario": "success"}).encode()
    )
    # In production MOCK_ADMIN_ENABLED=false → 403
    # In local dev with MOCK_ADMIN_ENABLED=true → 200 (acceptable)
    if status == 403:
        passed.append(check("Mock admin blocked (403) — production safe", True))
    elif status == 200:
        passed.append(check("Mock admin open (200) — ensure MOCK_ADMIN_ENABLED=false in production", True,
                            "⚠ WARNING: set MOCK_ADMIN_ENABLED=false for production"))
    else:
        passed.append(check("Mock admin returns expected status", False, f"unexpected {status}"))

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(passed)
    ok = sum(passed)
    print(f"\n{'='*50}")
    print(f"  Result: {ok}/{total} checks passed")
    if ok == total:
        print("  ✅  All smoke tests PASSED\n")
        sys.exit(0)
    else:
        print("  ❌  Some smoke tests FAILED — review output above\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
