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
                "provider_code": "gift_hub",
                "external_mock_id": "demo_gift_01",
                "display_name": "GiftHub INR Voucher Card"
            },
            {
                "provider_code": "shop_rewards",
                "external_mock_id": "tc3_account",
                "display_name": "TC3 Login-Fail Demo"
            },
            {
                "provider_code": "shop_rewards",
                "external_mock_id": "tc4_account",
                "display_name": "TC4 Partial-Expiry Demo"
            }
        ]

        # Fix any legacy display name typo in database
        legacy_github = db.query(LoyaltyAccount).filter(
            LoyaltyAccount.display_name == "GitHub INR Voucher Card"
        ).all()
        for leg in legacy_github:
            leg.display_name = "GiftHub INR Voucher Card"

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
            else:
                if existing.display_name != acc["display_name"]:
                    existing.display_name = acc["display_name"]

        db.commit()
        print("[Seed] Seeding completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
