# Absolute imports
import os
from flask import Config


__all__ = ['DefaultConfig', 'get_config']


class DefaultConfig(object):
    """Pi3Ctrl default configuration values (all uppercase to be persistent!).
    """
    # Default
    DEBUG = True
    DEVELOPMENT = False

    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = 'some-very-long-ascii-string-you-can-not-remember!'

    SECRET_KEY = 'do-i-really-need-this'

    # Hostapd
    HOSTAPD_COUNTRY_CODE = 'BE'
    HOSTAPD_CHANNEL = 6
    HOSTAPD_SSID = '${HOSTNAME}'
    HOSTAPD_WPA_PASSPHRASE = 'ChangePassword!'

    # Pi3Ctrl
    BUTTON_PINS = [17, 27, 22]
    BUTTON_OFF_SECONDS = 5

    LED = True
    LED_ON_SECONDS = .5
    LED_OFF_SECONDS = 1.5
    LED_PINS = [18, 23, 24]

    SOUNDFILE_ALLOWED_EXTENSIONS = {'wav', 'raw', 'pcm'}
    SOUNDFILE_FOLDER = '${HOME}/Pi3Ctrl'
    SOUNDFILE_PLAYER = '/usr/bin/aplay'

    MAX_CONTENT_LENGTH = 128 * 1000 * 1000  # 128MB

    SYSTEMD_STATUS = []


def get_config():
    """Get the pi3ctrl configuration as a `flask.Config`"""
    # init config object
    config = Config(os.path.dirname(os.path.abspath(__file__)))

    # load default config
    config.from_object('pi3ctrl.config.DefaultConfig')

    # load config from environ
    if os.environ.get('PI3CTRL_CONFIG') is not None:
        config.from_envvar('PI3CTRL_CONFIG', silent=True)

    return config
