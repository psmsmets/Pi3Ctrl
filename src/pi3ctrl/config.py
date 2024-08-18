__all__ = ['Config']


class Config(object):
    """Pi3Ctrl default configuration values.
    """
    # Default
    DEBUG = True
    DEVELOPMENT = True

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

    LED = True
    LED_ON_SECONDS = .5
    LED_OFF_SECONDS = 1.5
    LED_PINS = [18, 23, 24]

    SOUNDFILE_ALLOWED_EXTENSIONS = {'wav', 'raw', 'pcm'}
    SOUNDFILE_FOLDER = '${HOME}/Pi3Ctrl'
    SOUNDFILE_PLAYER = '/usr/bin/aplay'

    MAX_CONTENT_LENGTH = 128 * 1000 * 1000  # 128MB

    SYSTEMD_STATUS = []

    # Extra handlers
    def to_dict(self):
        return {k: v for k, v in self.__class__.__dict__.items() if not callable(v) and not k.startswith('__')}

    def items(self):
        return self.to_dict()
