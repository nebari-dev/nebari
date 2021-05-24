from typing import List, Optional
import os
import json

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

class Group(BaseModel):
    groupname: str
    gid: int

class User(BaseModel):
    username: str
    uid: int
    groups: List[Group]

NEXT_UID = 2000
NEXT_GID = 10

# Read in migration users/groups (i.e. hard-coded uid/gid as specified in earlier versions of qhub-config.yaml)

# /etc/migration-state/initial-users.json
# {'user1': {'uid': 1000, 'primary_group': 'admin', 'secondary_groups': ['users'], 'password': ''}, 'user2':...

# /etc/migration-state/initial-groups.json
# {'users': {'gid': 100}, 'admin': {'gid': 101}}

USERS = {}
GROUPS = {}

MIGRATION_FILEPATH_GROUPS = os.environ.get('MIGRATION_FILEPATH_GROUPS', '/etc/migration-state/initial-groups.json')
if os.path.isfile(MIGRATION_FILEPATH_GROUPS):
    with open(MIGRATION_FILEPATH_GROUPS, "rt") as f:
        migration_groups = json.load(f)
        for k, g in migration_groups.items():
            GROUPS[k] = Group(groupname=k, gid=g['gid'])
            if g['gid'] >= NEXT_GID:
                NEXT_GID = g['gid'] + 1

MIGRATION_FILEPATH_USERS = os.environ.get('MIGRATION_FILEPATH_USERS', '/etc/migration-state/initial-users.json')
if os.path.isfile(MIGRATION_FILEPATH_USERS):
    with open(MIGRATION_FILEPATH_USERS, "rt") as f:
        migration_users = json.load(f)
        for k, u in migration_users.items():
            primary_group = u.get('primary_group', 0)
            secondary_groups = u.get('secondary_groups', [])

            usergroups = [GROUPS[gname] for gname in [primary_group] + secondary_groups if gname in GROUPS]
            
            if 'uid' in u and u['uid']:
                USERS[k] = User(username=k, uid=u['uid'], groups=usergroups)
                if u['uid'] >= NEXT_UID:
                    NEXT_UID = u['uid'] + 1

# App

app = FastAPI()

@app.post("/user")
async def putuser(username: str, groupnames: List[str]):
    global NEXT_UID, NEXT_GID

    groups = []
    for groupname in groupnames:
        if not groupname in GROUPS:
            groups.append(GROUPS.setdefault(groupname, Group(groupname=groupname, gid=NEXT_GID)))
            NEXT_GID += 1
        else:
            groups.append(GROUPS[groupname])

    user = USERS.get(username, None)
    if user is None:
        user = User(username=username, uid=NEXT_UID, groups=groups)
        NEXT_UID += 1
        USERS[username] = user
    elif user.groups != groups:
        print("Updating groups")
        user.groups = groups

    return user

#@app.post("/groups")
#async def setgroups(grps: List[Group]):
#    for g in grps:
#        GROUPS[g.groupname] = g
#    return grps

#@app.post("/users")
#async def setusers(usrs: List[User]):
#    for u in usrs:
#        USERS[u.username] = u
#    return usrs

@app.get("/etc/passwd", response_class=PlainTextResponse)
async def getetcpasswd():
    lines = []
    for _, u in USERS.items():
        gid = u.groups[0].gid
        print(u)
        lines.append(f'{u.username}:x:{u.uid}:{gid}:{u.username}:/home/jovyan:/bin/bash')
    return "\n".join(lines)

@app.get("/etc/group", response_class=PlainTextResponse)
async def getetcgroup():
    lines = []
    for _, g in GROUPS.items():
        lines.append(f'{g.groupname}:x:{g.gid}:')
    return "\n".join(lines)
    