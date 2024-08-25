#!/bin/bash

pip install .

# apt
sudo apt update
sudo apt install -y rsyslog nginx dnsmasq hostapd
sudo apt purge -y dns-root-data

# /etc
sudo rsync -amtv --chown=root:root etc/* /etc

# services
sudo systemctl daemon-reload
sudo systemctl reset-failed

# rsyslog
sudo mkdir -p /var/log/pi3ctrl
sudo chown -R $USER:www-data /var/log/pi3ctrl
sudo systemctl restart rsyslog

# dnsmasq
sudo systemctl reset-failed dnsmasq
sudo systemctl unmask dnsmasq
sudo systemctl disable dnsmasq
sudo systemctl stop dnsmasq

# hostapd
sudo systemctl reset-failed hostapd
sudo systemctl unmask hostapd
sudo systemctl disable hostapd
sudo systemctl stop hostapd

# wpa_supplicant
sudo systemctl unmask wpa_supplicant
sudo systemctl disable wpa_supplicant

# nginx
sudo systemctl enable nginx
sudo systemctl stop nginx
sudo unlink /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# pi3ctrl-core
sudo systemctl enable pi3ctrl-core.service 
sudo systemctl restart pi3ctrl-core.service

# pi3ctrl-http
sudo systemctl enable pi3ctrl-http.service 
sudo systemctl restart pi3ctrl-http.service

# pi3ctrl-wifi
sudo systemctl enable pi3ctrl-wifi.service 
sudo systemctl restart pi3ctrl-wifi.service

# done
exit 0
