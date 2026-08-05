import logging
import sys
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    Intercepts standard Python logging messages (like Uvicorn's) 
    and routes them to Loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    # 1. Clear existing loguru handlers
    logger.remove()

    # 2. Intercept standard logging
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    for name in ["uvicorn.access", "uvicorn.error", "fastapi"]:
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False

    # 3. Add Console Sink (Human readable)
    logger.add(sys.stderr, level="INFO", colorize=True, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

    # 4. Add File Sink (JSON for Datadog/ELK)
    logger.add("logs/enterprise_agent.log", rotation="500 MB", level="DEBUG", serialize=True)