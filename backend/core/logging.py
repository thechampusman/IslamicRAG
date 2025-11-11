import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)

logger = logging.getLogger("islamic_rag")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)

__all__ = ["logger"]
