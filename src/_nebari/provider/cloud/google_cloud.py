import functools
from typing import List, Set

from google.cloud import compute_v1, container_v1, iam_credentials_v1, storage

from _nebari.constants import GCP_ENV_DOCS
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from _nebari.utils import check_environment_variables
from nebari import schema


def check_credentials() -> None:
    required_variables = {"GOOGLE_CREDENTIALS", "PROJECT_ID"}
    check_environment_variables(required_variables, GCP_ENV_DOCS)


@functools.lru_cache()
def regions(project: str) -> Set[str]:
    """Return a dict of available regions."""
    check_credentials()
    client = compute_v1.RegionsClient()
    response = client.list(project=project)

    return {region.name for region in response}


@functools.lru_cache()
def kubernetes_versions(project: str, region: str) -> List[str]:
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    check_credentials()
    client = container_v1.ClusterManagerClient()
    response = client.get_server_config(name=f"projects/{project}/locations/{region}")
    supported_kubernetes_versions = response.valid_master_versions

    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)


def cluster_exists(cluster_name: str, project_id: str, zone: str) -> bool:
    """Check if a GKE cluster exists."""
    client = container_v1.ClusterManagerClient()
    request = container_v1.GetClusterRequest()
    response = client.get_cluster(request=request, project_id=project_id, zone=zone)

    return response is not None


def bucket_exists(bucket_name: str, project_id: str) -> bool:
    """Check if a storage bucket exists."""
    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucket_name)
    return bucket is not None


def service_account_exists(service_account_name: str, project_id: str) -> bool:
    """Check if a service account exists."""
    client = iam_credentials_v1.IAMCredentialsClient()
    service_acc = client.service_account_path(project_id, service_account_name)
    return service_acc is not None


def delete_cluster(cluster_name: str, project_id: str, region: str):
    """Delete a GKE cluster if it exists."""
    check_credentials()

    if not cluster_exists(cluster_name, project_id, region):
        print(
            f"Cluster {cluster_name} does not exist in project {project_id}, region {region}. Exiting gracefully."
        )
        return

    client = container_v1.ClusterManagerClient()
    request = client.DeleteClusterRequest()
    try:
        client.delete_cluster(request=request)
    except google.api_core.exceptions.GoogleAPICallError as e:
        if e.status_code == 200:
            print("Cluster deleted successfully!")
        else:
            print("error deleting cluster!")


def delete_storage_bucket(bucket_name: str, project_id: str):
    """Delete a storage bucket if it exists."""
    check_credentials()

    if not bucket_exists(bucket_name, project_id):
        print(
            f"Bucket {bucket_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return

    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucket_name)
    try:
        bucket.delete()
        print(f"Successfully deleted bucket {bucket_name}.")
    except storage.exceptions.BucketNotFoundError as e:
        print(f"Failed to delete bucket {bucket_name}. Error: {e}")


def delete_service_account(service_account_name: str, project_id: str):
    """Delete a service account if it exists."""
    check_credentials()

    if not service_account_exists(service_account_name, project_id):
        print(
            f"Service account {service_account_name} does not exist in project {project_id}. Exiting gracefully."
        )
        return
    client = iam_credentials_v1.IAMCredentialsClient()
    client.service_account_path(project_id, service_account_name)
    try:
        client.delete_service_account(service_account_name)
        print(f"Successfully deleted service account {service_account_name}.")
    except iam_credentials_v1.exceptions.IamServiceAccountNotFoundError as e:
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
