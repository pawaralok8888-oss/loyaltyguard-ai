import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app.clock import Clock, KOLKATA_TZ
from backend.app.models import User, LoyaltyAccount
from backend.app.config import settings

from sqlalchemy.pool import StaticPool

# Enable mock admin endpoints for the test environment (must patch the singleton
# because pydantic-settings reads env at import time, before setdefault would apply)
settings.MOCK_ADMIN_ENABLED = "true"

# In-memory test SQLite DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh transactional database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def frozen_clock():
    """Sets clock to the official test freeze time: 2026-10-21T00:00:00+05:30."""
    freeze_time = datetime(2026, 10, 21, 0, 0, 0, tzinfo=KOLKATA_TZ)
    Clock.set_frozen(freeze_time)
    yield freeze_time
    Clock.reset()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Creates a default synthetic test user."""
    user = User(
        display_name="Test User",
        email="test_user@synthetic.local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_account(db_session, test_user):
    """Creates a default synthetic test loyalty account."""
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="Test Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account
