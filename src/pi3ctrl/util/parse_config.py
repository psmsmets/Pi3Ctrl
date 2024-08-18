# Absolute imports
import os
import re
import socket
from configparser import ConfigParser, MissingSectionHeaderError


__all__ = ['expand_env', 'parse_config']


def expand_env(var: str) -> str:
    """Expand environment variable if defined."""
    # print(os.environ['HOSTNAME'], os.environ)
    if re.sub(r'[^A-Z]', '', var.upper()) == 'HOSTNAME':
        return socket.gethostname()
    else:
        return os.environ.get(var, var)


def parse_config(filenames, config=None, defaults=None, logger=None, **kwargs):
    """Parse a single config file using ConfigParser.read() while catching the
    MissingSectionHeaderError to the section '[default]'.
    """

    # subsitute clean environment
    if defaults is True:
        defaults = os.environ

    # init
    config = config or ConfigParser(defaults=defaults, **kwargs)

    # Config paths should be list or tuple
    if isinstance(filenames, str):
        filenames = [filenames]
    elif not isinstance(filenames, (list, tuple)):
        raise TypeError('filenames should be a str or a list/tuple of str')

    # parse files and add DEFAULT section if missing
    for filename in filenames:
        with open(filename, 'r') as f:
            try:
                config.read_file(f, source=config)
            except MissingSectionHeaderError:
                f_str = '[DEFAULT]\n' + f.read()
                config.read_string(f_str)

    return config
