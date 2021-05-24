from typing import List, Optional

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

USERS = {}

_groups_objs = [
    Group(groupname="admin", gid=101),
    Group(groupname="users", gid=100)
]

GROUPS = dict([(g.groupname, g) for g in _groups_objs])

NEXT_UID = 1000

app = FastAPI()


@app.post("/user")
async def putuser(username: str, groupnames: List[str]):
    global NEXT_UID

    groups = [GROUPS.get(groupname) for groupname in groupnames]

    user = USERS.get(username, None)
    if user is None:
        user = User(username=username, uid=NEXT_UID, groups=groups)
        NEXT_UID += 1
        USERS[username] = user
    elif user.groups != groups:
        print("Updating groups")
        user.groups = groups

    return user

@app.post("/groups")
async def setgroups(grps: List[Group]):
    for g in grps:
        GROUPS[g.groupname] = g
    return grps

@app.post("/users")
async def setusers(usrs: List[User]):
    for u in usrs:
        USERS[u.username] = u
    return usrs

@app.get("/etc/passwd", response_class=PlainTextResponse)
async def getetcpasswd():
    lines = []
    for _, u in USERS.items():
        gid = u.groups[0].gid
        lines.append(f'{u.username}:x:{u.uid}:{gid}:{u.username}:/home/jovyan:/bin/bash')
    return "\n".join(lines)

@app.get("/etc/group", response_class=PlainTextResponse)
async def getetcgroup():
    lines = []
    for _, g in GROUPS.items():
        lines.append(f'{g.groupname}:x:{g.gid}:')
    return "\n".join(lines)
    