import functools
import os
import tempfile
import typing

import kubernetes.client
import kubernetes.config
import requests

from _nebari.constants import DO_ENV_DOCS
from _nebari.provider.cloud.amazon_web_services import aws_delete_s3_bucket
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from _nebari.utils import check_environment_variables, set_do_environment
from nebari import schema


def check_credentials() -> None:
    required_variables = {
        "DIGITALOCEAN_TOKEN",
        "SPACES_ACCESS_KEY_ID",
        "SPACES_SECRET_ACCESS_KEY",
    }
    check_environment_variables(required_variables, DO_ENV_DOCS)


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
        "DELETE": requests.delete,
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


def kubernetes_versions() -> typing.List[str]:
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    supported_kubernetes_versions = sorted(
        [_["slug"].split("-")[0] for _ in _kubernetes_options()["options"]["versions"]]
    )
    filtered_versions = filter_by_highest_supported_k8s_version(
        supported_kubernetes_versions
    )
    return [f"{v}-do.0" for v in filtered_versions]


def digital_ocean_get_cluster_id(cluster_name):
    clusters = digital_ocean_request("kubernetes/clusters").json()[
        "kubernetes_clusters"
    ]

    cluster_id = None
    for cluster in clusters:
        if cluster["name"] == cluster_name:
            cluster_id = cluster["id"]
            break

    return cluster_id


def digital_ocean_get_kubeconfig(cluster_id: str):
    kubeconfig_content = digital_ocean_request(
        f"kubernetes/clusters/{cluster_id}/kubeconfig"
    ).content

    with tempfile.NamedTemporaryFile(delete=False) as temp_kubeconfig:
        temp_kubeconfig.write(kubeconfig_content)

    return temp_kubeconfig.name


def digital_ocean_delete_kubernetes_cluster(cluster_name: str):
    cluster_id = digital_ocean_get_cluster_id(cluster_name)
    digital_ocean_request(f"kubernetes/clusters/{cluster_id}", method="DELETE")


def digital_ocean_cleanup(config: schema.Main):
    """Delete all Digital Ocean resources created by Nebari."""

    name = config.project_name
    namespace = config.namespace

    cluster_name = f"{name}-{namespace}"
    tf_state_bucket = f"{cluster_name}-terraform-state"
    do_spaces_endpoint = "https://nyc3.digitaloceanspaces.com"

    cluster_id = digital_ocean_get_cluster_id(cluster_name)
    if cluster_id is None:
        return

    kubernetes.config.load_kube_config(digital_ocean_get_kubeconfig(cluster_id))
    api = kubernetes.client.CoreV1Api()

    labels = {"component": "singleuser-server", "app": "jupyterhub"}

    api.delete_collection_namespaced_pod(
        namespace=namespace,
        label_selector=",".join([f"{k}={v}" for k, v in labels.items()]),
    )

    set_do_environment()
    aws_delete_s3_bucket(
        tf_state_bucket, digitalocean=True, endpoint=do_spaces_endpoint
    )
    digital_ocean_delete_kubernetes_cluster(cluster_name)
