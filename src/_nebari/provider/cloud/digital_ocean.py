import functools
import os

import requests

from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version


def check_credentials():
    DO_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-do"

    for variable in {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "SPACES_ACCESS_KEY_ID",
        "SPACES_SECRET_ACCESS_KEY",
        "DIGITALOCEAN_TOKEN",
    }:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {DO_ENV_DOCS}"""
            )

    if os.environ["AWS_ACCESS_KEY_ID"] != os.environ["SPACES_ACCESS_KEY_ID"]:
        raise ValueError(
            f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must be equal\n
            See {DO_ENV_DOCS} for more information"""
        )

    if (
        os.environ["AWS_SECRET_ACCESS_KEY"]
        != os.environ["SPACES_SECRET_ACCESS_KEY"]
    ):
        raise ValueError(
            f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must be equal\n
            See {DO_ENV_DOCS} for more information"""
        )



def digital_ocean_request(url, method="GET", json=None):
    BASE_DIGITALOCEAN_URL = "https://api.digitalocean.com/v2/"

    for name in {"DIGITALOCEAN_TOKEN"}:
        if name not in os.environ:
            raise ValueError(
                f"Digital Ocean api requests require environment variable={name} defined"
            )

    headers = {"Authorization": f'Bearer {os.environ["DIGITALOCEAN_TOKEN"]}'}

    method_map = {
        "GET": requests.get,
    }

    response = method_map[method](
        f"{BASE_DIGITALOCEAN_URL}{url}", headers=headers, json=json
    )
    response.raise_for_status()
    return response


@functools.lru_cache()
def _kubernetes_options():
    return digital_ocean_request("kubernetes/options").json()


def instances():
    return _kubernetes_options()["options"]["sizes"]


def regions():
    return _kubernetes_options()["options"]["regions"]


def kubernetes_versions(region):
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    supported_kubernetes_versions = sorted(
        [_["slug"] for _ in _kubernetes_options()["options"]["versions"]]
    )
    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)
