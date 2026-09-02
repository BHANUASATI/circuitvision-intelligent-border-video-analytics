"""
Centralised logger — Loguru with structured JSON output in production.
"""
import sys
from loguru import logger
from ai_service.configs.settings import settings


def setup_logger() -> None:
    logger.remove()  # remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    )

    if settings.app_env == "production":
        # JSON structured log to stdout — ingested by log aggregators
        logger.add(
            sys.stdout,
            level="INFO",
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stdout,
            level="DEBUG",
            format=log_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Always persist errors to file inside container
    logger.add(
        "/var/log/ibvap/ai_service_errors.log",
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
        serialize=True,
    )


setup_logger()

__all__ = ["logger"]
