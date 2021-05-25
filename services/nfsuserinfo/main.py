from typing import List, Dict
import os
import json
import logging

from fastapi import FastAPI
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

class User(BaseModel):
    username: str
    uid: int
    groups: List[Group]

class Holdall(BaseModel):
    users: Dict[str, User]
    groups: Dict[str, Group]

    def new_uid(self):
        return 1+max([2000]+[u.uid for _, u in self.users.items()])

    def new_gid(self):
        return 1+max([10]+[g.gid for _, g in self.groups.items()])

HOLDALL = Holdall(users={}, groups={})

# Read new state if saved

STATE_FOLDER_PATH = os.environ.get('STATE_FOLDER_PATH', '/etc/nfsuserinfo-state')

state_file = os.path.join(STATE_FOLDER_PATH, "state.json")


def read_state():
    global HOLDALL
    with open(state_file, "rt") as f:
        HOLDALL = Holdall(**json.load(f))

def save_state():
    with open(state_file, "wt") as f:
        f.write(HOLDALL.json())

if os.path.isfile(state_file):
    read_state()

# Read in migration users/groups (i.e. hard-coded uid/gid as specified in earlier versions of qhub-config.yaml)

# /etc/migration-state/initial-users.json
# {'user1': {'uid': 1000, 'primary_group': 'admin', 'secondary_groups': ['users'], 'password': ''}, 'user2':...

# /etc/migration-state/initial-groups.json
# {'users': {'gid': 100}, 'admin': {'gid': 101}}

MIGRATION_FILEPATH_GROUPS = os.environ.get('MIGRATION_FILEPATH_GROUPS', '/etc/migration-state/initial-groups.json')
if os.path.isfile(MIGRATION_FILEPATH_GROUPS):
    logger.info(f"Reading migration groups from {MIGRATION_FILEPATH_GROUPS}")
    with open(MIGRATION_FILEPATH_GROUPS, "rt") as f:
        migration_groups = json.load(f)
        for k, g in migration_groups.items():
            HOLDALL.groups[k] = Group(groupname=k, gid=g['gid'])

MIGRATION_FILEPATH_USERS = os.environ.get('MIGRATION_FILEPATH_USERS', '/etc/migration-state/initial-users.json')
if os.path.isfile(MIGRATION_FILEPATH_USERS):
    logger.info(f"Reading migration users from {MIGRATION_FILEPATH_USERS}")
    with open(MIGRATION_FILEPATH_USERS, "rt") as f:
        migration_users = json.load(f)
        for k, u in migration_users.items():
            primary_group = u.get('primary_group', 0)
            secondary_groups = u.get('secondary_groups', [])

            usergroups = [HOLDALL.groups[gname] for gname in [primary_group] + secondary_groups if gname in HOLDALL.groups]
            
            if 'uid' in u and u['uid']:
                HOLDALL.users[k] = User(username=k, uid=u['uid'], groups=usergroups)

# App

save_state()

print("print at startup")

app = FastAPI()

@app.post("/user")
async def putuser(username: str, groupnames: List[str]):
    updated = False

    groups = []
    for groupname in groupnames:
        if not groupname in HOLDALL.groups:
            groups.append(HOLDALL.groups.setdefault(groupname, Group(groupname=groupname, gid=HOLDALL.new_gid())))
            updated = True
        else:
            groups.append(HOLDALL.groups[groupname])

    user = HOLDALL.users.get(username, None)
    if user is None:
        user = User(username=username, uid=HOLDALL.new_uid(), groups=groups)
        HOLDALL.users[username] = user
        updated = True
    elif user.groups != groups:
        print("Updating groups")
        user.groups = groups
        updated = True

    if updated:
        save_state()

    return user

@app.get("/etc/passwd", response_class=PlainTextResponse)
async def getetcpasswd():
    lines = []
    for _, u in HOLDALL.users.items():
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
