import logging

from Config import *

def get_logger(name: str = None):
    logger = logging.getLogger(name)
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)
    
    fmt = logging.Formatter('[%(asctime)-10s] (line No: %(lineno)d) %(name)s:%(levelname)s - %(message)s')

    stderr = logging.StreamHandler()
    stderr.setLevel(logging.DEBUG)
    stderr.setFormatter(fmt)
    logger.addHandler(stderr)

    fperr = logging.FileHandler('debug.log')
    fperr.setLevel(logging.DEBUG)
    fperr.setFormatter(fmt)
    logger.addHandler(fperr)

    return logger
    