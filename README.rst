*************************************
Pi3Ctrl
*************************************

|Maintenance yes| |MIT license| |made-with-python| |Workflow status|

.. |Maintenance yes| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
.. |MIT license| image:: https://img.shields.io/badge/License-MIT-blue.svg
.. |made-with-python| image:: https://img.shields.io/badge/Made%20with-Python-1f425f.svg
.. |Workflow status| image:: https://github.com/psmsmets/pi3ctrl/actions/workflows/tests.yml/badge.svg

Python 3 event player for Raspberry Pi with GPIO control.


Setup
=====

.. codeblock:: bash

   git clone https://github.com/psmsmets/Pi3Ctrl.git

   cd Pi3Ctrl

   pip install .

   sudo rsync -amtv --chown=root:root src/etc/* /etc

   sudo systemctl daemon-reload
   sudo systemctl reset-failed

   sudo systemctl reset-failed dnsmasq
   sudo systemctl unmask dnsmasq
   sudo systemctl disable dnsmasq

   sudo systemctl reset-failed hostapd
   sudo systemctl unmask hostapd
   sudo systemctl disable hostapd

   sudo systemctl enable nginx
   sudo systemctl restart nginx

   sudo systemctl enable pi3ctrl-core.service 
   sudo systemctl restart pi3ctrl-core.service

   sudo systemctl enable pi3ctrl-http.service 
   sudo systemctl restart pi3ctrl-http.service

   sudo systemctl enable pi3ctrl-wifi.service 
   sudo systemctl restart pi3ctrl-wifi.service




Licensing
=========

The source code for Pi3Ctrl is open-source and licensed under MIT_.

.. _MIT: https://raw.githubusercontent.com/psmsmets/pi3ctrl/main/LICENSE

Pieter Smets © 2024. All rights reserved.
