"""HTTP lifecycle and database readiness for this independent provider."""
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

SERVICE = "revenue"
logger = logging.getLogger("uvicorn.error")


def setting(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


engine = create_engine(setting("DATABASE_URL"), pool_pre_ping=True, pool_timeout=3,
                       connect_args={"connect_timeout": 3}, hide_parameters=True)


@asynccontextmanager
async def lifespan(app):
    yield
    engine.dispose()


app = FastAPI(title=SERVICE + " simulated provider", lifespan=lifespan)


def error(status, code, category, message):
    return JSONResponse(status_code=status, content={
        "code": code, "category": category, "message": message,
        "transaction_reference": None, "provider_reference": SERVICE,
        "retryable": status == 503, "timestamp": datetime.now(UTC).isoformat(),
    })


@app.middleware("http")
async def log_request(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        response = error(500, "INTERNAL_ERROR", "INTERNAL", "Unexpected provider error")
    route = request.scope.get("route")
    logger.info(json.dumps({"provider": SERVICE, "event": "request", "method": request.method,
                            "route": getattr(route, "path", "unmatched"), "status": response.status_code}))
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    return error(503, "DATABASE_UNAVAILABLE", "PROVIDER", "Department database unavailable")


@app.get("/health")
def health():
    with engine.connect() as db:
        db.execute(text("SELECT 1 FROM revenue.revenue_records LIMIT 1"))
    return {"provider": SERVICE, "status": "ready", "simulated": True}
