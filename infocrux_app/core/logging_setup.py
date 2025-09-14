import logging, sys
from logging.handlers import RotatingFileHandler
from .config import STORAGE_DIR

def setup_logger():
    log_file = STORAGE_DIR / "app.log"
    logger = logging.getLogger("infocrux")
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout); sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    if not logger.handlers:
        logger.addHandler(sh); logger.addHandler(fh)
    return logger
