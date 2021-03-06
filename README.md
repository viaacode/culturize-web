# CultURIze-Web
A Culturize web service to publish PURI's 

![logo-culturize-klei-web](https://user-images.githubusercontent.com/14292591/174084481-574397a4-d54b-4359-af57-546eb811b8c1.png)

The cultURIze webservice has been built as a multi container docker application. It’s a python django application running inside a container, with a containerised database (PostGreSQL) and nginx as reverse proxy in front of the django application to serve static files. The django application provides multiple endpoints that are linked to different functionalities in the application and all accept JSON data as input.

## Api documentation:

[blob/master/openapi-spec.yml ](https://github.com/viaacode/culturize-web/blob/master/openapi-spec.yml) 

https://editor.swagger.io/ can be used to view the documentation file. 

The cultURIze API supports the following functions

**List all records**

`curl -s https://culturize.web.example.com/api/record -H
"Culturize-Key: meemoosecretbeerstash"`

**Add record**

`curl -X POST https://culturize.web.example.com/api/record -d
'[{"resource_url": "https://meemoo.be/kennisbanken", "persistent_url":
"culturize.data/abc-123"}]' -H "Content-Type: Application/JSON" -H`

**Add multiple records**

`curl -X POST https://culturize.web.example.com/api/record -d
'[{"resource_url": "https://meemoo.be/kennisbanken", "persistent_url":
"culturize.data/abc-123"}, {“resource_url”: “https://example.com”, “persistent_url”: “culturize.data/123-abc”]' -H "Content-Type: Application/JSON" -H`

**Disable record**

`curl -X POST https://culturize.web.example.com/api/record -d '[{"resource_url": "https://meemoo.be/kennisbanken", "enabled": false, "persistent_url": "culturize.data/abc-123"}]' -H "Content-Type: Application/JSON" -H "Culturize-Key: meemoosecretbeerstash"
**Print logs**
curl -s https://culturize.douwe.linuxbe.com/api/logs --header
"Culturize-Key: meemoosecretbeerstash"`

When the Webservice has activated a persistent URI, it produces a respons

`[{"resource_url":"https://meemoo.be/kennisbanken","persistent_url":"culturize.data/abc-123"}]l`

## Culturize Web Installation 

Make sure the server is configure with SSL to ensure communication to and from the webservice is secure.

### Setting up

* Clone this repo
* Create a environment file called `.env.prod` in the root of the repository.
* Copy paste this inside the `.env.prod` file. Replace "culturize" after `SQL_DATABASE=` and `SQL_PASSWORD=` with your own made up username and password. 
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
POSTGRES_PASSWORD=culturize
POSTGRES_DB=culturize-web
```
* Paste a password in the "acceskey" file at 
`culturize-web/app/culturizeweb/accesskey`

### Installing
Run the two commands below to build and start the webservice.
* `docker-compose -f docker-compose.prod.yml up -d --build`
* `docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput`
After installing running `docker-compose up -f` from the repo can be used to start the Culturize Webservice. 






