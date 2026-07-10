"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

On startup, tables are created automatically (init_db). For production,
prefer Alembic migrations instead of relying on create_all.
"""

import logging

from fastapi import FastAPI, Depends
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db
from app.schemas import HealthResponse
from app.routers import emails, analysis, actions, dashboard, tasks, demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("email_automation")

app = FastAPI(
    title=settings.app_name,
    description=(
        "An AI system that reads business emails, classifies them, proposes "
        "workflow actions (Gmail drafts, calendar events, tasks), and only "
        "executes them after human approval. AI recommends. Human approves. "
        "System executes."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Starting %s (env=%s, demo_mode=%s)", settings.app_name, settings.env, settings.demo_mode)
    init_db()
    logger.info("Database initialized at %s", settings.database_url)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check(db: Session = Depends(get_db)):
    """Basic health/status endpoint."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        app_name=settings.app_name,
        env=settings.env,
        demo_mode=settings.demo_mode,
        database_connected=db_ok,
    )


@app.get("/", tags=["system"])
def root():
    return {
        "message": f"{settings.app_name} is running.",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(emails.router)
app.include_router(analysis.router)
app.include_router(actions.router)
app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(demo.router)
