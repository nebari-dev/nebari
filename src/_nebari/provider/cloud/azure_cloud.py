import functools
import logging
import os
import time
from typing import Dict

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.resource import ResourceManagementClient

from _nebari.constants import AZURE_ENV_DOCS
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from _nebari.utils import (
    AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
    check_environment_variables,
    construct_azure_resource_group_name,
)
from nebari import schema

logger = logging.getLogger("azure")
logger.setLevel(logging.ERROR)

DURATION = 10
RETRIES = 10


def check_credentials() -> DefaultAzureCredential:
    required_variables = {"ARM_CLIENT_ID", "ARM_SUBSCRIPTION_ID", "ARM_TENANT_ID"}
    check_environment_variables(required_variables, AZURE_ENV_DOCS)

    optional_variable = "ARM_CLIENT_SECRET"
    arm_client_secret = os.environ.get(optional_variable, None)
    if arm_client_secret:
        logger.info("Authenticating as a service principal.")
    else:
        logger.info(f"No {optional_variable} environment variable found.")
        logger.info("Allowing Azure SDK to authenticate using OIDC or other methods.")
    return DefaultAzureCredential()


@functools.lru_cache()
def initiate_container_service_client():
    subscription_id = os.environ.get("ARM_SUBSCRIPTION_ID", None)
    credentials = check_credentials()

    return ContainerServiceClient(
        credential=credentials, subscription_id=subscription_id
    )


@functools.lru_cache()
def initiate_resource_management_client():
    subscription_id = os.environ.get("ARM_SUBSCRIPTION_ID", None)
    credentials = check_credentials()

    return ResourceManagementClient(
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


def delete_resource_group(resource_group_name: str):
    """Delete resource group and all resources within it."""

    client = initiate_resource_management_client()
    try:
        client.resource_groups.begin_delete(resource_group_name)
    except ResourceNotFoundError:
        logger.info(f"Resource group `{resource_group_name}` deleted successfully.")
        return

    retries = 0
    while retries < RETRIES:
        try:
            client.resource_groups.get(resource_group_name)
        except ResourceNotFoundError:
            logger.info(f"Resource group `{resource_group_name}` deleted successfully.")
            break
        logger.info(
            f"Waiting for resource group `{resource_group_name}` to be deleted..."
        )
        time.sleep(DURATION)
        retries += 1


def azure_cleanup(config: schema.Main):
    """Delete all resources on Azure created by Nebari"""

    # deleting this resource group automatically deletes the associated node resource group
    aks_resource_group = construct_azure_resource_group_name(
        project_name=config.project_name,
        namespace=config.namespace,
        base_resource_group_name=config.azure.resource_group_name,
    )

    state_resource_group = construct_azure_resource_group_name(
        project_name=config.project_name,
        namespace=config.namespace,
        base_resource_group_name=config.azure.resource_group_name,
        suffix=AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
    )

    delete_resource_group(aks_resource_group)
    delete_resource_group(state_resource_group)


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
