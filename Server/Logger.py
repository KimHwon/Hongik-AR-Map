import logging

from .Config import *

def get_logger(name: str = None):
    logger = logging.getLogger(name)
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    stderr = logging.StreamHandler()
    stderr.setLevel(logging.DEBUG)
    stderr.setFormatter(
        logging.Formatter('[%(asctime)-10s] (line No: %(lineno)d) %(name)s:%(levelname)s - %(message)s')
    )
    logger.addHandler(stderr)

    return logger