import json
import os

import z2jh  # noqa: E402
from kubespawner import KubeSpawner  # noqa: E402
from tornado import gen

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

    def get_packages(conda_prefix):
        try:
            packages = set()
            for filename in os.listdir(os.path.join(conda_prefix, "conda-meta")):
                if filename.endswith(".json"):
                    with open(os.path.join(conda_prefix, "conda-meta", filename)) as f:
                        packages.add(json.load(f).get("name"))
            return packages
        except OSError as e:
            import logging

            logger = logging.getLogger()
            logger.error(f"An issue with a conda environment was encountered.\n{e}")

    def get_conda_prefixes(conda_store_mount):
        for namespace in os.listdir(conda_store_mount):
            if os.path.isdir(os.path.join(conda_store_mount, namespace, "envs")):
                for name in os.listdir(
                    os.path.join(conda_store_mount, namespace, "envs")
                ):
                    yield namespace, name, os.path.join(
                        conda_store_mount, namespace, "envs", name
                    )

    def list_dashboard_environments(conda_store_mount):
        for namespace, name, conda_prefix in get_conda_prefixes(conda_store_mount):
            packages = get_packages(conda_prefix)
            if packages and {"cdsdashboards-singleuser"} <= packages:
                yield namespace, name, conda_prefix

    def conda_environments():
        conda_store_mount = z2jh.get_config("custom.conda-store-mount")
        return [
            name
            for namespace, name, conda_prefix in list_dashboard_environments(
                conda_store_mount
            )
        ]

    c.CDSDashboardsConfig.conda_envs = conda_environments

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
