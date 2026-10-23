"""
Seed script to populate initial synthetic user and loyalty accounts for LoyaltyGuard AI.
Usage:
    python -m backend.scripts.seed_demo
"""
from backend.app.db import SessionLocal, engine, Base
from backend.app.models import User, LoyaltyAccount

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if user already exists
        user = db.query(User).filter(User.email == "demo@synthetic.loyaltyguard.local").first()
        if not user:
            user = User(
                display_name="Demo Traveler",
                email="demo@synthetic.loyaltyguard.local"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[Seed] Created synthetic user: {user.display_name} (ID: {user.id})")
        else:
            print(f"[Seed] Existing synthetic user found: {user.display_name} (ID: {user.id})")

        # Seed initial synthetic accounts if not present
        accounts_data = [
            {
                "provider_code": "shop_rewards",
                "external_mock_id": "demo_shop_01",
                "display_name": "ShopRewards Club"
            },
            {
                "provider_code": "fly_miles",
                "external_mock_id": "demo_fly_01",
                "display_name": "FlyMiles SkyPass"
            },
            {
                "provider_code": "gift_hub",
                "external_mock_id": "demo_gift_01",
                "display_name": "GiftHub INR Voucher Card"
            }
        ]

        for acc in accounts_data:
            existing = db.query(LoyaltyAccount).filter(
                LoyaltyAccount.user_id == user.id,
                LoyaltyAccount.provider_code == acc["provider_code"],
                LoyaltyAccount.external_mock_id == acc["external_mock_id"]
            ).first()

            if not existing:
                account = LoyaltyAccount(
                    user_id=user.id,
                    provider_code=acc["provider_code"],
                    external_mock_id=acc["external_mock_id"],
                    display_name=acc["display_name"],
                    status="unchecked"
                )
                db.add(account)
                print(f"[Seed] Added account: {acc['display_name']} ({acc['provider_code']})")

        db.commit()
        print("[Seed] Seeding completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
