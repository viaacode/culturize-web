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
else
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

cat << EOF
Culturize-web can check if resource URL are still online and report any resources that went offline.
EOF
read -r -p "Should cultURIze-web check the resource URL's? [Y/n]: " resp
if [[ -z "$resp" || "$resp" == "Y" || "$resp" == "y" ]]; then
    use_checker=true
else
    use_checker=false
fi

if [[ "$use_checker" == true ]]; then
    echo "URL_MONITORING_ENABLED=true" >> .env.web
    read -r -p "Monitoring interval configuration (cron style, default: 1 1 * * *)? [empty for default]: " resp
    if [[ -z "$resp" ]]; then
        echo "URL_MONITORING_FREQUENCY=1 1 * * *" >> .env.web
    else
        echo "URL_MONITORING_FREQUENCY=$resp" >> .env.web
    fi

    read -r -p "Monitoring rate limit configuration (max requests per second, 10 default)? [empty for default]: " resp
    if [[ -z "$resp" ]]; then
        echo "URL_MONITORING_RATE_LIMIT=10" >> .env.web
    else
        echo "URL_MONITORING_RATE_LIMIT=$resp" >> .env.web
    fi

    read -r -p "Should cultURIze-web report (mail) broken links? [Y/n]: " resp
    if [[ -z "$resp" || "$resp" == "Y" || "$resp" == "y" ]]; then
        use_reporter=true
    else
        use_reporter=false
    fi

    if [[ "$use_reporter" == true ]]; then
        echo "URL_MONITORING_REPORTING_ENABLED=true" >> .env.web
        read -r -p "Email subject line? [${domain_name} URL check failures]" resp
        if [[ -z "$resp" ]]; then
            echo "URL_MONITORING_REPORTING_EMAIL_SUBJECT=$domain_name URL check failures" >> .env.web
        else
            echo "URL_MONITORING_REPORTING_EMAIL_SUBJECT=$resp" >> .env.web
        fi

        read -r -p "Email host (SMTP endpoint)?: " resp
        if [[ -z "$resp" ]]; then
            echo "no email host given, abort"
            exit 1
        else
            echo "EMAIL_HOST=$resp" >> .env.web
        fi

        read -r -p "Email host user?: " resp
        if [[ -z "$resp" ]]; then
            echo "no email host user given, abort"
            exit 1
        else
            echo "EMAIL_HOST_USER=$resp" >> .env.web
        fi

        read -r -p "Email host password?: " resp
        if [[ -z "$resp" ]]; then
            echo "no email host password given, abort"
            exit 1
        else
            echo "EMAIL_HOST_PASSWORD=$resp" >> .env.web
        fi

        read -r -p "Email port?: " resp
        if [[ -z "$resp" ]]; then
            echo "no email port given, abort"
            exit 1
        else
            echo "EMAIL_PORT=$resp" >> .env.web
        fi
    fi
fi


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
