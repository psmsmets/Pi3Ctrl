#!/bin/bash

pip install .

sudo systemctl daemon-reload
sudo systemctl reset-failed

sudo systemctl restart pi3ctrl-core.service
sudo systemctl restart pi3ctrl-http.service
