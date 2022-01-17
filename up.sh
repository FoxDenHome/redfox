#!/bin/sh
set -e

cd "$(dirname "$0")"

docker-compose -p redfox pull
docker-compose -p redfox up -d --build --remove-orphans

docker image prune -f -a
