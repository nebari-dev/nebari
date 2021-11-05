import os
import functools
import logging
from azure.identity import EnvironmentCredential
from azure.mgmt.containerservice import ContainerServiceClient

logger = logging.getLogger("azure")
logger.setLevel(logging.ERROR)


@functools.lru_cache()
def initiate_container_service_client():
    subscription_id = os.environ.get("ARM_SUBSCRIPTION_ID", None)

    # Python SDK needs different env var names to Terraform SDK
    for envname in ("TENANT_ID", "CLIENT_SECRET", "CLIENT_ID"):
        azure_name = f"AZURE_{envname}"
        if azure_name not in os.environ:
            os.environ[azure_name] = os.environ[f"ARM_{envname}"]

    return ContainerServiceClient(
        credential=EnvironmentCredential(), subscription_id=subscription_id
    )


@functools.lru_cache()
def kubernetes_versions(azure_location="Central US"):

    client = initiate_container_service_client()

    k8s_versions_list = client.container_services.list_orchestrators(
        azure_location, resource_type="managedClusters"
    ).as_dict()
    supported_kubernetes_versions = []

    for key in k8s_versions_list["orchestrators"]:
        if key["orchestrator_type"] == "Kubernetes":
            supported_kubernetes_versions.append(key["orchestrator_version"])

    return supported_kubernetes_versions
