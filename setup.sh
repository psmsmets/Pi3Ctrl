#!/bin/bash

pip install .

sudo rsync -amtv --chown=root:root etc/* /etc

sudo systemctl daemon-reload
sudo systemctl reset-failed

sudo systemctl reset-failed dnsmasq
sudo systemctl unmask dnsmasq
sudo systemctl disable dnsmasq

sudo systemctl reset-failed hostapd
sudo systemctl unmask hostapd
sudo systemctl disable hostapd

sudo systemctl enable nginx
sudo systemctl stop nginx
sudo unlink /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

sudo systemctl enable pi3ctrl-core.service 
sudo systemctl restart pi3ctrl-core.service

sudo systemctl enable pi3ctrl-http.service 
sudo systemctl restart pi3ctrl-http.service

sudo systemctl enable pi3ctrl-wifi.service 
sudo systemctl restart pi3ctrl-wifi.service
