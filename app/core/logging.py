import sys

from loguru import logger


def configure_logging(level: str, structured: bool = False) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        backtrace=False,
        diagnose=False,
        enqueue=False,
        serialize=structured,
    )
