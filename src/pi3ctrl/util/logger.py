# Absolute imports
import logging
import sys


__all__ = ['init_logger']


def init_logger(
    prog=None, debug=False
):
    """Create the logger object
    """
    # create logger
    logger = logging.getLogger(prog or 'audio-player')

    # log to stdout
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(logging.Formatter(
        "%(levelname)s: %(message)s"
        # "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(streamHandler)

    # set logger level
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    return logger
