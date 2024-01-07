
import kubernetes.client.models
from tornado import gen

kubernetes.client.models.V1EndpointPort = (
    kubernetes.client.models.CoreV1EndpointPort
)  # noqa: E402

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


def get_conda_store_environments(query_package: str = ""):
    import urllib3
    import yarl

    external_url = z2jh.get_config("custom.conda-store-service-name")
    token = z2jh.get_config("custom.conda-store-jhub-apps-token")
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
    return [f"{env['namespace']['name']}-{env['name']}" for env in j.get("data", [])]


c.Spawner.pre_spawn_hook = get_username_hook

c.JupyterHub.allow_named_servers = False
c.JupyterHub.spawner_class = KubeSpawner

if z2jh.get_config("custom.jhub-apps-enabled"):
    from jhub_apps import theme_template_paths
    from jhub_apps.configuration import install_jhub_apps

    domain = z2jh.get_config("custom.external-url")
    hub_url = f"https://{domain}"
    c.JupyterHub.bind_url = hub_url
    c.JupyterHub.log_level = 10
    c.JupyterHub.log_level = "DEBUG"
    c.Spawner.debug = True

    c.JAppsConfig.conda_envs = get_conda_store_environments
    c.JAppsConfig.python_exec = "/home/conda/aktech/envs/aktech-aktech-japps/bin/python"
    c.JAppsConfig.jupyterhub_config_path = (
        "/usr/local/etc/jupyterhub/jupyterhub_config.py"
    )
    c.JAppsConfig.hub_host = "hub"

    def service_for_jhub_apps(name, url):
        return {
            "name": name,
            "url": hub_url,
            "display": True,
            "info": {
                "name": name,
                "url": url,
                "external": True,
            },
            "oauth_no_confirm": True,
        }


    c.JupyterHub.services.extend([
        service_for_jhub_apps(name="JupyterLab", url="/user/[USER]/lab"),
        service_for_jhub_apps(name="Argo", url="/argo"),
        service_for_jhub_apps(name="Users", url="/auth/admin/nebari/console/"),
        service_for_jhub_apps(name="Environments", url="/conda-store"),
        service_for_jhub_apps(name="Monitoring", url="/monitoring"),
    ])
    c = install_jhub_apps(c, spawner_to_subclass=KubeSpawner)
