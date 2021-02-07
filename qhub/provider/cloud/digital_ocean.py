import os
import functools

import requests


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


def kubernetes_versions():
    return _kubernetes_options()["options"]["versions"]
