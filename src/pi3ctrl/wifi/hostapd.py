# Absolute imports
import os
import re
import socket
import tempfile
from flask import Config
from importlib import resources

# Relative imports
from .. import wifi
from ..utils import is_RPi, system_call


__all__ = ['read_hostapd_config', 'write_hostapd_config', 'update_hostapd_config']


_hostapd_etc = '/etc/hostapd/hostapd.conf'
_hostapd_tmp = os.path.join(tempfile.gettempdir(), 'hostapd.conf')
_hostapd_raw = resources.files(wifi) / 'hostapd.conf'
_hostapd_cfg = _hostapd_etc if is_RPi and os.path.isfile(_hostapd_etc) else _hostapd_tmp


def expand_env(var: str) -> str:
    """Expand environment variable if defined."""
    if re.sub(r'[^A-Z]', '', var.upper()) == 'HOSTNAME':
        return socket.gethostname()
    else:
        return os.environ.get(var, var)


def read_hostapd_config(**kwargs) -> Config:
    """Read the hostapd configuration from the config file."""
    # init config object
    config = Config('')

    # read the hostapd config
    config.from_pyfile(_hostapd_cfg)

    return config


def write_hostapd_config(config, **kwargs) -> None:
    """Write the mapped hostapd configuration to a file.
    """
    if is_RPi:
        os.umask(0)

    def opener(path, flags):
        return os.open(path, flags, 0o644)

    with open(_hostapd_raw, "r") as fo:
        hostapd = fo.read()

    with open(_hostapd_tmp, 'w', opener=opener) as fw:
        fw.write(
            hostapd.format(
                CHANNEL=config['HOSTAPD_CHANNEL'],
                SSID=expand_env(config['HOSTAPD_SSID']),
                WPA_PASSPHRASE=expand_env(config['HOSTAPD_WPA_PASSPHRASE']),
                COUNTRY_CODE=config['HOSTAPD_COUNTRY_CODE']
            )
        )

    cmd = ['/usr/bin/sudo', '/usr/bin/cp', _hostapd_tmp, _hostapd_cfg]

    return system_call(cmd, **kwargs) if is_RPi else True


def update_hostapd_config(config: Config, **kwargs) -> Config:
    """Update, write and load the hostapd configuration."""

    if write_hostapd_config(config, **kwargs):
        pass
    hostapd = read_hostapd_config()

    return hostapd
