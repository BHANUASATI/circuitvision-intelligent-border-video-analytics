"""Backend structured logger — mirrors ai_service pattern."""
import sys
from loguru import logger
from app.core.config import settings


def setup_logger() -> None:
    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
    )
    if settings.app_env == "production":
        logger.add(sys.stdout, level="INFO", serialize=True, backtrace=False)
    else:
        logger.add(sys.stdout, level="DEBUG", format=fmt, colorize=True)

    import os, pathlib
    log_dir = pathlib.Path(os.environ.get("LOG_DIR", "/tmp/ibvap_logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_dir / "backend_errors.log"),
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
        serialize=True,
    )


setup_logger()
__all__ = ["logger"]
