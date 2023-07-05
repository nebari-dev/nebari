import json
import os
from functools import partial

import kubernetes.client.models
import urllib3
import yarl
from tornado import gen

kubernetes.client.models.V1EndpointPort = (
    kubernetes.client.models.CoreV1EndpointPort
)  # noqa: E402

import z2jh  # noqa: E402
from kubespawner import KubeSpawner  # noqa: E402


@gen.coroutine
def get_username_hook(spawner):
    auth_state = yield spawner.user.get_auth_state()
    username = auth_state["oauth_user"]["preferred_username"]

    spawner.environment.update(
        {
            "PREFERRED_USERNAME": username,
        }
    )


c.Spawner.pre_spawn_hook = get_username_hook

c.JupyterHub.allow_named_servers = False
c.JupyterHub.spawner_class = KubeSpawner
