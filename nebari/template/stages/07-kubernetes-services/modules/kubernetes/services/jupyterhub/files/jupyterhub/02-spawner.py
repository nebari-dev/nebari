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

cdsdashboards = z2jh.get_config("custom.cdsdashboards")


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

if cdsdashboards["enabled"]:
    from cdsdashboards.app import CDS_TEMPLATE_PATHS
    from cdsdashboards.builder.kubebuilder import KubeBuilder
    from cdsdashboards.hubextension import cds_extra_handlers
    from cdsdashboards.hubextension.spawners.variablekube import VariableKubeSpawner

    c.JupyterHub.allow_named_servers = True
    c.JupyterHub.extra_handlers.extend(cds_extra_handlers)
    c.JupyterHub.template_paths.extend(CDS_TEMPLATE_PATHS)
    c.JupyterHub.spawner_class = VariableKubeSpawner
    c.CDSDashboardsConfig.builder_class = KubeBuilder
    c.VariableMixin.default_presentation_cmd = [
        "python3",
        "-m",
        "jhsingle_native_proxy.main",
    ]
    c.JupyterHub.default_url = "/hub/home"

    # Force dashboard creator to select an instance size
    c.CDSDashboardsConfig.spawn_default_options = False

    def get_conda_store_environments(query_package: str = ""):
        external_url = z2jh.get_config("custom.conda-store-service-name")
        token = z2jh.get_config("custom.conda-store-cdsdashboards")
        endpoint = "conda-store/api/v1/environment"

        url = yarl.URL(f"http://{external_url}/{endpoint}/")

        if query_package:
            url = url % {"packages": query_package}

        http = urllib3.PoolManager()
        response = http.request(
            "GET", str(url), headers={"Authorization": f"Bearer {token}"}
        )

        # parse response
        j = json.loads(response.data.decode("UTF-8"))
        return [
            f"{env['namespace']['name']}-{env['name']}" for env in j.get("data", [])
        ]

    c.CDSDashboardsConfig.conda_envs = partial(
        get_conda_store_environments, query_package="cdsdashboards-singleuser"
    )

    # TODO: make timeouts configurable
    c.VariableMixin.proxy_ready_timeout = 600
    c.VariableMixin.proxy_request_timeout = 600

    home_username = f"/home/{os.getenv('PREFERRED_USERNAME')}"
    c.CDSDashboardsConfig.extra_presentation_types = ["panel-serve"]
    c.VariableMixin.extra_presentation_launchers = {
        "panel-serve": {
            "args": [
                "python3",
                "{presentation_path}",
                "{--}port",
                "{port}",
                "{--}address",
                "{origin_host}",
            ],
            "debug_args": [],
            "env": {"PYTHONPATH": f"{home_username}/{{presentation_dirname}}"},
        }
    }

else:
    c.JupyterHub.allow_named_servers = False
    c.JupyterHub.spawner_class = KubeSpawner
