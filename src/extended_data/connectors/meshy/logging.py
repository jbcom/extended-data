"""Rich logging configuration for Meshy SDK."""

from __future__ import annotations

import logging

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure Rich logging with proper exception handling.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=False, show_path=True)],
    )

    logger = logging.getLogger("meshy")
    logger.setLevel(level)

    return logger


# Global logger instance
logger = setup_logging()
