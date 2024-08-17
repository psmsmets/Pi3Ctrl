#!/usr/bin/env python
from setuptools import setup
from setuptools.command.install import install
from subprocess import check_call
import atexit


def _post_install():
    """Post-installation."""
    print('POST INSTALL')
    check_call("ls $HOME".split())


class new_install(install):
    def __init__(self, *args, **kwargs):
        super(new_install, self).__init__(*args, **kwargs)
        atexit.register(_post_install)


if __name__ == "__main__":
    setup(cmdclass={'install': new_install})
