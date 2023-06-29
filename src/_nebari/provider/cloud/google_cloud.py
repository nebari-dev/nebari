import os
import functools
import json
import subprocess

from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version


def check_credentials():
    GCP_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-gcp"
    for variable in {"GOOGLE_CREDENTIALS"}:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {GCP_ENV_DOCS}"""
            )



@functools.lru_cache()
def projects():
    output = subprocess.check_output(["gcloud", "projects", "list", "--format=json"])
    data = json.loads(output.decode("utf-8"))
    return {_["name"]: _["projectId"] for _ in data}


@functools.lru_cache()
def regions(project):
    output = subprocess.check_output(
        ["gcloud", "compute", "regions", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data}


@functools.lru_cache()
def zones(project, region):
    output = subprocess.check_output(
        ["gcloud", "compute", "zones", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data if _["name"].startswith(region)}


@functools.lru_cache()
def kubernetes_versions(region):
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    output = subprocess.check_output(
        [
            "gcloud",
            "container",
            "get-server-config",
            "--region",
            region,
            "--format=json",
        ]
    )
    data = json.loads(output.decode("utf-8"))
    supported_kubernetes_versions = sorted([_ for _ in data["validMasterVersions"]])
    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)


@functools.lru_cache()
def instances(project):
    output = subprocess.check_output(
        [
            "gcloud",
            "compute",
            "machine-types",
            "list",
            "--project",
            project,
            "--format=json",
        ]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data}


# Getting pricing data could come from here
# https://cloudpricingcalculator.appspot.com/static/data/pricelist.json
