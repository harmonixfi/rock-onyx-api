#!/bin/sh -e

cd $(dirname $0)

if [ -z ${TZ+x} ]; then
  echo "TZ environment variable must be set"
  exit 1
fi

date
exec /usr/local/bin/supercronic /app/crontab