"""
BloodBridge AI — FastAPI Backend.
Main application entry point.
"""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from core.neo4j_client import close as close_neo4j, health_check as check_neo4j
from core.database import get_supabase
from postgrest.types import CountMethod

# Import all API routers
from api.emergency import router as emergency_router
from api.donors import router as donors_router
from api.patients import router as patients_router
from api.blood_banks import router as blood_banks_router
from api.admin import router as admin_router
from api.websocket import router as websocket_router
from api.lora import router as lora_router
from api.webhooks import router as webhooks_router
from api.auth import router as auth_router

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bloodbridge")

# Setup rate limiter
from core.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events context manager.
    Handles startup configuration (scheduler, webhook bots) and shutdown cleanups.
    """
    logger.info("Initializing BloodBridge AI services...")
    
    # A6: Production safety checks
    if settings.APP_ENV == "production":
        if settings.DEMO_MOCK_MODE:
            raise RuntimeError("FATAL: DEMO_MOCK_MODE=True in production. Aborting.")
        if settings.ALLOWED_ORIGINS == "*":
            logger.warning("CORS ALLOWED_ORIGINS is '*' in production — consider restricting.")
        if settings.NEO4J_PASSWORD in ["", "password", "admin"]:
            raise RuntimeError("FATAL: Neo4j password is insecure in production. Aborting.")
    
    # 1. Startup APScheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from scheduler.cron import setup_cron_jobs
        scheduler = AsyncIOScheduler()
        setup_cron_jobs(scheduler)
        app.state.scheduler = scheduler
        scheduler.start()
        logger.info("APScheduler and recurring cron jobs started successfully.")

        # One-shot startup job: auto-generate transfusion schedules for eligible patients
        from datetime import datetime, timedelta
        from scheduler.jobs import run_auto_schedule_generation
        scheduler.add_job(
            run_auto_schedule_generation,
            'date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='auto_schedule_startup',
            replace_existing=True
        )
        logger.info("Auto-schedule generation startup job registered (30s delay).")
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}", exc_info=True)

    # 2. Startup Bot webhook/polling setups placeholder
    logger.info("Telegram Bot service placeholder loaded.")
    
    yield
    
    # 3. Shutdown APScheduler
    if hasattr(app.state, "scheduler"):
        logger.info("Stopping APScheduler...")
        app.state.scheduler.shutdown()
        logger.info("APScheduler stopped.")
        
    # 4. Close Neo4j client connection
    logger.info("Closing Neo4j connections...")
    await close_neo4j()
    logger.info("Neo4j driver connection closed.")
    logger.info("Shutdown lifecycle complete.")

# Initialize app
app = FastAPI(
    title="BloodBridge AI",
    version="1.0.0",
    description="Agentic AI FastAPI backend for BloodBridge blood donation matching & coordination",
    lifespan=lifespan
)

# Exception handlers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS middleware config — uses ALLOWED_ORIGINS from env (A6)
origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(emergency_router)
app.include_router(donors_router)
app.include_router(patients_router)
app.include_router(blood_banks_router)
app.include_router(admin_router)
app.include_router(websocket_router)
app.include_router(lora_router)
app.include_router(webhooks_router)
app.include_router(auth_router)

@app.get("/health")
async def health_endpoint():
    """
    GET /health
    Verifies availability and calculates latency for all system microservices.
    """
    services_status = {}
    
    # FastAPI service check
    services_status["fastapi"] = {"status": "ok", "latency_ms": 0}
    
    # Neo4j connection check
    t0 = time.perf_counter()
    neo4j_ok = await check_neo4j()
    neo4j_latency = int((time.perf_counter() - t0) * 1000)
    services_status["neo4j"] = {
        "status": "ok" if neo4j_ok else "offline",
        "latency_ms": neo4j_latency
    }
    
    # Supabase connection check
    t0 = time.perf_counter()
    supabase_ok = False
    try:
        supabase = get_supabase()
        # Check client connectivity by querying exact count on donors table
        supabase.table("donors").select("count", count=CountMethod.exact).limit(1).execute()
        supabase_ok = True
    except Exception as e:
        logger.warning(f"Supabase connection test failed: {e}")
        
    supabase_latency = int((time.perf_counter() - t0) * 1000)
    services_status["supabase"] = {
        "status": "ok" if supabase_ok else "degraded",
        "latency_ms": supabase_latency
    }
    
    # Telegram API connection check
    t0 = time.perf_counter()
    telegram_ok = False
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.telegram.org", timeout=2.0)
            if resp.status_code in [200, 404]:
                telegram_ok = True
    except Exception as e:
        logger.warning(f"Telegram reachability check failed: {e}")
        
    telegram_latency = int((time.perf_counter() - t0) * 1000)
    services_status["telegram"] = {
        "status": "ok" if telegram_ok else "offline",
        "latency_ms": telegram_latency
    }
    
    # Bolna.ai API connection check (India-first voice call provider)
    t0 = time.perf_counter()
    bolna_ok = False
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.bolna.ai", timeout=2.0)
            if resp.status_code in [200, 404, 405, 422]:
                bolna_ok = True
    except Exception as e:
        logger.warning(f"Bolna reachability check failed: {e}")

    bolna_latency = int((time.perf_counter() - t0) * 1000)
    services_status["bolna"] = {
        "status": "ok" if bolna_ok else "offline",
        "latency_ms": bolna_latency
    }
    
    overall_status = "ok"
    if not neo4j_ok or not supabase_ok:
        overall_status = "degraded"
        
    return {
        "status": overall_status,
        "services": services_status
    }
