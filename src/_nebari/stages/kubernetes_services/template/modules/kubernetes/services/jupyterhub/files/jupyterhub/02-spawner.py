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


def get_scoped_token(
    conda_store_url: str,
    admin_token: str,
    name: str,
    groups: list[str] = None,
    admin: bool = False,
):
    """Generate a conda store auth token for a given set of groups. The
    token will only have `view` permissions for each group (regardless if
    the user has higher permissions associated with the group generally).

    If the user is an admin, then the token will have `view` permissions
    for all namespaces.

    By default, the user will have view permissions for the following
    groups:
    - `default/*`
    - `filesystem/*`
    - `nebari-git/*`
    - `global/*`

    Parameters
    ----------
    conda_store_url : str
        The URL of the Conda Store instance.
    admin_token : str
        The admin token used to authenticate with the Conda Store API.
    name : str
        The name of the user for whom the token will be generated (the token
        will have `view` permission to this namespace).
    groups : list[str], optional
        A list of group names that the user should have access to. If not provided,
        default roles will be assigned.
    admin : bool, optional
        Whether the user is an admin. If true, the token will have `view` permissions
        for all namespaces. Defaults to False.

    Returns
    -------
    str
        The generated token.
    """
    import urllib3

    token_endpoint = f"http://{conda_store_url}/conda-store/api/v1/token/"
    http = urllib3.PoolManager()

    # add default role bindings
    role_bindings = {
        "role_bindings": {
            f"{name}/*": ["viewer"],
            "default/*": ["viewer"],
            "filesystem/*": ["viewer"],
            "nebari-git/*": ["viewer"],
            "global/*": ["viewer"],
        }
    }

    # add role bindings for all the groups the user is part of
    if groups is not None:
        for group in groups:
            group = group.replace("/", "")
            role_bindings["role_bindings"][f"{group}/*"] = ["viewer"]

    # if the user is an admin, they can view all namespace + environments
    if admin:
        role_bindings["role_bindings"]["*/*"] = ["viewer"]

    encoded_body = json.dumps(role_bindings)

    # generate a token with with the generated role bindings
    token_response = http.request(
        "POST",
        str(token_endpoint),
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        },
        body=encoded_body,
    )
    token_data = json.loads(token_response.data.decode("UTF-8"))
    return token_data.get("data", {}).get("token")


# TODO: this should get unit tests. Currently, since this is not a python module,
# adding tests in a traditional sense is not possible. See https://github.com/soapy1/nebari/tree/try-unit-test-spawner
# for a demo on one approach to adding test.
def get_conda_store_environments(user_info: dict):
    """Gets the conda-store environments for a given user using the v1 environment
    API.

    This scopes permissions for the given user using the `groups` field in the
    user_info dict. The user_info dict comes from Jupyter's user dict. The groups
    in this dict come from the keycloak groups, which include the list of conda-store
    namespaces the user has access to. For the purpose of this function, we can assume
    that if the user is part of the group, it at least has `view` permissions on the
    conda-store namespaces.

    Parameters
    ----------
    user_info : dict
        A dictionary containing user information originating from the JupyterHub
        user info. The scheme of the user info is:
        ```
        {
            "name": "string",
            "admin": true,
            "roles": [
                "string"
            ],
            "groups": [
                "string"
            ],
            "server": "string",
            "pending": "spawn",
            "last_activity": "2019-08-24T14:15:22Z",
            "servers": {
            },
            "auth_state": {}
        }
        ```

    Returns
    -------
    list[str]
        A list of all conda-store environments for the given user
    """
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

    groups = user_info["groups"]
    name = user_info["name"]
    admin = user_info["admin"]
    # get token with appropriate scope for the user making the request
    scoped_token = get_scoped_token(external_url, token, name, groups, admin)

    # get total number of records from the endpoint
    total_records = get_total_records(base_url, scoped_token)

    # will contain all the environment info returned from the api
    env_data = []

    # generate a list of urls to hit to build the response
    urls = generate_paged_urls(base_url, total_records, page_size)

    http = urllib3.PoolManager()

    # get content from urls
    for url in urls:
        response = http.request(
            "GET", url, headers={"Authorization": f"Bearer {scoped_token}"}
        )
        decoded_response = json.loads(response.data.decode("UTF-8"))
        env_data += decoded_response.get("data", [])

    # Filter and return conda environments for the user
    envs = [f"{env['namespace']['name']}-{env['name']}" for env in env_data]
    return envs


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

    from jhub_apps.service_utils import service_for_jhub_apps

    c.JupyterHub.services.extend(
        [
            service_for_jhub_apps(name="Argo", url="/argo"),
            service_for_jhub_apps(name="Users", url="/auth/admin/nebari/console/"),
            service_for_jhub_apps(
                name="Environments",
                url="/conda-store",
                pinned=True,
                description="This is conda-store, your environments manager.",
                thumbnail="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIGlkPSJMYXllcl8xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0ODMgNDczIj48ZGVmcz48c3R5bGU+LmNscy0xe2ZpbGw6I2ZmZjt9LmNscy0ye2ZpbGw6I2E4ZTI5Zjt9LmNscy0ze2ZpbGw6IzQwYWYyZjt9PC9zdHlsZT48L2RlZnM+PGc+PHBhdGggY2xhc3M9ImNscy0yIiBkPSJNMjY5LjYyLDM3OC4xaC0xNS41MXYtOC41NWgxNS41MXMtMi42NywzLjAzLTIuODQsNGMtLjE3LC45OCwyLjg0LDQuNTUsMi44NCw0LjU1WiIvPjxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTcwLjQ1LDM5NC41OWMtNC45NCwwLTguOTktMS41Ny0xMi4xNS00LjcxLTMuMTYtMy4xNC00Ljc1LTcuMjMtNC43NS0xMi4yNXMxLjYtOS4xMSw0LjgxLTEyLjI1LDcuMzctNC43MSwxMi40OS00LjcxYzIuNzQsMCw1LjM0LC41NCw3LjgxLDEuNjIsMi40NywxLjA4LDQuNTEsMi42Myw2LjEzLDQuNjVsLTUuOTMsNS4xMmMtMi4wMi0yLjMzLTQuNTgtMy41LTcuNjgtMy41LTIuNiwwLTQuNzEsLjg0LTYuMzMsMi41MnMtMi40MiwzLjg1LTIuNDIsNi41LC44Miw0Ljg5LDIuNDYsNi42LDMuNzYsMi41Niw2LjM2LDIuNTZjMy4xNCwwLDUuNy0xLjEyLDcuNjctMy4zN2w1Ljk5LDUuMzJjLTEuNTMsMS43NS0zLjU0LDMuMTgtNi4wMyw0LjI4LTIuNDcsMS4wNy01LjI5LDEuNjItOC40MywxLjYyWiIvPjxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTEwNi43NCwzOTQuNTljLTUuMTYsMC05LjM2LTEuNTktMTIuNTktNC43OC0zLjIzLTMuMTktNC44NS03LjI1LTQuODUtMTIuMTlzMS42Mi05LDQuODUtMTIuMTksNy40My00Ljc4LDEyLjU5LTQuNzgsOS4zMSwxLjU3LDEyLjU5LDQuNzFjMy4yOCwzLjE0LDQuOTIsNy4yMyw0LjkyLDEyLjI1cy0xLjY0LDkuMTEtNC45MiwxMi4yNWMtMy4yNywzLjE2LTcuNDcsNC43My0xMi41OSw0LjczWm0wLTcuODhjMi40MiwwLDQuNDUtLjg1LDYuMDktMi41NnMyLjQ2LTMuODgsMi40Ni02LjUzLS44MS00Ljg4LTIuNDItNi41NmMtMS42Mi0xLjY4LTMuNjYtMi41Mi02LjEzLTIuNTJzLTQuNTcsLjg2LTYuMTYsMi41OS0yLjM5LDMuOS0yLjM5LDYuNSwuODEsNC43MSwyLjQyLDYuNDZjMS42MiwxLjc1LDMuNjYsMi42Miw2LjEzLDIuNjJaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMTUwLjc3LDM2MC42NmM3Ljk5LDAsMTEuOTksNC42MiwxMS45OSwxMy44N3YxOS41MmgtOC44MnYtMTcuM2MwLTMuMDEtLjUyLTUuMTMtMS41NS02LjM2LTEuMDMtMS4yMy0yLjYzLTEuODUtNC43OC0xLjg1LTIuMjksMC00LjExLC43Ny01LjQ1LDIuMzItMS4zNSwxLjU1LTIuMDIsMy43Ni0yLjAyLDYuNjN2MTYuNTZoLTguODJ2LTMyLjg2aDguODJ2NC4yNGguMTNjMi42OS0zLjE4LDYuMTktNC43NywxMC41LTQuNzdaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMTk0Ljk0LDM0NC41aDguODJ2NDkuNTVoLTguNDJ2LTMuOTdoLS4xM2MtMi4zOCwzLjAxLTUuNzUsNC41MS0xMC4xLDQuNTEtNC41OCwwLTguMzUtMS41Ni0xMS4zMS00LjY4cy00LjQ0LTcuMTktNC40NC0xMi4yMiwxLjQ3LTkuMDEsNC40MS0xMi4yMiw2LjYzLTQuODEsMTEuMDctNC44MWM0LjE4LDAsNy40NywxLjQxLDkuOSw0LjI0aC4ydi0yMC40aDBabS0xNC4yNywzOS43MmMxLjU3LDEuNjYsMy41OSwyLjQ5LDYuMDYsMi40OXM0LjUzLS44Myw2LjE5LTIuNDksMi40OS0zLjgxLDIuNDktNi40Ni0uODItNC44NS0yLjQ2LTYuNi0zLjcyLTIuNjMtNi4yMy0yLjYzLTQuNDMsLjg0LTYuMDMsMi41MmMtMS41OSwxLjY4LTIuMzksMy45Mi0yLjM5LDYuNywuMDEsMi42NiwuNzksNC44MSwyLjM3LDYuNDdaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMjM2LjE1LDM2MS4yaDguNzV2MzIuODZoLTguMzV2LTMuOTdoLS4yYy0yLjI5LDMuMDEtNS41Nyw0LjUxLTkuODMsNC41MS00LjU4LDAtOC4zNC0xLjU2LTExLjI4LTQuNjhzLTQuNDEtNy4xOS00LjQxLTEyLjIyLDEuNDctOS4wMSw0LjQxLTEyLjIyLDYuNjMtNC44MSwxMS4wNy00LjgxYzQuMDgsMCw3LjI5LDEuNDEsOS42Myw0LjI0aC4ydi0zLjcxaDBabS04LjAyLDI1LjUxYzIuMzMsMCw0LjMxLS44Myw1LjkzLTIuNDlzMi40Mi0zLjgxLDIuNDItNi40Ni0uNzgtNC44NS0yLjM2LTYuNmMtMS41Ny0xLjc1LTMuNTUtMi42My01LjkzLTIuNjNzLTQuNDQsLjg0LTYuMDYsMi41Mi0yLjQyLDMuOTItMi40Miw2LjcsLjc4LDQuOCwyLjM2LDYuNDZjMS41OCwxLjY3LDMuNiwyLjUsNi4wNiwyLjVaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMjkxLjA5LDM5NC41OWMtNS4xNiwwLTkuNjEtMS41OS0xMy4zMy00Ljc4bDQuMzEtNi4xM2MyLjY5LDIuNTYsNS43MiwzLjg0LDkuMDksMy44NCwxLjI2LDAsMi4yNC0uMjUsMi45Ni0uNzRzMS4wOC0xLjE0LDEuMDgtMS45NWMwLS43Mi0uNDMtMS4zMi0xLjI4LTEuODItLjg1LS40OS0yLjQzLTEuMS00LjcxLTEuODItMy4xOS0xLjA4LTUuNjctMi40MS03LjQ0LTQuMDEtMS43Ny0xLjU5LTIuNjYtMy44My0yLjY2LTYuN3MxLjEyLTUuMjgsMy4zNy03LjFjMi4yNC0xLjgyLDUuMDctMi43Myw4LjQ4LTIuNzMsNC40OSwwLDguNDgsMS4zNywxMS45OCw0LjExbC00LjI0LDYuNDZjLTIuNDctMi4zMy01LjA5LTMuNS03Ljg4LTMuNS0uODEsMC0xLjU1LC4yMS0yLjIyLC42NC0uNjcsLjQzLTEuMDEsMS4wNC0xLjAxLDEuODUsMCwuNjMsLjM5LDEuMiwxLjE4LDEuNzIsLjc4LC41MiwyLjA1LDEuMTEsMy44LDEuNzgsMS43OSwuNjcsMy4xMiwxLjE4LDMuOTcsMS41MnMxLjg2LC44MywzLjAzLDEuNDhjMS4xNywuNjUsMS45OSwxLjI4LDIuNDYsMS44OSwuNDcsLjYxLC45LDEuNCwxLjI4LDIuMzksLjM4LC45OSwuNTcsMi4xMSwuNTcsMy4zNywwLDMuMDUtMS4wOSw1LjUyLTMuMjcsNy40MS0yLjE4LDEuODgtNS4zNSwyLjgyLTkuNTIsMi44MloiLz48cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik0zMjAuODQsMzk0LjU5Yy0yLjkyLDAtNS4yMS0uOTItNi44Ny0yLjc2LTEuNjYtMS44NC0yLjQ5LTQuNTUtMi40OS04LjE1di0xNS4yMmgtMy45MXYtNy4yN2gzLjkxdi0xMC43N2w4Ljc1LS45NHYxMS43MWg4Ljk1djcuMjdoLTguOTV2MTRjMCwyLjc4LC45Nyw0LjE3LDIuODksNC4xNywxLjI2LDAsMi42NS0uMzgsNC4xOC0xLjE0bDIuMjksNy4wN2MtMi41MSwxLjM2LTUuNDIsMi4wMy04Ljc1LDIuMDNaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMzQ5LjgsMzk0LjU5Yy01LjE2LDAtOS4zNi0xLjU5LTEyLjU5LTQuNzgtMy4yMy0zLjE5LTQuODUtNy4yNS00Ljg1LTEyLjE5czEuNjItOSw0Ljg1LTEyLjE5LDcuNDMtNC43OCwxMi41OS00Ljc4LDkuMzEsMS41NywxMi41OSw0LjcxYzMuMjgsMy4xNCw0LjkyLDcuMjMsNC45MiwxMi4yNXMtMS42NCw5LjExLTQuOTIsMTIuMjVjLTMuMjgsMy4xNi03LjQ4LDQuNzMtMTIuNTksNC43M1ptMC03Ljg4YzIuNDIsMCw0LjQ1LS44NSw2LjA5LTIuNTYsMS42NC0xLjcxLDIuNDYtMy44OCwyLjQ2LTYuNTNzLS44MS00Ljg4LTIuNDItNi41NmMtMS42Mi0xLjY4LTMuNjYtMi41Mi02LjEzLTIuNTJzLTQuNTcsLjg2LTYuMTYsMi41OS0yLjM5LDMuOS0yLjM5LDYuNSwuODEsNC43MSwyLjQyLDYuNDZjMS42MiwxLjc1LDMuNjYsMi42Miw2LjEzLDIuNjJaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMzkzLjIyLDM2MC42NmMuMzYsMCwuNTgsLjAyLC42NywuMDd2OS41NmMtLjU4LS4wNC0xLjM1LS4wNy0yLjI5LS4wNy0yLjY1LDAtNC43MSwuOC02LjIsMi4zOS0xLjQ4LDEuNTktMi4yMiwzLjY1LTIuMjIsNi4xNnYxNS4yOGgtOC44MnYtMzIuODZoOC44MnY0Ljg1aC4wN2MyLjU3LTMuNTksNS44OS01LjM4LDkuOTctNS4zOFoiLz48cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Ik00MjkuNDUsMzc3LjI5YzAsMS43NS0uMDcsMi44MS0uMiwzLjE2aC0yMy4wOWMuNTQsMS45OCwxLjU1LDMuNTIsMy4wMyw0LjY1LDEuNDgsMS4xMiwzLjI3LDEuNjgsNS4zOSwxLjY4LDMuMTksLjA0LDUuODEtMS4xOSw3Ljg4LTMuN2w1LjczLDUuMzJjLTMuMjgsNC4xMy04LjAxLDYuMTktMTQuMjEsNi4xOS00Ljg5LDAtOC45My0xLjU3LTEyLjEyLTQuNzEtMy4xOS0zLjE0LTQuNzgtNy4yNS00Ljc4LTEyLjMyczEuNTQtOC45OSw0LjYxLTEyLjE1YzMuMDgtMy4xNiw2Ljk3LTQuNzUsMTEuNjgtNC43NXM4LjYzLDEuNTYsMTEuNjEsNC42OGMyLjk3LDMuMTIsNC40Nyw3LjEsNC40NywxMS45NVptLTE1LjgzLTguODljLTEuODQsMC0zLjQxLC40OS00LjcxLDEuNDgtMS4zLC45OS0yLjIsMi40LTIuNjksNC4yNGgxNC40N2MtLjk4LTMuODEtMy4zNC01LjcyLTcuMDctNS43MloiLz48L2c+PGc+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJNMjMwLjkxLDE5MC41MWMtMjUuMDMtMTMuODItNDkuOTctMjcuNzktNzQuOTctNDEuNjctNy45OC00LjQzLTEzLjU4LTEuMTQtMTMuNTksNy45NS0uMDMsMTQuMywwLDI4LjYsMCw0Mi45MXMuMSwyOC42MS0uMDYsNDIuOTFjLS4wNSw0Ljg4LDEuNjYsOC4wMyw2LjE0LDEwLjI4LDI1LjMsMTIuNzIsNTAuNDksMjUuNjYsNzUuNzQsMzguNDgsNi45MiwzLjUxLDEyLjQ4LC4wMywxMi40OC03LjgxLC4wMy0yNy44LS4wNi01NS41OSwuMDgtODMuMzksLjAzLTQuNjYtMS44NC03LjQ3LTUuODEtOS42NloiLz48cGF0aCBjbGFzcz0iY2xzLTIiIGQ9Ik0yNTIuMDksMTkwLjUxYzI1LjAzLTEzLjgyLDQ5Ljk3LTI3Ljc5LDc0Ljk3LTQxLjY3LDcuOTgtNC40MywxMy41OC0xLjE0LDEzLjU5LDcuOTUsLjAzLDE0LjMsLjAxLDI4LjYsLjAxLDQyLjkxcy0uMSwyOC42MSwuMDYsNDIuOTFjLjA1LDQuODgtMS42Niw4LjAzLTYuMTQsMTAuMjgtMjUuMywxMi43Mi01MC40OSwyNS42Ni03NS43NCwzOC40OC02LjkyLDMuNTEtMTIuNDgsLjAzLTEyLjQ4LTcuODEtLjAzLTI3LjgsLjA2LTU1LjU5LS4wOC04My4zOS0uMDMtNC42NiwxLjg0LTcuNDcsNS44MS05LjY2WiIvPjxwYXRoIGNsYXNzPSJjbHMtMiIgZD0iTTI5MC43NSw3OS44N2gtMTUuNTF2OC41NWgxNS41MXMtMi42Ny0zLjAzLTIuODQtNCwyLjg0LTQuNTUsMi44NC00LjU1WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0iTTI1My45Niw4MS4xNGMyLjI0LC4xLDQuMDYtMS41NSw0LjE3LTMuOCwuMS0yLjI0LTEuNTUtNC4wNC0zLjgxLTQuMTUtMi4yMi0uMTEtNC4xMSwxLjYtNC4yLDMuNzktLjEsMi4yMSwxLjYxLDQuMDYsMy44NCw0LjE2WiIvPjxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTI3Mi45MSwxMTYuMzRjLTEuMy0xLjY3LTMuNTYtMy40MS02Ljc4LTUuMnMtNi4wMS0zLjE2LTguMzYtNC4wOWMtMi4zNi0uOTMtNi4wMS0yLjMyLTEwLjk2LTQuMTgtNC44My0xLjg2LTguMzMtMy41LTEwLjUtNC45MnMtMy4yNS0zLTMuMjUtNC43NGMwLTIuMjMsLjkzLTMuOTMsMi43OS01LjExLDEuNzgtMS4xMywzLjc0LTEuNyw1Ljg3LTEuNzV2LS4wN2M4Ljg0LC41OSwxOS4yMiwxLjYyLDI3LjgsMi4xMywxLjU0LC4wOSwxLjg2LS4zMiwxLjc3LTEuNzYtLjY0LTEwLjU0LTguNjMtMTcuNDgtMTkuMDQtMTkuMi0uODQtLjE0LTEuODctLjI2LTIuOTUtLjM2aDBjLTYuMzMtLjgtMTAuNTctLjI0LTEyLjAxLDAtNy4xOSwuNzYtMTMuMzEsMy4xOC0xOC4zNiw3LjI3LTYuMiw1LjAyLTkuMjksMTEuNTUtOS4yOSwxOS42czIuNDUsMTQuMDksNy4zNCwxOC40OWM0Ljg5LDQuNCwxMS43Myw4LjA4LDIwLjUzLDExLjA2LDYuMzIsMS45OCwxMC42NSwzLjY2LDEzLjAxLDUuMDIsMi4zNSwxLjM2LDMuNTMsMy4wNCwzLjUzLDUuMDIsMCwyLjIzLS45OSw0LjAzLTIuOTgsNS4zOS0xLjk4LDEuMzYtNC43MSwyLjA0LTguMTgsMi4wNC0xLjQ4LDAtMi45NC0uMS00LjM4LS4yOC05LjYyLS43LTE2LjktMS43NS0yNi41Mi0yLjUtMS4zMi0uMS0xLjY2LC4yLTEuNjQsMS41LC4xNiwxMC4xNSw3Ljg5LDE4LjA2LDE3Ljk4LDE5LjQ1LDEuODUsLjI1LDYuNTYsMS4xOCwxMC41MywxLjIyLDEuMjcsLjA4LDIuNTUsLjEyLDMuODUsLjEyLDExLjUyLDAsMjAuMjgtMi42LDI2LjI5LTcuOCw2LjAxLTUuMiw5LjAxLTEyLjAxLDkuMDEtMjAuNDQsMC0zLjQ2LS41My02LjU2LTEuNTgtOS4yOS0xLjA0LTIuNzQtMi4yMi00Ljk0LTMuNTItNi42MVptLTE4LjU5LTQzLjE1YzIuMjYsLjExLDMuOTEsMS45MSwzLjgxLDQuMTUtLjEsMi4yNS0xLjkyLDMuOS00LjE3LDMuOC0yLjIyLS4xLTMuOTQtMS45Ni0zLjg1LTQuMTYsLjEtMi4xOSwxLjk5LTMuODksNC4yMS0zLjc5WiIvPjwvZz48L3N2Zz4K",
            ),
            service_for_jhub_apps(name="Monitoring", url="/monitoring"),
        ]
    )

    c.JupyterHub.template_paths = theme_template_paths

    kwargs = {}
    jhub_apps_signature = inspect.signature(install_jhub_apps)
    if "oauth_no_confirm" in jhub_apps_signature.parameters:
        kwargs["oauth_no_confirm"] = True

    c = install_jhub_apps(c, spawner_to_subclass=KubeSpawner, **kwargs)
