# Absolute imports
import os
import tempfile
from configparser import ConfigParser
from importlib import resources

# Relative imports
from .. import wifi
from ..util.parse_config import expand_env, parse_config
from ..util.is_raspberry_pi import is_RPi
from ..util.system_call import system_call


__all__ = ['read_hostapd_config', 'write_hostapd_config']


_hostapd_etc = '/etc/hostapd/hostapd.conf'
_hostapd_tmp = os.path.join(tempfile.gettempdir(), 'hostapd.conf')
_hostapd_raw = resources.files(wifi) / 'hostapd.conf'
_hostapd_cfg = _hostapd_etc if is_RPi and os.path.isfile(_hostapd_etc) else _hostapd_tmp


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
