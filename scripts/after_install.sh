#!/usr/bin/env bash
sudo python3 -m pip install -r /webapps/reddit-proxy/requirements.txt
sudo python3 -m pip install -r /webapps/reddit-proxy/logging-requirements.txt
if sudo /usr/local/bin/supervisorctl reread; then
    echo "Supervisor reread succeeded"
else
    echo "Starting up supervisor"
    source /home/ec2-user/secrets.sh
    sudo -E /usr/local/bin/supervisord -c /webapps/reddit-proxy/cfg/supervisor.conf || :
fi