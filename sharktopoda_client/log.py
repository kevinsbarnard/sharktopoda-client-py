"""
Logging utilities.
"""

import logging


FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
STREAM_HANDLER = logging.StreamHandler()
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.DEBUG)


def set_stream_level(level: int) -> None:
    """
    Set the log level of the stream handler.
    
    Args:
        level: The log level to set the stream handler to.
    """
    STREAM_HANDLER.setLevel(level)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a pre-configured logger with a given name.
    
    Args:
        name: The name of the logger.
    
    Returns:
        A logger with a given name.
    """
    logger = logging.Logger(name, level=level)
    logger.addHandler(STREAM_HANDLER)
    
    return logger


class LogMixin:
    """
    Mixin to add a logger to a class.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger for a class.
        
        Returns:
            The logger for a class.
        """
        if getattr(self, "_logger", None) is None:  # lazy instantiation
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
