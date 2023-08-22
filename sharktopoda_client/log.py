"""
Logging utilities.
"""

import logging


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a pre-configured logger with a given name.

    Args:
        name: The name of the logger.

    Returns:
        A logger with a given name.
    """
    logger = logging.Logger(name, level=level)

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
            self._logger.addHandler(logging.NullHandler())  # Ensure no errors if no handlers are configured
        return self._logger
