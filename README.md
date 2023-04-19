# CultURIze-Web


![logo-culturize-klei-web](https://user-images.githubusercontent.com/14292591/174084481-574397a4-d54b-4359-af57-546eb811b8c1.png)

This is the GitHub repository for CultURIze webservice.

## About

CultURIze webservice is an automated workflow to create and activate persistent URI’s for entities, managed by cultural heritage institutions.

The cultURIze webservice has been built as a multi container docker application. It’s a python django application running inside a container, with a containerised database (PostGreSQL) and nginx as reverse proxy in front of the django application to serve static files. The django application provides multiple endpoints that are linked to different functionalities in the application and all accept JSON data as input.


## Getting Started

### For users
More information about inspiration, governance, and howto's for setting up a Culturize webservice workflow are available on the [Wiki](https://github.com/viaacode/culturize-web/wiki)

### For developers

#### Culturize Web Installation 

We provide a setup script to do most of the configuration work. This can be started with ./setup.sh
and asks some questions before generating the different config files. This setup can also handle the
SSL setup by using Let's Encrypt for certificate management.

A manual install is also possible by following the below steps:

Make sure the server is configure with SSL to ensure communication to and from the webservice is secure.

##### Setting up

* Clone this repo
* Create a environment file called `.env.prod` in the root of the repository.
* Copy paste this inside the `.env.prod` file. Replace "culturize" after `SQL_DATABASE=` and `SQL_PASSWORD=` with your own made up name and password. 
```
DEBUG=1
SECRET_KEY=ruWxpjmdysErePWRKEpckOCCefmIGp
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=culturize-web
SQL_USER=culturize
SQL_PASSWORD=culturize
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres
```
* Create another file at the root of the repo `.env.prod.db`, make sure the username and password from `SQL_DATABASE=` and `SQL_PASSWORD=` are in sync with `POSTGRES_PASSWORD=` and `POSTGRES_DB=` from `.env.prod.`
```
POSTGRES_USER=TheSameUsernameAsYouUsedAtSQL_DATABASEin.env.prod
POSTGRES_PASSWORD=TheSameUsernameAsYouUsedAtSQL_DATABASEin.env.prod
POSTGRES_DB=culturize-web
```
* Replace the default password in the "acceskey" file at 
`culturize-web/app/culturizeweb/accesskey` to something else

##### Installing
Run the two commands below to build and start the webservice.
* `docker-compose -f docker-compose.prod.yml up -d --build`
* `docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput`
After installing running `docker-compose up -f` from the repo can be used to start the Culturize Webservice. 

( If you get "Command 'docker-compose' not found..." you might not have installed Docker-compose or you have installed a newer version and you need to use `docker compose -f docker-compose.prod.yml up -d --build` and `docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput` )

If you get unauthorized access on the last command (manage.py migrate) it can be that you first
created the database container with the wrong credentials. You'll need to remove the attached docker
volume to recreate the database with the correct credentials. You can list the docker volumes with
'docker volume ls' after you identified the database volume (will have db in it's name) you can
remove it with 'docker volume rm <volume-name>'.

##### Starting
In the case culturize-web containers are down, use `docker-compose -f docker-compose.yml up -d` to start the containers. 


## API documentation:

[blob/master/openapi-spec.yml ](https://github.com/viaacode/culturize-web/blob/master/openapi-spec.yml) 

https://editor.swagger.io/ can be used to view the documentation file. 

The cultURIze API supports the following functions

**List all records**

`curl -s https://culturize.web.example.com/api/record -H
"Culturize-Key: meemoosecretbeerstash"`

**Add record**

`curl -X POST https://culturize.web.example.com/api/record -d
'[{"resource_url": "https://meemoo.be/kennisbanken", "persistent_url":
"culturize.data/abc-123"}]' -H "Content-Type: Application/JSON" -H "Culturize-Key: meemoosecretbeerstash"`

**Add multiple records**

`curl -X POST https://culturize.web.example.com/api/record -d
'[{"resource_url": "https://meemoo.be/kennisbanken", "persistent_url":
"culturize.data/abc-123"}, {“resource_url”: “https://example.com”, “persistent_url”: “culturize.data/123-abc”]' -H "Content-Type: Application/JSON" -H "Culturize-Key: meemoosecretbeerstash"`

**Disable record**

`curl -X POST https://culturize.web.example.com/api/record -d '[{"resource_url": "https://meemoo.be/kennisbanken", "enabled": false, "persistent_url": "culturize.data/abc-123"}]' -H "Content-Type: Application/JSON" -H "Culturize-Key: meemoosecretbeerstash"
**Print logs**
curl -s https://culturize.douwe.linuxbe.com/api/logs --header
"Culturize-Key: meemoosecretbeerstash"`

When the Webservice has activated a persistent URI, it produces a respons

`[{"resource_url":"https://meemoo.be/kennisbanken","persistent_url":"culturize.data/abc-123"}]l`



