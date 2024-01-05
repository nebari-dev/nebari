import kubernetes.client.models
from tornado import gen

kubernetes.client.models.V1EndpointPort = (
    kubernetes.client.models.CoreV1EndpointPort
)  # noqa: E402

from kubespawner import KubeSpawner  # noqa: E402
from jhub_apps.configuration import install_jhub_apps


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
c.JupyterHub.bind_url = "https://jamit.quansight.dev/"
# c.JAppsConfig.python_exec = "/home/conda/aktech/envs/aktech-japps/bin/python"
c.JAppsConfig.conda_envs = [
    "aktech-japps",
    "nebari-git-dashboard",
    "nebari-git-dask",
    "base",
    "default",
]

c.JAppsConfig.jupyterhub_config_path = "/usr/local/etc/jupyterhub/jupyterhub_config.py"

c = install_jhub_apps(c, spawner_to_subclass=KubeSpawner)
c.JupyterHub.log_level = 10
c.JupyterHub.log_level = "DEBUG"
c.Spawner.debug = True
