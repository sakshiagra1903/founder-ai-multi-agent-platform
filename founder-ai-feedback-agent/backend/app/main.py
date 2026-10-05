"""
Founder AI — Feedback Agent
FastAPI application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.database import create_tables
from app.api.routes import auth, feedback, analytics, insights, chat, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.upload_dir + "/reports", exist_ok=True)
    logger.info(f"Starting {settings.app_name} [{settings.app_env}]")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    await create_tables()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered customer feedback intelligence for startup founders",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.app_name} API", "docs": "/docs"}
