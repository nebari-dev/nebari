import functools
import logging
import os
from typing import Dict

from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version

logger = logging.getLogger("azure")
logger.setLevel(logging.ERROR)


def check_credentials():
    for variable in {
        "ARM_CLIENT_ID",
        "ARM_CLIENT_SECRET",
        "ARM_SUBSCRIPTION_ID",
        "ARM_TENANT_ID",
    }:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {constants.AZURE_ENV_DOCS}"""
            )


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


### PYDANTIC VALIDATORS ###


def validate_tags(tags: Dict[str, str]) -> Dict[str, str]:
    max_name_length = 512
    max_value_length = 256
    invalid_chars = "<>%&\\?/"

    for tag_name, tag_value in tags.items():
        if any(char in tag_name for char in invalid_chars):
            raise ValueError(
                f"Tag name '{tag_name}' contains invalid characters. Invalid characters are: `{invalid_chars}`"
            )

        if len(tag_name) > max_name_length:
            raise ValueError(
                f"Tag name '{tag_name}' exceeds maximum length of {max_name_length} characters."
            )

        if len(tag_value) > max_value_length:
            raise ValueError(
                f"Tag value '{tag_value}' for tag '{tag_name}' exceeds maximum length of {max_value_length} characters."
            )

    return tags
