from typing import List, Dict
import os
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.logger import logger as fastapi_logger

from pydantic import BaseModel

# Logging is still a mess! This doesn't work...

gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_logger = logging.getLogger("gunicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

fastapi_logger.handlers = gunicorn_error_logger.handlers

if __name__ != "__main__":
    fastapi_logger.setLevel(uvicorn_access_logger.level)
else:
    fastapi_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Group(BaseModel):
    groupname: str
    gid: int
    id: str

class User(BaseModel):
    username: str
    uid: int
    id: str
    groups: List[Group]

class Holdall(BaseModel):
    users: Dict[str, User]
    groups: Dict[str, Group]

    def new_uid(self):
        return 1+max([2000]+[u.uid for _, u in self.users.items()])

    def new_gid(self):
        return 1+max([10]+[g.gid for _, g in self.groups.items()])

HOLDALL = Holdall(users={}, groups={})


# Keycloak config

from keycloak import KeycloakAdmin

class KeycloakStore:
    def __init__(self, server_url, username, password, realm_name):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.realm_name = realm_name
    
    def _get_keycloak_admin(self):
        return KeycloakAdmin(server_url=self.server_url, username=self.username, password=self.password, realm_name=self.realm_name, user_realm_name="master")

    def get_user_groups(self):
        keycloak_admin = self._get_keycloak_admin()

        # [{'id': '2804321d-1b19-4bbb-950b-0b969b91b421', 'createdTimestamp': 1630572243430, 'username': 'dan', 
        # 'enabled': True, 'totp': False, 'emailVerified': False, 'attributes': {'uid': ['100']}, 
        # 'disableableCredentialTypes': [], 'requiredActions': [], 'notBefore': 0, 
        # 'access': {'manageGroupMembership': True, 'view': True, 'mapRoles': True, 'impersonate': True, 'manage': True}}]
        k_users = keycloak_admin.get_users()

        # [{'id': '2bc355e5-e942-46a4-bab3-54c6831542a2', 'name': 'admin', 'path': '/admin', 'subGroups': []}, 
        # {'id': 'd983e73c-a4c1-4ead-8230-ce85035cb0dc', 'name': 'users', 'path': '/users', 'subGroups': []}]
        k_groups = keycloak_admin.get_groups()

        max_gid = 1000
        need_gids = []
        groups = {}

        for kg in k_groups:
            # {'id': '2bc355e5-e942-46a4-bab3-54c6831542a2', 'name': 'admin', 'path': '/admin', 
            # 'attributes': {'gid': ['200']}, 'realmRoles': [], 'clientRoles': {}, 'subGroups': [], 
            # 'access': {'view': True, 'manage': True, 'manageMembership': True}}
            k_group = keycloak_admin.get_group(kg['id'])

            # If no gid, we will need to assign one
            try:
                gid = int(k_group.get('attributes', {}).get('gid', ['0'])[0])
            except ValueError:
                gid = 0
                
            if gid == 0:
                need_gids.append(kg['name'])
            else:
                if gid > max_gid:
                    max_gid = gid

            groups[kg['name']] = {'groupname': kg['name'], 'gid': gid, 'id': kg['id']}

        # Generate new gid for groups that need one
        for groupname in need_gids:
            max_gid += 1
            keycloak_admin.update_group(groups[groupname]['id'], {'attributes': {'gid': [str(max_gid)]}, 'name': groupname})
            groups[groupname]['gid'] = max_gid

        print(groups)

        # Get group members
        user_memberships = {}

        for groupname, group in groups.items():
            members = keycloak_admin.get_group_members(group['id'])
            for u in members:
                username = u['username']
                user_memberships.setdefault(username, []).append(groupname)

        print(user_memberships)

        # Filter users and assign any uids
        users = {}
        max_uid = 1000
        need_uids = []
        for ku in k_users:

            # If no uid, we will need to assign one
            try:
                uid = int(ku.get('attributes', {}).get('uid', ['0'])[0])
            except ValueError:
                uid = 0

            if uid == 0:
                need_uids.append(ku['username'])
            else:
                if uid > max_uid:
                    max_uid = uid

            users[ku['username']] = {'username': ku['username'], 'uid': uid, 'id': ku['id'],
                'groups': [groups[g] for g in user_memberships.get(ku['username'], [])]
                }

        # Generate new uid for users that need one
        for username in need_uids:
            max_uid += 1
            keycloak_admin.update_user(users[username]['id'], {'attributes': {'uid': [str(max_uid)]}})
            users[username]['uid'] = max_uid

        # Get users
        return {'groups': groups, 'users': users}

KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'http://localhost:8080/auth/')
KEYCLOAK_USERNAME = os.environ.get('KEYCLOAK_USERNAME', 'admin')
KEYCLOAK_PASSWORD = os.environ.get('KEYCLOAK_PASSWORD', 'admin')
KEYCLOAK_REALM_NAME = os.environ.get('KEYCLOAK_REALM_NAME', 'qhub')

keycloak_store = KeycloakStore(KEYCLOAK_SERVER_URL, KEYCLOAK_USERNAME, KEYCLOAK_PASSWORD, KEYCLOAK_REALM_NAME)

def refresh_store():
    global HOLDALL
    global keycloak_store
    HOLDALL = Holdall(**keycloak_store.get_user_groups())

refresh_store()

app = FastAPI()

@app.post("/user")
async def putuser(username: str):
    refresh_store()

    user = HOLDALL.users.get(username, None)
    if user is None:
        raise HTTPException(status_code=404, detail=f"{username} not found")

    return user

@app.get("/etc/passwd", response_class=PlainTextResponse)
async def getetcpasswd():
    lines = []
    for _, u in HOLDALL.users.items():
        gid = 0
        if len(u.groups) > 0:
            gid = u.groups[0].gid
        print(u)
        lines.append(f'{u.username}:x:{u.uid}:{gid}:{u.username}:/home/jovyan:/bin/bash')
    return "\n".join(lines)

@app.get("/etc/group", response_class=PlainTextResponse)
async def getetcgroup():
    lines = []
    for _, g in HOLDALL.groups.items():
        lines.append(f'{g.groupname}:x:{g.gid}:')
    logger.info("Writing /etc/group %d lines", len(lines))
    print("print in /etc/groups")
    return "\n".join(lines)
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
