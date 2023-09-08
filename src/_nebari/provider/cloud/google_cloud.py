import functools
import json
import os
import subprocess
from typing import Dict, List

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version


def check_credentials():
    for variable in {"GOOGLE_CREDENTIALS", "PROJECT_ID"}:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {constants.GCP_ENV_DOCS}"""
            )


@functools.lru_cache()
def projects() -> Dict[str, str]:
    """Return a dict of available projects."""
    check_credentials()
    output = subprocess.check_output(["gcloud", "projects", "list", "--format=json"])
    data = json.loads(output.decode("utf-8"))
    return {_["name"]: _["projectId"] for _ in data}


@functools.lru_cache()
def regions(project: str) -> Dict[str, str]:
    """Return a dict of available regions."""
    check_credentials()
    output = subprocess.check_output(
        ["gcloud", "compute", "regions", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data}


@functools.lru_cache()
def zones(project: str, region: str) -> Dict[str, str]:
    """Return a dict of available zones."""
    check_credentials()
    output = subprocess.check_output(
        ["gcloud", "compute", "zones", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data if _["name"].startswith(region)}


@functools.lru_cache()
def kubernetes_versions(region: str) -> List[str]:
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    check_credentials()
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
def instances(project: str) -> Dict[str, str]:
    """Return a dict of available instances."""
    check_credentials()
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


### PYDANTIC VALIDATORS ###


def validate_region(project_id: str, region: str) -> str:
    """Validate the GCP region is valid."""
    available_regions = regions(project_id)
    if region not in available_regions:
        raise ValueError(
            f"Region {region} is not one of available regions {available_regions}"
        )
    return region
