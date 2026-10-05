"""Structured logging configuration using loguru."""
import sys
from loguru import logger
from app.core.config import settings


def configure_logging() -> None:
    logger.remove()
    log_level = "DEBUG" if settings.debug else "INFO"
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, format=fmt, level=log_level, colorize=True)
    if settings.is_production:
        logger.add(
            "logs/app.log",
            rotation="100 MB",
            retention="30 days",
            level="INFO",
            serialize=True,
        )
