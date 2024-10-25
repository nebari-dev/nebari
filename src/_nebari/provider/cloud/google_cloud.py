import functools
import json
import os
from typing import List, Set

import google.api_core.exceptions
from google.auth import load_credentials_from_dict, load_credentials_from_file
from google.cloud import compute_v1, container_v1, iam_admin_v1, storage

from _nebari.constants import GCP_ENV_DOCS
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from _nebari.utils import check_environment_variables
from nebari import schema


def check_credentials() -> None:
    required_variables = {"GOOGLE_CREDENTIALS", "PROJECT_ID"}
    check_environment_variables(required_variables, GCP_ENV_DOCS)


@functools.lru_cache()
def load_credentials():
    check_credentials()
    credentials = os.environ["GOOGLE_CREDENTIALS"]
    project_id = os.environ["PROJECT_ID"]

    # Scopes need to be explicitly defined when using workload identity
    # federation.
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    # Google credentials are stored as strings in GHA secrets so we need
    # to determine if the credentials are stored as a file or not before
    # reading them
    if credentials.endswith(".json"):
        loaded_credentials, _ = load_credentials_from_file(credentials, scopes=scopes)
    else:
        loaded_credentials, _ = load_credentials_from_dict(
            json.loads(credentials), scopes=scopes
        )

    return loaded_credentials, project_id


@functools.lru_cache()
def regions() -> Set[str]:
    """Return a dict of available regions."""
    credentials, project_id = load_credentials()
    client = compute_v1.RegionsClient(credentials=credentials)
    response = client.list(project=project_id)

    return {region.name for region in response}


@functools.lru_cache()
def kubernetes_versions(region: str) -> List[str]:
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    credentials, project_id = load_credentials()
    client = container_v1.ClusterManagerClient(credentials=credentials)
    response = client.get_server_config(
        name=f"projects/{project_id}/locations/{region}"
    )
    supported_kubernetes_versions = response.valid_master_versions

    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)


def cluster_exists(cluster_name: str, region: str) -> bool:
    """Check if a GKE cluster exists."""
    credentials, project_id = load_credentials()
    client = container_v1.ClusterManagerClient(credentials=credentials)

    try:
        client.get_cluster(
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
    except google.api_core.exceptions.NotFound:
        return False
    return True


def bucket_exists(bucket_name: str) -> bool:
    """Check if a storage bucket exists."""
    credentials, _ = load_credentials()
    client = storage.Client(credentials=credentials)

    try:
        client.get_bucket(bucket_name)
    except google.api_core.exceptions.NotFound:
        return False
    return True


def service_account_exists(service_account_name: str) -> bool:
    """Check if a service account exists."""
    credentials, project_id = load_credentials()
    client = iam_admin_v1.IAMClient(credentials=credentials)

    service_account_path = client.service_account_path(project_id, service_account_name)
    try:
        client.get_service_account(name=service_account_path)
    except google.api_core.exceptions.NotFound:
        return False
    return True


def delete_cluster(cluster_name: str, region: str):
    """Delete a GKE cluster if it exists."""
    credentials, project_id = load_credentials()
    if not cluster_exists(cluster_name, region):
        print(
            f"Cluster {cluster_name} does not exist in project {project_id}, region {region}. Exiting gracefully."
        )
        return

    client = container_v1.ClusterManagerClient(credentials=credentials)
    try:
        client.delete_cluster(
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )
        print(f"Successfully deleted cluster {cluster_name}.")
    except google.api_core.exceptions.GoogleAPIError as e:
        print(f"Failed to delete bucket {bucket_name}. Error: {e}")


def delete_storage_bucket(bucket_name: str):
    """Delete a storage bucket if it exists."""
    credentials, project_id = load_credentials()

    if not bucket_exists(bucket_name):
        print(
            f"Bucket {bucket_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return

    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    try:
        bucket.delete(force=True)
        print(f"Successfully deleted bucket {bucket_name}.")
    except google.api_core.exceptions.GoogleAPIError as e:
        print(f"Failed to delete bucket {bucket_name}. Error: {e}")


def delete_service_account(service_account_name: str):
    """Delete a service account if it exists."""
    credentials, project_id = load_credentials()

    if not service_account_exists(service_account_name):
        print(
            f"Service account {service_account_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return

    client = iam_admin_v1.IAMClient(credentials=credentials)
    service_account_path = client.service_account_path(project_id, service_account_name)
    try:
        client.delete_service_account(name=service_account_path)
        print(f"Successfully deleted service account {service_account_name}.")
    except google.api_core.exceptions.GoogleAPIError as e:
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

    delete_cluster(cluster_name, region)
    delete_storage_bucket(bucket_name)
    delete_service_account(service_account_name)
