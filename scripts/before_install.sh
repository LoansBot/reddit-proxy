#!/usr/bin/env bash
sudo yum -y install python3 make glibc-devel gcc patch python3-devel libcurl4-gnutls-dev libxml2-dev libssl-dev postgresql-common postgresql-devel postgresql-client
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install supervisor
sudo /usr/local/bin/supervisorctl stop all || :
sudo pkill -F /webapps/reddit-proxy/src/supervisord.pid || :
rm -rf /webapps/reddit-proxy/src
rm -rf /webapps/reddit-proxy/scripts
rm -rf /webapps/reddit-proxy/cfg
rm -f /webapps/reddit-proxy/requirements.txt
rm -f /webapps/reddit-proxy/logging-requirements.txt