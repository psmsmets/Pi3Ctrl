__all__ = ['Config']


class Config(object):
    DEBUG = True
    DEVELOPMENT = True
    SECRET_KEY = 'do-i-really-need-this'
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = SECRET_KEY

    BUTTON_PINS = [17, 27, 22]  # Change these to the pins you are using
    LED_PINS = [18, 23, 24]     # Change these to the LED pins you are using
