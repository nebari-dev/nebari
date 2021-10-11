import os
import time
import functools
from azure.identity import EnvironmentCredential
from azure.identity import DefaultAzureCredential
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.containerservice import ContainerServiceClient


@functools.lru_cache()
def initiate_container_service_client():
    subscription_id = os.environ.get("ARM_SUBSCRIPTION_ID", None)
    return ContainerServiceClient(
        credential=EnvironmentCredential(), subscription_id=subscription_id
    )


@functools.lru_cache()
def get_azure_default_kubernetes_version(azure_location="Central US"):

    client = initiate_container_service_client()
    azure_location = azure_location.replace(" ", "").lower()

    k8s_versions_list = client.container_services.list_orchestrators(
        azure_location, resource_type="managedClusters"
    ).as_dict()
    default_kubernetes_version = []

    for key in k8s_versions_list["orchestrators"]:
        if key["orchestrator_type"] == "Kubernetes":
            if "default" in key:
                default_kubernetes_version.append(key["orchestrator_version"])

    return default_kubernetes_version


@functools.lru_cache()
def kubernetes_versions(azure_location="Central US"):

    client = initiate_container_service_client()
    azure_location = azure_location.replace(" ", "").lower()

    k8s_versions_list = client.container_services.list_orchestrators(
        azure_location, resource_type="managedClusters"
    ).as_dict()
    supported_kubernetes_versions = []

    for key in k8s_versions_list["orchestrators"]:
        if key["orchestrator_type"] == "Kubernetes":
            supported_kubernetes_versions.append(key["orchestrator_version"])

    return supported_kubernetes_versions
