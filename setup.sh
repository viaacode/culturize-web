#!/usr/bin/env bash

debugflag=0
database="postgres"
sql_engine="django.db.backends.postgresql"
sql_host="db" # docker compose makes service name available as dns name
sql_port=5432
sql_database="culturize"
sql_user="culturize"
secret_key=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 25)
echo "secret key generated"
sql_password=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 20)
echo "SQL password generated"

read -r -p "Enter api/login key or leave empty for auto generation: " resp
if [[ -z "$resp" ]]; then
    api_accesskey=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 20)
    echo "api/login key generated"
else
    api_accesskey=$resp
fi

read -r -p "Specify the domain name on which culturize-web will be hosted: " resp
if [[ -z "$resp" ]]; then
    echo "empty domain name not supported"
    exit 1
else
    domain_name=$resp
    echo "configuring for ${domain_name}"
fi

cat << EOF
Culturize-web can manage the HTTPS certificate setup via Let's Encrypt if it's the only service
hosted on this domain name (${domain_name}). If multiple services (discouraged) are running on
this domain name some sort of reverse proxy needs to handle the incomming requests and route
them to the corresponding service. This reverse proxy then also needs to handle the HTTPS setup.
EOF
read -r -p "Should cultURIze-web handle the HTTPS traffic? [Y/n]: " resp
if [[ -z "$resp" || "$resp" == "Y" || "$resp" == "y" ]]; then
    use_swag=true
elif [[ "$resp" == "n" || "$resp" == "N" ]]; then
    use_swag=false
fi


echo ${api_accesskey} > app/culturizeweb/accesskey


echo "DEBUG=${debugflag}" > .env.web
echo "SECRET_KEY=${secret_key}" >> .env.web
echo "DJANGO_ALLOWED_HOSTS=${domain_name}" >> .env.web
echo "SQL_ENGINE=${sql_engine}" >> .env.web
echo "SQL_DATABASE=${sql_database}" >> .env.web
echo "SQL_USER=${sql_user}" >> .env.web
echo "SQL_PASSWORD=${sql_password}" >> .env.web
echo "SQL_HOST=${sql_host}" >> .env.web
echo "SQL_PORT=${sql_port}" >> .env.web
echo "DATABASE=${database}" >> .env.web


echo "POSTGRES_USER=${sql_user}" > .env.db
echo "POSTGRES_PASSWORD=${sql_password}" >> .env.db
echo "POSTGRES_DB=${sql_database}" >> .env.db


if [[ "$use_swag" == true ]]; then
    echo "VALIDATION=http" > .env.nginx
    echo "URL=${domain_name}" >> .env.nginx
    echo "SUBDOMAINS=www" >> .env.nginx

    cp docker-compose.swag.yml docker-compose.yml
else
    cp docker-compose.nginx.yml docker-compose.yml
fi

cat << EOF
Setup finished. Use this to build and run the docker containers:

    docker-compose up -d --build

Then do the initial database creation:

    docker-compose exec web python manage.py migrate --noinput
EOF
