# absolute imports
from flask import current_app as app
from logging import Logger
from subprocess import Popen, PIPE
import os
import socket
import sys


__all__ = ['is_RPi']


core_services = ['pi3ctrl-core.service',
                 'pi3ctrl-http.service',
                 'pi3ctrl-wifi.service',
                 'nginx.service',
                 'dnsmasq.service',
                 'hostapd.service']


def is_raspberry_pi():
    """Checks if the device is a Rasperry Pi
    """
    if not os.path.exists('/proc/device-tree/model'):
        return False
    with open('/proc/device-tree/model') as f:
        model = f.read()
    return model.startswith('Raspberry Pi')


is_RPi = is_raspberry_pi()


def get_ipv4_address():
    """Get the RPi's private IPv4 address"""
    hostname_ips = socket.gethostbyname_ex(socket.gethostname())[2]
    ip_list = [ip for ip in hostname_ips if not ip.startswith("127.")]
    if ip_list:
        return ip_list[0]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 53))
    ip = s.getsockname()[0]
    s.close()
    return ip if ip else "127.0.0.1"


def systemd_status(service: str):
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


def systemd_status_all():
    """Get the systemd status of all services.
    """
    status = dict()
    services = core_services + app.config['SYSTEMD_STATUS']
    for s in services:
        status[s] = systemd_status(s)
    return status


def wifi_ssid_passphrase(ssid: str, passphrase: str):
    """Add Wi-Fi ssid and passphrase to wpa_supplicant and connect.
    """
    cmd = os.path.join(os.path.dirname(sys.executable), 'append_wpa_supplicant')
    return system_call([cmd, ssid, passphrase], as_dict=True)


def wifi_autohotspot():
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
