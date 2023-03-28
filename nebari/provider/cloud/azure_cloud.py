import functools
import logging
import os

from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient

from nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version

logger = logging.getLogger("azure")
logger.setLevel(logging.ERROR)


@functools.lru_cache()
def initiate_container_service_client():
    subscription_id = os.environ.get("ARM_SUBSCRIPTION_ID", None)

    credentials = DefaultAzureCredential()

    return ContainerServiceClient(
        credential=credentials, subscription_id=subscription_id
    )


@functools.lru_cache()
def kubernetes_versions(region="Central US"):
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    client = initiate_container_service_client()
    azure_location = region.replace(" ", "").lower()

    k8s_versions_list = client.container_services.list_orchestrators(
        azure_location, resource_type="managedClusters"
    ).as_dict()
    supported_kubernetes_versions = []

    for key in k8s_versions_list["orchestrators"]:
        if key["orchestrator_type"] == "Kubernetes":
            supported_kubernetes_versions.append(key["orchestrator_version"])

    supported_kubernetes_versions = sorted(supported_kubernetes_versions)
    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)
