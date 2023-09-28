import functools
import json
import os
import subprocess
from typing import Dict, List

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from nebari import schema


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
    output = subprocess.check_output(
        ["gcloud", "projects", "list", "--format=json(name,projectId)"]
    )
    data = json.loads(output)
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


def cluster_exists(cluster_name: str, project_id: str, region: str) -> bool:
    """Check if a GKE cluster exists."""
    try:
        subprocess.check_output(
            [
                "gcloud",
                "container",
                "clusters",
                "describe",
                cluster_name,
                "--project",
                project_id,
                "--region",
                region,
            ]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def bucket_exists(bucket_name: str, project_id: str) -> bool:
    """Check if a storage bucket exists."""
    try:
        print(f"Checking if bucket {bucket_name} exists in project {project_id}.")
        subprocess.check_output(
            [
                "gsutil",
                "ls",
                f"gs://{bucket_name}/",
                "-p",
                project_id,
            ]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def service_account_exists(service_account_name: str, project_id: str) -> bool:
    """Check if a service account exists."""
    try:
        subprocess.check_output(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "describe",
                service_account_name,
                "--project",
                project_id,
            ]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def delete_cluster(cluster_name: str, project_id: str, region: str):
    """Delete a GKE cluster if it exists."""
    check_credentials()

    if not cluster_exists(cluster_name, project_id, region):
        print(
            f"Cluster {cluster_name} does not exist in project {project_id}, region {region}. Exiting gracefully."
        )
        return

    try:
        subprocess.check_call(
            [
                "gcloud",
                "container",
                "clusters",
                "delete",
                cluster_name,
                "--project",
                project_id,
                "--region",
                region,
                "--quiet",
            ]
        )
        print(f"Successfully deleted cluster {cluster_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete cluster {cluster_name}. Error: {e}")


def delete_storage_bucket(bucket_name: str, project_id: str):
    """Delete a storage bucket if it exists."""
    check_credentials()

    if not bucket_exists(bucket_name, project_id):
        print(
            f"Bucket {bucket_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return

    try:
        subprocess.check_call(
            [
                "gsutil",
                "-m",
                "rm",
                "-r",
                f"gs://{bucket_name}",
                "-p",
                project_id,
            ]
        )
        print(f"Successfully deleted bucket {bucket_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete bucket {bucket_name}. Error: {e}")


def delete_service_account(service_account_name: str, project_id: str):
    """Delete a service account if it exists."""
    check_credentials()

    if not service_account_exists(service_account_name, project_id):
        print(
            f"Service account {service_account_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return

    try:
        subprocess.check_call(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "delete",
                service_account_name,
                "--quiet",
                "--project",
                project_id,
            ]
        )
        print(f"Successfully deleted service account {service_account_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete service account {service_account_name}. Error: {e}")


def gcp_cleanup(config: schema.Main):
    """Delete all GCP resources."""
    check_credentials()
    project_name = config.project_name
    namespace = config.namespace
    project_id = config.google_cloud_platform.project
    region = config.google_cloud_platform.region
    cluster_name = f"{project_name}-{namespace}"
    bucket_name = f"{project_name}-{namespace}-terraform-state"
    service_account_name = (
        f"{project_name}-{namespace}@{project_id}.iam.gserviceaccount.com"
    )

    delete_cluster(cluster_name, project_id, region)
    delete_storage_bucket(bucket_name, project_id)
    delete_service_account(service_account_name, project_id)


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
