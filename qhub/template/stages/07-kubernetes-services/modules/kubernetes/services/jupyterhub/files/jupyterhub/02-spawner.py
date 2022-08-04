# remove after next kubespawner release past 1/20/2022
# https://github.com/jupyterhub/kubespawner/pull/558
import os

import kubernetes.client.models
from tornado import gen

kubernetes.client.models.V1EndpointPort = kubernetes.client.models.CoreV1EndpointPort

import z2jh  # noqa: E402
from kubespawner import KubeSpawner  # noqa: E402

cdsdashboards = z2jh.get_config("custom.cdsdashboards")
conda_store_environments = z2jh.get_config("custom.environments")


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

    c.CDSDashboardsConfig.conda_envs = [
        environment["name"] for _, environment in conda_store_environments.items()
    ]

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
