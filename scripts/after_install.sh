#!/usr/bin/env bash
sudo python3 -m pip install -r /webapps/reddit-proxy/requirements.txt
sudo python3 -m pip install -r /webapps/reddit-proxy/logging-requirements.txt
if supervisorctl reread; then
    echo "Supervisor reread succeeded"
else
    echo "Starting up supervisor"
    supervisord -c /webapps/reddit-proxy/cfg/supervisor.conf || :
fi