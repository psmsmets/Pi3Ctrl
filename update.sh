#!/bin/bash

pip install .

# reset systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed

# restart pi3ctrl services
sudo systemctl restart pi3ctrl-core.service
sudo systemctl restart pi3ctrl-http.service
sudo systemctl start pi3ctrl-wifi.service

# done
exit 0
