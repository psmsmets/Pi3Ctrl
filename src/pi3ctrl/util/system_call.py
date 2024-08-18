# Absolute imports
import logging
from subprocess import Popen, PIPE


# Relative import
from ..util.logger import init_logger


__all__ = ['system_call']


def system_call(command: list, logger: logging.Logger = None, **kwargs):
    """Execute a system call. Returns `True` on success.
    """
    if not isinstance(command, list):
        raise TypeError("command should be a list!")

    logger = logger if isinstance(logger, logging.Logger) else init_logger(debug=True)
    logger.debug(' '.join(command))

    p = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)

    output, error = p.communicate()

    if output:
        logger.debug(output.decode("utf-8"))

    if p.returncode != 0:
        logger.error(error.decode("utf-8"))

    return p.returncode == 0
