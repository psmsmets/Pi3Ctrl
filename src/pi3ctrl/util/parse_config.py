# Absolute imports
import os
import re
import socket
from configparser import ConfigParser, MissingSectionHeaderError


__all__ = ['expand_env', 'parse_config']


def expand_env(var: str) -> str:
    """Expand environment variable if defined."""
    if re.sub(r'[^A-Z]', '', var.upper()) == 'HOSTNAME':
        return socket.gethostname()
    else:
        return os.environ.get(var, var)


def parse_config(configfiles, config=None, defaults=None, logger=None, **kwargs):
    """Parse a single config file using ConfigParser.read() while catching the
    MissingSectionHeaderError to the section '[DEFAULT]'.
    """

    # Init object with defaults
    if defaults is True:
        defaults=os.environ
    
    config = config or ConfigParser(defaults=defaults, **kwargs)

    # Config paths should be list or tuple
    if isinstance(configfiles, str):
        configfiles = [configfiles]
    elif not isinstance(configfiles, (list, tuple)):
        raise TypeError('configfiles should be a str or a list/tuple of str')

    # Parse files and add DEFAULT section if missing
    for configfile in configfiles:

        configfile = os.path.expandvars(configfile)

        if not os.path.isfile(configfile):
            continue

        with open(configfile, 'r') as f:
            try:
                config.read_file(f, source=config)
            except MissingSectionHeaderError:
                f_str = '[DEFAULT]\n' + f.read()
                config.read_string(f_str)

    return config
