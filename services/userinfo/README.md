# Run Locally

Start server:
```
cd services/userinfo
export MIGRATION_FILEPATH_GROUPS=`pwd`/example-initial-groups.json
export MIGRATION_FILEPATH_USERS=`pwd`/example-initial-users.json
export STATE_FOLDER_PATH=`pwd`/state
python main.py
```

Get/Set users to obtain existing or new uids:
```
curl 'http://localhost:8000/user?username=dan' -H 'Content-Type: application/json' -d '["admin","users"]'
curl 'http://localhost:8000/user?username=bob' -H 'Content-Type: application/json' -d '["users"]'
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
