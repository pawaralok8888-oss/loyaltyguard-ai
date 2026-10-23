"""
Synthetic mock portal data fixtures for LoyaltyGuard AI.
Providers:
- shop_rewards (unit: points)
- fly_miles (unit: points)
- gift_hub (unit: INR)
"""

DEFAULT_FIXTURES = {
    "shop_rewards": {
        "demo_shop_01": {
            "account_id": "demo_shop_01",
            "provider": "shop_rewards",
            "unit": "points",
            "total_balance": 1200.0,
            "batches": [
                {"batch_id": "batch_A", "amount_remaining": 300.0, "expires_at": "2026-10-25"},
                {"batch_id": "batch_B", "amount_remaining": 900.0, "expires_at": "2026-12-31"}
            ]
        },
        "tc1_account": {
            "account_id": "tc1_account",
            "provider": "shop_rewards",
            "unit": "points",
            "total_balance": 250.0,
            "batches": [
                {"batch_id": "tc1_batch", "amount_remaining": 250.0, "expires_at": "2026-10-28"}
            ]
        }
    },
    "fly_miles": {
        "demo_fly_01": {
            "account_id": "demo_fly_01",
            "provider": "fly_miles",
            "unit": "points",
            "total_balance": 5000.0,
            "batches": [
                {"batch_id": "fly_batch_1", "amount_remaining": 1500.0, "expires_at": "2026-10-27"},
                {"batch_id": "fly_batch_2", "amount_remaining": 3500.0, "expires_at": "2027-06-30"}
            ]
        }
    },
    "gift_hub": {
        "demo_gift_01": {
            "account_id": "demo_gift_01",
            "provider": "gift_hub",
            "unit": "INR",
            "total_balance": 750.0,
            "batches": [
                {"batch_id": "gift_batch_1", "amount_remaining": 750.0, "expires_at": "2026-10-24"}
            ]
        }
    }
}
