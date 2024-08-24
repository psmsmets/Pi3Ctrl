# Absolute imports
import os
from flask import Config


__all__ = ['DefaultConfig', 'get_config']


class DefaultConfig(object):
    """Pi3Ctrl default configuration values (all uppercase to be persistent!).
    """
    # Flask
    DEBUG = True
    DEVELOPMENT = False

    SECRET_KEY = 'some-very-long-ascii-string-you-should-not-remember!'
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = SECRET_KEY

    # Pi3Ctrl
    PI3CTRL_SECRET = 'PleaseChange!'

    BUTTON_PINS = [17, 27, 22]
    BUTTON_OFF_SECONDS = 5

    LED = True
    LED_ON_SECONDS = .5
    LED_OFF_SECONDS = 1.5
    LED_PINS = [18, 23, 24]

    SOUNDFILE_ALLOWED_EXTENSIONS = {'wav', 'raw', 'pcm'}
    SOUNDFILE_FOLDER = 'soundFiles'
    SOUNDFILE_PLAYER = '/usr/bin/aplay'

    MAX_CONTENT_LENGTH = 128 * 1000 * 1000  # 128MB

    SYSTEMD_STATUS = []

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pi3ctrl.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Hostapd
    HOSTAPD_COUNTRY_CODE = 'BE'
    HOSTAPD_CHANNEL = 6
    HOSTAPD_SSID = '${HOSTNAME}'
    HOSTAPD_WPA_PASSPHRASE = 'ChangePassword!'


def get_config():
    """Get the pi3ctrl configuration as a `flask.Config`"""
    # init config object
    config = Config(os.path.dirname(os.path.abspath(__file__)))

    # load default config
    config.from_object('pi3ctrl.config.DefaultConfig')

    # load config from etc
    if os.path.isfile('/etc/pi3ctrl/pi3ctrl.conf'):
        config.from_pyfile('/etc/pi3ctrl/pi3ctrl.conf')

    # load config from environ
    if os.environ.get('PI3CTRL_CONFIG') is not None:
        config.from_envvar('PI3CTRL_CONFIG', silent=True)

    return config
