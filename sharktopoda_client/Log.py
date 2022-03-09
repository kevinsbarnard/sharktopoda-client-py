import logging

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_logger(name: str, level=logging.DEBUG):
    logger = logging.Logger(name, level=level)
    formatter = logging.Formatter(LOG_FORMAT)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger
    