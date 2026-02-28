"""AUTHENTIX LEDGER — FastAPI Application Entrypoint."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import auth, cases, evidence, profiles, registry, reports

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("authentix_ledger.startup", blockchain_mode=settings.BLOCKCHAIN_MODE)
    # Ensure MinIO bucket exists on startup
    try:
        from app.services.storage import get_minio_client
        get_minio_client()
    except Exception as e:
        logger.warning("minio.init_failed", error=str(e))
    yield
    logger.info("authentix_ledger.shutdown")


app = FastAPI(
    title="AUTHENTIX LEDGER API",
    description="Blockchain-backed fake profile detection system for law enforcement",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Security Middleware ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request.start", method=request.method, path=request.url.path)
    response = await call_next(request)
    logger.info("request.end", method=request.method, path=request.url.path, status=response.status_code)
    return response


# ── Prometheus Metrics ─────────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ── Routers ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)
app.include_router(profiles.router, prefix=API_PREFIX)
app.include_router(evidence.router, prefix=API_PREFIX)
app.include_router(registry.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "authentix-ledger", "version": "1.0.0"}


@app.get("/", tags=["Health"])
def root():
    return {"message": "AUTHENTIX LEDGER API — see /api/docs for documentation"}
