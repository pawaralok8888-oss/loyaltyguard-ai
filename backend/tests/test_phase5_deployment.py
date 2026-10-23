"""
Phase 5 deployment-readiness tests.

Tests:
- P5-01: mock admin blocked when MOCK_ADMIN_ENABLED=false
- P5-02: mock admin allowed when MOCK_ADMIN_ENABLED=true (already tested implicitly; explicit here)
- P5-03: /api/checks/run rejected without shared secret (401)
- P5-04: /api/checks/run rejected with wrong secret (401)
- P5-05: /health returns all required fields
- P5-06: seed is idempotent (calling seed() twice yields same account count)
- P5-07: PORTAL_BASE_URL is configurable via settings
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.main import app


# ── P5-01: Mock admin blocked when flag is false ───────────────────────────────
def test_mock_admin_blocked_when_flag_false(client):
    """Mock admin endpoints must return 403 when MOCK_ADMIN_ENABLED=false."""
    original = settings.MOCK_ADMIN_ENABLED
    try:
        settings.MOCK_ADMIN_ENABLED = "false"
        r = client.post(
            "/mock/admin/scenario",
            json={"provider": "shop_rewards", "external_id": "x", "scenario": "success"},
            headers={"X-Shared-Secret": settings.N8N_SHARED_SECRET}
        )
        assert r.status_code == 403, (
            f"Expected 403 when MOCK_ADMIN_ENABLED=false, got {r.status_code}: {r.text}"
        )
        assert "disabled" in r.json()["detail"].lower()
    finally:
        settings.MOCK_ADMIN_ENABLED = original


# ── P5-02: Mock admin allowed when flag is true (and secret correct) ───────────
def test_mock_admin_allowed_when_flag_true(client):
    """Mock admin endpoints must return 200 when MOCK_ADMIN_ENABLED=true + correct secret."""
    original = settings.MOCK_ADMIN_ENABLED
    try:
        settings.MOCK_ADMIN_ENABLED = "true"
        r = client.post(
            "/mock/admin/scenario",
            json={"provider": "shop_rewards", "external_id": "p5_test", "scenario": "success"},
            headers={"X-Shared-Secret": settings.N8N_SHARED_SECRET}
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json()["status"] == "ok"
    finally:
        settings.MOCK_ADMIN_ENABLED = original


# ── P5-03: Mock admin with flag=true but wrong secret → 403 ───────────────────
def test_mock_admin_wrong_secret(client):
    """Even with flag=true, wrong secret must return 403."""
    original = settings.MOCK_ADMIN_ENABLED
    try:
        settings.MOCK_ADMIN_ENABLED = "true"
        r = client.post(
            "/mock/admin/scenario",
            json={"provider": "shop_rewards", "external_id": "x", "scenario": "success"},
            headers={"X-Shared-Secret": "totally_wrong_secret"}
        )
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    finally:
        settings.MOCK_ADMIN_ENABLED = original


# ── P5-04: Bulk check without secret → 401 ────────────────────────────────────
def test_bulk_check_requires_secret(client):
    """POST /api/checks/run without header must return 401."""
    r = client.post("/api/checks/run")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


# ── P5-05: Bulk check with wrong secret → 401 ─────────────────────────────────
def test_bulk_check_wrong_secret(client):
    """POST /api/checks/run with wrong secret must return 401."""
    r = client.post("/api/checks/run", headers={"X-Shared-Secret": "not_the_secret"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


# ── P5-06: Health check returns all required fields ───────────────────────────
def test_health_check_fields(client):
    """GET /health must return status, clock_utc, clock_local, environment."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "clock_utc" in body
    assert "clock_local" in body
    assert "environment" in body


# ── P5-07: Seed is idempotent ─────────────────────────────────────────────────
def test_seed_is_idempotent(db_session):
    """Calling seed() twice must not create duplicate accounts or raise errors."""
    from backend.app.models import User, LoyaltyAccount
    from backend.app.db import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # Use a fresh in-memory DB for this test
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # Patch get_db to use our engine, then run seed twice
    import backend.scripts.seed_demo as seed_module
    original_session = seed_module.SessionLocal
    original_engine = seed_module.engine

    try:
        seed_module.SessionLocal = Session
        seed_module.engine = engine
        seed_module.seed()
        seed_module.seed()  # second call — must be idempotent

        session = Session()
        users = session.query(User).all()
        accounts = session.query(LoyaltyAccount).all()
        session.close()

        assert len(users) == 1, f"Expected 1 user after 2 seeds, got {len(users)}"
        assert len(accounts) == 3, f"Expected 3 accounts after 2 seeds, got {len(accounts)}"
    finally:
        seed_module.SessionLocal = original_session
        seed_module.engine = original_engine


# ── P5-08: PORTAL_BASE_URL is configurable ────────────────────────────────────
def test_portal_base_url_configurable():
    """settings.PORTAL_BASE_URL must be present and overridable."""
    assert hasattr(settings, "PORTAL_BASE_URL"), "PORTAL_BASE_URL missing from settings"
    assert isinstance(settings.PORTAL_BASE_URL, str)
    assert settings.PORTAL_BASE_URL.startswith("http"), (
        f"PORTAL_BASE_URL should be an http URL, got: {settings.PORTAL_BASE_URL}"
    )
