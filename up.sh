#!/bin/sh
set -e

cd "$(dirname "$0")"

docker-compose pull -p redfox
docker-compose up -p redfox -d --build --remove-orphans

docker image prune -f -a
