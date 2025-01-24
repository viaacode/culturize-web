#!/usr/bin/env bash

COMPOSE_FILE="docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "docker-compose.yml not found. Can't upgrade this, if on a new install try setup.sh"
    exit 1
fi

CURRENT_SETUP=""
if grep "Dockerfile.swag" $COMPOSE_FILE; then
    CURRENT_SETUP="swag"
else
    CURRENT_SETUP="nginx"
fi

read -r -p "Updating will bring the webservice down for some minutes. Continue? [y/N]: " resp
if [[ -z "$resp" || "$resp" == "n" || "$resp" == "N" ]]; then
    echo "aborting automatic update"
    exit 1
fi

read -r -p "Update script will overwrite current docker-compose.yml. Continue? [y/N]: " resp
if [[ -z "$resp" || "$resp" == "n" || "$resp" == "N" ]]; then
    echo "aborting automatic update"
    exit 1
fi

git pull

echo "Stopping currently running containers"
docker-compose down

if [[ "$CURRENT_SETUP" == "swag" ]]; then
    cp docker-compose.swag.yml docker-compose.yml
else
    cp docker-compose.nginx.yml docker-compose.yml
fi

echo "starting new containers"
docker-compose up -d --build

echo "migrating database"
docker compose exec web python manage.py migrate --noinput

echo "update finished"

