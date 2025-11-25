import logging


def get_logger():
    logger = logging.getLogger("notifier")
    # logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.INFO)
    # Add handler only if not already added
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
