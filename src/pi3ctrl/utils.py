# absolute imports
from configparser import ConfigParser, MissingSectionHeaderError
from flask import current_app as app
from logging import Logger
from subprocess import Popen, PIPE
import logging
import os
import socket
import sys


__all__ = ['is_RPi']


core_services = ['pi3ctrl-core.service',
                 'pi3ctrl-http.service',
                 'pi3ctrl-wifi.service',
                 'nginx.service',
                 'dnsmasq.service',
                 'hostapd.service',
                 'wpa_supplicant.service']


def is_raspberry_pi() -> bool:
    """Checks if the device is a Rasperry Pi
    """
    if not os.path.exists('/proc/device-tree/model'):
        return False
    with open('/proc/device-tree/model') as f:
        model = f.read()
    return model.startswith('Raspberry Pi')


is_RPi = is_raspberry_pi()


def get_ipv4_address() -> str:
    """Get the RPi's private IPv4 address"""
    try:
        hostname_ips = socket.gethostbyname_ex(socket.gethostname())[2]
        ip_list = [ip for ip in hostname_ips if not ip.startswith("127.")]
        if ip_list:
            return ip_list[0]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        ip = None
    return ip or "127.0.0.1"


def parse_config(configfiles, config=None, defaults=None, logger=None, environ=False, **kwargs):
    """Parse a single config file using ConfigParser.read() while catching the
    MissingSectionHeaderError to the section '[DEFAULT]'.
    """

    # Init object with defaults
    if defaults is True:
        defaults = os.environ

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


def systemd_status(service: str) -> dict:
    """Get the systemd status of a single service.
    """
    r = system_call(['/usr/bin/systemctl', 'status', service], as_dict=True)
    if r['stdout'] and 'Active: ' in r['stdout']:
        status = r['stdout'].split('<br>')[2].split('Active: ')[1]
        if 'since' in status:
            status = status.split(' since ')[0]
    else:
        status = None
    return dict(service=service, status=status, **r)


def systemd_status_all() -> dict:
    """Get the systemd status of all services.
    """
    status = dict()
    services = core_services + app.config['SYSTEMD_STATUS']
    for s in services:
        status[s] = systemd_status(s)
    return status


def wifi_ssid_passphrase(ssid: str, passphrase: str) -> dict:
    """Add Wi-Fi ssid and passphrase to wpa_supplicant and connect.
    """
    cmd = os.path.join(os.path.dirname(sys.executable), 'append_wpa_supplicant')
    return system_call(['/usr/bin/sudo', cmd, ssid, passphrase], as_dict=True)


def wifi_autohotspot() -> dict:
    """Run autohotspot.
    """
    return system_call(['/usr/bin/sudo', '/usr/bin/systemctl', 'start', 'pi3ctrl-wifi'], as_dict=True)


def system_call(*args, logger: Logger = None, as_dict: bool = False, **kwargs):
    """Wraps Popen and Popen.communicate() in a catch error statement and
    returns a serialized dictionary object for jsonify.
    """

    log = isinstance(logger, Logger)

    def _resp_dict(**kwargs):
        r = {
            'success': False,
            'returncode': None,
            'stdout': None,
            'stderr': None,
            **kwargs,
        }
        return r

    logger.debug(' '.join(args[0])) if log else None

    try:
        p = Popen(*args, **kwargs, stdout=PIPE, stderr=PIPE)
    except OSError as e:
        logger.error(e) if log else None
        return _resp_dict('error', e) if as_dict else False

    try:
        # wait for process to finish;
        # this also sets the returncode variable inside 'p'
        stdout, stderr = p.communicate()

        success = p.returncode == 0

        if log:
            if stdout:
                logger.debug(stdout.decode("utf-8"))
            if not success:
                logger.error(stderr.decode("utf-8"))

        # construct return dict
        if as_dict:
            r = _resp_dict(
                success=success,
                returncode=p.returncode,
                stdout="<br>".join(stdout.decode("utf-8").split("\n")),
                stderr="<br>".join(stderr.decode("utf-8").split("\n")),
            )
        else:
            r = success
    except Exception as e:
        logger.error(e.strerror) if log else None
        r = _resp_dict(returncode=e.errno, stderr=e.strerror) if as_dict else False

    return r


def get_logger(prog=None, debug=False):
    """Create the logger object
    """
    # create logger
    logger = logging.getLogger(prog or __name__)

    # log to stdout
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(logging.Formatter(
        "%(levelname)s: %(message)s"
        # "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(streamHandler)

    # set logger level
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    return logger
