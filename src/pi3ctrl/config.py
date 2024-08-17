__all__ = ['Config']


class Config(object):
    """Pi3Ctrl default configuration values.
    """
    DEBUG = True
    DEVELOPMENT = True

    SECRET_KEY = 'do-i-really-need-this'
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = 'some-very-long-ascii-string-you-can-not-remember!'

    BUTTON_PINS = [17, 27, 22]

    LED = True
    LED_ON_SECONDS = .5
    LED_OFF_SECONDS = 1.5
    LED_PINS = [18, 23, 24]

    SOUNDFILE_ALLOWED_EXTENSIONS = {'wav', 'raw', 'pcm'}
    SOUNDFILE_FOLDER = '${HOME}/Pi3Ctrl'
    SOUNDFILE_PLAYER = '/usr/bin/aplay'

    MAX_CONTENT_LENGTH = 128 * 1000 * 1000  # 128MB

    SYSTEMD_STATUS = ['nginx.service', 'dnsmasq.service', 'hostapd.service']

    def to_dict(self):
        return {k: v for k, v in self.__class__.__dict__.items() if not callable(v) and not k.startswith('__')}

    def items(self):
        return self.to_dict()
