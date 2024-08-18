# Absolute imports
import os
import tempfile
from configparser import ConfigParser

# Relative imports
from ..util.parse_config import expand_env, parse_config
from ..util.is_raspberry_pi import is_RPi


__all__ = ['read_hostapd_config', 'write_hostapd_config']


_hostapd_raw = os.path.join('wifi', 'hostapd.conf')
_hostapd_cfg = os.path.join('/etc/hostapd' if is_RPi else tempfile.gettempdir(), 'hostapd.conf')


def read_hostapd_config(**kwargs) -> ConfigParser:
    """Parse the hostapd configuration using ConfigParser.
    """
    try:
        hostapd = parse_config(_hostapd_cfg, **kwargs)
    except FileNotFoundError:
        hostapd = parse_config(_hostapd_raw, **kwargs)

    return hostapd


def write_hostapd_config(config, **kwargs) -> None:
    """Parse the hostapd configuration using ConfigParser.
    """
    if is_RPi:
        os.umask(0)

    def opener(path, flags):
        return os.open(path, flags, 0o644)

    with open(_hostapd_raw, "r") as fo:
        hostapd = fo.read()

    with open(_hostapd_cfg, 'w', opener=opener) as fm:
        fm.write(
            hostapd.format(
                CHANNEL=config['HOSTAPD_CHANNEL'],
                SSID=expand_env(config['HOSTAPD_SSID']),
                WPA_PASSPHRASE=expand_env(config['HOSTAPD_WPA_PASSPHRASE']),
                COUNTRY_CODE=config['HOSTAPD_COUNTRY_CODE']
            )
        )

    return None
