import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.config import settings
from backend.app.db import engine, Base
from backend.app.clock import Clock
from backend.app.mock_portal.router import router as mock_router
from backend.app.routers.accounts import router as accounts_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.checks import router as checks_router
from backend.app.routers.expiries import router as expiries_router
from backend.app.routers.runs import router as runs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: create DB tables then run the idempotent seed so demo data is
    always present on first boot (local dev and Render/Railway cold-start).
    """
    Base.metadata.create_all(bind=engine)
    try:
        from backend.scripts.seed_demo import seed
        seed()
    except Exception as exc:  # Never crash the server if seed fails
        print(f"[startup] Seed warning (non-fatal): {exc}")

    # Mount built React SPA if frontend/dist exists (single-service deployment)
    dist_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    )
    if os.path.exists(dist_path):
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="static_frontend")
        print(f"[startup] Serving React SPA from {dist_path}")
    else:
        print("[startup] frontend/dist not found — run 'npm run build' to enable SPA serving")

    yield  # Application runs here


app = FastAPI(
    title="LoyaltyGuard AI",
    description="Agentic loyalty points & gift card expiry tracker with human-in-the-loop approval",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup for frontend (Vite dev proxy, or same-origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(mock_router)
app.include_router(accounts_router)
app.include_router(alerts_router)
app.include_router(checks_router)
app.include_router(expiries_router)
app.include_router(runs_router)


@app.get("/health", tags=["health"])
def health_check():
    planner_mode = (
        f"Planner: {settings.LLM_PROVIDER} (LLM on)"
        if (settings.LLM_API_KEY and settings.LLM_PROVIDER != "fallback")
        else "Planner: rule-based (LLM off)"
    )
    return {
        "status": "healthy",
        "clock_utc": Clock.now_utc().isoformat(),
        "clock_local": Clock.now_local().isoformat(),
        "environment": settings.ENVIRONMENT,
        "planner_mode": planner_mode,
        "llm_provider": settings.LLM_PROVIDER
    }

