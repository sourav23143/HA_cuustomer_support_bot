"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import get_settings
from app.api.chat import router as chat_router
from app.api.tickets import router as tickets_router
from app.api.health import router as health_router, demo_router
from app.db.mongodb import close_mongo_client

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="HealthAssist AI Support Agent",
    description=(
        "AI Customer Support & Resolution Agent for a healthcare "
        "quick doctor-patient connection platform."
    ),
    version="1.0.0",
)

# CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(tickets_router)
app.include_router(demo_router)


@app.on_event("startup")
async def startup():
    """Application startup — verify connections."""
    settings = get_settings()
    logger.info(
        "application_starting",
        environment=settings.ENVIRONMENT,
        llm_model=settings.LLM_MODEL,
    )


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown — cleanup connections."""
    await close_mongo_client()
    logger.info("application_shutdown")
