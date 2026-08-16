#!/bin/bash

set -e

python -u manage.py qcluster &
echo $! > /tmp/qcluster.pid

exec python healthcheck.py