import logging
import sys


def setup_logging(level=logging.INFO):
    logger = logging.getLogger("agent")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


logger = setup_logging()
