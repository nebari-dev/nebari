# Run Locally

First you need to run Keycloak (see below), setting env vars if not using defaults

Start server:
```
cd services/userinfo
python main.py
```

Get/Set users to obtain existing or new uids:
```
curl 'http://localhost:8000/user?username=dan' -H 'Content-Type: application/json'
curl 'http://localhost:8000/user?username=bob' -H 'Content-Type: application/json'
```

Obtain passwd and group files:
```
curl http://localhost:8000/etc/passwd
curl http://localhost:8000/etc/group
```

To build as Docker image:
```
docker build -t quansight/qhub-userinfo:3 .
```

# Keycloak

Run as local Docker container:
```
docker run -p 8080:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin -e KEYCLOAK_LOGLEVEL=DEBUG quay.io/keycloak/keycloak:14.0.0
```

## Curl

Login to http://localhost:8080/ admin console with admin/admin, create 'qhub' realm.

To access Keycloak REST API (see https://www.appsdeveloperblog.com/keycloak-rest-api-create-a-new-user/)
There are two ways to get an access token:

Method one - password grant:
```
curl --location --request POST 'http://localhost:8080/auth/realms/master/protocol/openid-connect/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'username=admin' \
--data-urlencode 'password=admin' \
--data-urlencode 'grant_type=password' \
--data-urlencode 'client_id=admin-cli'
```

Method two - client credentials grant:

Client Credentials grant type allows us to request an admin access token by providing client-id and client-secret instead of an admin username and password. To be able to use this approach, the OAuth 2 Client application called 'admin-cli' that is in the 'master' Keycloak realm, needs to be set to 'confidential'. (Through the web console.)

Then using client credentials obtained from the web console:
```
curl --location --request POST 'http://localhost:8080/auth/realms/master/protocol/openid-connect/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'client_id=admin-cli' \
--data-urlencode 'client_secret=7fb49e15-2a86-4b7c-a648-27746c67895b'
```

## Python

```
pip install python-keycloak
```

[https://github.com/marcospereirampj/python-keycloak](https://github.com/marcospereirampj/python-keycloak)

```
keycloak_admin = KeycloakAdmin(server_url="http://localhost:8080/auth/", username="admin", password="admin", realm_name="qhub", user_realm_name="master")

keycloak_admin.get_groups()

keycloak_admin.create_realm(payload={"realm": "qhub"}, skip_exists=False)

keycloak_admin.get_users()
```