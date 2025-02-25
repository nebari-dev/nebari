import inspect
import json

import kubernetes.client.models
from tornado import gen

kubernetes.client.models.V1EndpointPort = (
    kubernetes.client.models.CoreV1EndpointPort
)  # noqa: E402

from kubespawner import KubeSpawner  # noqa: E402

# conda-store default page size
DEFAULT_PAGE_SIZE_LIMIT = 100


@gen.coroutine
def get_username_hook(spawner):
    auth_state = yield spawner.user.get_auth_state()
    username = auth_state["oauth_user"]["preferred_username"]

    spawner.environment.update(
        {
            "PREFERRED_USERNAME": username,
        }
    )


def get_total_records(url: str, token: str) -> int:
    import urllib3

    http = urllib3.PoolManager()
    response = http.request("GET", url, headers={"Authorization": f"Bearer {token}"})
    decoded_response = json.loads(response.data.decode("UTF-8"))
    return decoded_response.get("count", 0)


def generate_paged_urls(base_url: str, total_records: int, page_size: int) -> list[str]:
    import math

    urls = []
    # pages starts at 1
    for page in range(1, math.ceil(total_records / page_size) + 1):
        urls.append(f"{base_url}?size={page_size}&page={page}")

    return urls


# TODO: this should get unit tests. Currently, since this is not a python module,
# adding tests in a traditional sense is not possible. See https://github.com/soapy1/nebari/tree/try-unit-test-spawner
# for a demo on one approach to adding test.
def get_conda_store_environments(user_info: dict):
    import os

    import urllib3

    # Check for the environment variable `CONDA_STORE_API_PAGE_SIZE_LIMIT`. Fall
    # back to using the default page size limit if not set.
    page_size = os.environ.get(
        "CONDA_STORE_API_PAGE_SIZE_LIMIT", DEFAULT_PAGE_SIZE_LIMIT
    )

    external_url = z2jh.get_config("custom.conda-store-service-name")
    token = z2jh.get_config("custom.conda-store-jhub-apps-token")
    endpoint = "conda-store/api/v1/environment"

    base_url = f"http://{external_url}/{endpoint}/"
    http = urllib3.PoolManager()

    # get total number of records from the endpoint
    total_records = get_total_records(base_url, token)

    # will contain all the environment info returned from the api
    env_data = []

    # generate a list of urls to hit to build the response
    urls = generate_paged_urls(base_url, total_records, page_size)

    # get content from urls
    for url in urls:
        response = http.request(
            "GET", url, headers={"Authorization": f"Bearer {token}"}
        )
        decoded_response = json.loads(response.data.decode("UTF-8"))
        env_data += decoded_response.get("data", [])

    # Filter and return conda environments for the user
    return [f"{env['namespace']['name']}-{env['name']}" for env in env_data]


c.Spawner.pre_spawn_hook = get_username_hook

c.JupyterHub.allow_named_servers = False
c.JupyterHub.spawner_class = KubeSpawner

if z2jh.get_config("custom.jhub-apps-enabled"):
    from jhub_apps import theme_template_paths
    from jhub_apps.configuration import install_jhub_apps

    domain = z2jh.get_config("custom.external-url")
    hub_url = f"https://{domain}"
    c.JupyterHub.bind_url = hub_url
    c.JupyterHub.default_url = "/hub/home"
    c.Spawner.debug = True

    c.JAppsConfig.conda_envs = get_conda_store_environments
    c.JAppsConfig.jupyterhub_config_path = (
        "/usr/local/etc/jupyterhub/jupyterhub_config.py"
    )
    c.JAppsConfig.hub_host = "hub"
    c.JAppsConfig.service_workers = 4

    jhub_apps_overrides = json.loads(z2jh.get_config("custom.jhub-apps-overrides"))
    for config_key, config_value in jhub_apps_overrides.items():
        setattr(c.JAppsConfig, config_key, config_value)

    def service_for_jhub_apps(name, url):
        return {
            "name": name,
            "display": True,
            "info": {
                "name": name,
                "url": url,
                "external": True,
            },
        }

    c.JupyterHub.services.extend(
        [
            service_for_jhub_apps(name="Argo", url="/argo"),
            service_for_jhub_apps(name="Users", url="/auth/admin/nebari/console/"),
            service_for_jhub_apps(name="Environments", url="/conda-store"),
            service_for_jhub_apps(name="Monitoring", url="/monitoring"),
        ]
    )

    c.JupyterHub.template_paths = theme_template_paths

    kwargs = {}
    jhub_apps_signature = inspect.signature(install_jhub_apps)
    if "oauth_no_confirm" in jhub_apps_signature.parameters:
        kwargs["oauth_no_confirm"] = True

    c = install_jhub_apps(c, spawner_to_subclass=KubeSpawner, **kwargs)
