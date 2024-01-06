import os
import uuid

import kubernetes.client.models
from tornado import gen

kubernetes.client.models.V1EndpointPort = (
    kubernetes.client.models.CoreV1EndpointPort
)  # noqa: E402

from kubespawner import KubeSpawner  # noqa: E402
from jhub_apps.configuration import install_jhub_apps
from jhub_apps import theme_template_paths


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
hub_url = "https://jamit.quansight.dev/"
c.JupyterHub.bind_url = hub_url
# c.JAppsConfig.python_exec = "/home/conda/aktech/envs/aktech-japps/bin/python"
c.JAppsConfig.conda_envs = [
    "aktech-japps",
    "nebari-git-dashboard",
    "nebari-git-dask",
    "base",
    "default",
]

c.JAppsConfig.jupyterhub_config_path = "/usr/local/etc/jupyterhub/jupyterhub_config.py"

os.environ["JWT_SECRET_KEY"] = uuid.uuid4().hex
c = install_jhub_apps(c, spawner_to_subclass=KubeSpawner)
c.JupyterHub.log_level = 10
c.JupyterHub.log_level = "DEBUG"
c.Spawner.debug = True

c.JupyterHub.template_paths = theme_template_paths
c.JupyterHub.services.extend(
    [
        {
            "name": "JuypterLab",
            "url": hub_url,
            "display": True,
            "info": {
                "name": "JupyterLab",
                "url": "/user/[USER]/lab",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
        {
            "name": "Argo",
            "url": hub_url,
            "display": True,
            "info": {
                "name": "Argo Workflows",
                "url": "/hub/argo",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
        {
            "name": "Users",
            "url": hub_url,
            "display": True,
            "info": {
                "name": "User Management",
                "url": "/auth/admin/nebari/console/",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
        {
            "name": "Environments",
            "url": hub_url,
            "display": True,
            "info": {
                "name": "Environments",
                "url": "/hub/conda-store",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
        {
            "name": "Monitoring",
            "url": hub_url,
            "display": True,
            "info": {
                "name": "Monitoring",
                "url": "/hub/monitoring",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
        {
            "name": "MLflow",
            "url": "http://mlflow.mlflow:5000",
            "display": True,
            "info": {
                "name": "MLflow",
                "url": "http://mlflow.mlflow:5000",
                "external": True,
            },
            "oauth_no_confirm": True,
        },
    ]
)

# nebari will control these as ways to customize the template
c.JupyterHub.template_vars = {
    "hub_title": "Welcome to Nebari",
    "hub_subtitle": "your open source data science platform",
    "welcome": "Running in dev mode",
    "logo": "/services/japps/static/img/Nebari-Logo-Horizontal-Lockup-White-text.svg",
    "primary_color": "#C316E9",
    "primary_color_dark": "#79158a",
    "secondary_color": "#18817A",
    "secondary_color_dark": "#12635E",
    "accent_color": "#eda61d",
    "accent_color_dark": "#a16d14",
    "text_color": "#1c1d26",
    "h1_color": "#0f1015",
    "h2_color": "#0f1015",
    "navbar_text_color": "#ffffff",
    "navbar_hover_color": "#20b1a8",
    "navbar_color": "#1c1d26",
}
