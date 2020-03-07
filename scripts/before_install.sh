#!/usr/bin/env bash
sudo yum -y install python3 make glibc-devel gcc patch python3-devel libcurl4-gnutls-dev libxml2-dev libssl-dev postgresql-common postgresql-devel postgresql-client
sudo python3 -m pip install --upgrade pip
rm -rf /webapps/reddit-proxy/src
rm -rf /webapps/reddit-proxy/scripts
rm -rf /webapps/reddit-proxy/cfg
rm -f /webapps/reddit-proxy/requirements.txt
