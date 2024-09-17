import contextlib
import enum
import inspect
import os
import pathlib
import re
import sys
import tempfile
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Type, Union

from pydantic import Field, field_validator, model_validator

from _nebari import constants
from _nebari.provider import terraform
from _nebari.provider.cloud import (
    amazon_web_services,
    azure_cloud,
    digital_ocean,
    google_cloud,
)
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.kubernetes_services import SharedFsEnum
from _nebari.stages.tf_objects import NebariTerraformState
from _nebari.utils import (
    AZURE_NODE_RESOURCE_GROUP_SUFFIX,
    construct_azure_resource_group_name,
    modified_environ,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


def get_kubeconfig_filename():
    return str(pathlib.Path(tempfile.gettempdir()) / "NEBARI_KUBECONFIG")


class LocalInputVars(schema.Base):
    kubeconfig_filename: str = get_kubeconfig_filename()
    kube_context: Optional[str] = None


class ExistingInputVars(schema.Base):
    kube_context: str


class DigitalOceanNodeGroup(schema.Base):
    instance: str
    min_nodes: int
    max_nodes: int


class DigitalOceanInputVars(schema.Base):
    name: str
    environment: str
    region: str
    tags: List[str]
    kubernetes_version: str
    node_groups: Dict[str, DigitalOceanNodeGroup]
    kubeconfig_filename: str = get_kubeconfig_filename()


class GCPNodeGroupInputVars(schema.Base):
    name: str
    instance_type: str
    min_size: int
    max_size: int
    labels: Dict[str, str]
    preemptible: bool
    guest_accelerators: List["GCPGuestAccelerator"]


class GCPPrivateClusterConfig(schema.Base):
    enable_private_nodes: bool
    enable_private_endpoint: bool
    master_ipv4_cidr_block: str


@schema.yaml_object(schema.yaml)
class GCPNodeGroupImageTypeEnum(str, enum.Enum):
    UBUNTU_CONTAINERD = "UBUNTU_CONTAINERD"
    COS_CONTAINERD = "COS_CONTAINERD"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class GCPInputVars(schema.Base):
    name: str
    environment: str
    region: str
    project_id: str
    availability_zones: List[str]
    node_groups: List[GCPNodeGroupInputVars]
    kubeconfig_filename: str = get_kubeconfig_filename()
    tags: List[str]
    kubernetes_version: str
    release_channel: str
    networking_mode: str
    network: str
    subnetwork: Optional[str] = None
    ip_allocation_policy: Optional[Dict[str, str]] = None
    master_authorized_networks_config: Optional[Dict[str, str]] = None
    private_cluster_config: Optional[GCPPrivateClusterConfig] = None
    node_group_image_type: GCPNodeGroupImageTypeEnum = None


class AzureNodeGroupInputVars(schema.Base):
    instance: str
    min_nodes: int
    max_nodes: int


class AzureInputVars(schema.Base):
    name: str
    environment: str
    region: str
    kubeconfig_filename: str = get_kubeconfig_filename()
    kubernetes_version: str
    node_groups: Dict[str, AzureNodeGroupInputVars]
    resource_group_name: str
    node_resource_group_name: str
    vnet_subnet_id: Optional[str] = None
    private_cluster_enabled: bool
    tags: Dict[str, str] = {}
    max_pods: Optional[int] = None
    network_profile: Optional[Dict[str, str]] = None
    workload_identity_enabled: bool = False


class AWSNodeGroupInputVars(schema.Base):
    name: str
    instance_type: str
    gpu: bool = False
    min_size: int
    desired_size: int
    max_size: int
    single_subnet: bool
    permissions_boundary: Optional[str] = None


class AWSInputVars(schema.Base):
    name: str
    environment: str
    existing_security_group_id: Optional[str] = None
    existing_subnet_ids: Optional[List[str]] = None
    region: str
    kubernetes_version: str
    eks_endpoint_access: Optional[
        Literal["private", "public", "public_and_private"]
    ] = "public"
    node_groups: List[AWSNodeGroupInputVars]
    availability_zones: List[str]
    vpc_cidr_block: str
    permissions_boundary: Optional[str] = None
    kubeconfig_filename: str = get_kubeconfig_filename()
    tags: Dict[str, str] = {}
    efs_enabled: bool


def _calculate_asg_node_group_map(config: schema.Main):
    if config.provider == schema.ProviderEnum.aws:
        return amazon_web_services.aws_get_asg_node_group_mapping(
            config.project_name,
            config.namespace,
            config.amazon_web_services.region,
        )
    else:
        return {}


def _calculate_node_groups(config: schema.Main):
    if config.provider == schema.ProviderEnum.aws:
        return {
            group: {"key": "eks.amazonaws.com/nodegroup", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.gcp:
        return {
            group: {"key": "cloud.google.com/gke-nodepool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.azure:
        return {
            group: {"key": "azure-node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.do:
        return {
            group: {"key": "doks.digitalocean.com/node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.existing:
        return config.existing.model_dump()["node_selectors"]
    else:
        return config.local.model_dump()["node_selectors"]


def node_groups_to_dict(node_groups):
    return {ng_name: ng.model_dump() for ng_name, ng in node_groups.items()}


@contextlib.contextmanager
def kubernetes_provider_context(kubernetes_credentials: Dict[str, str]):
    credential_mapping = {
        "config_path": "KUBE_CONFIG_PATH",
        "config_context": "KUBE_CTX",
        "username": "KUBE_USER",
        "password": "KUBE_PASSWORD",
        "client_certificate": "KUBE_CLIENT_CERT_DATA",
        "client_key": "KUBE_CLIENT_KEY_DATA",
        "cluster_ca_certificate": "KUBE_CLUSTER_CA_CERT_DATA",
        "host": "KUBE_HOST",
        "token": "KUBE_TOKEN",
    }

    credentials = {
        credential_mapping[k]: v
        for k, v in kubernetes_credentials.items()
        if v is not None
    }
    with modified_environ(**credentials):
        yield


class KeyValueDict(schema.Base):
    key: str
    value: str


class DigitalOceanNodeGroup(schema.Base):
    """Representation of a node group with Digital Ocean

    - Kubernetes limits: https://docs.digitalocean.com/products/kubernetes/details/limits/
    - Available instance types: https://slugs.do-api.dev/
    """

    instance: str
    min_nodes: Annotated[int, Field(ge=1)] = 1
    max_nodes: Annotated[int, Field(ge=1)] = 1


DEFAULT_DO_NODE_GROUPS = {
    "general": DigitalOceanNodeGroup(instance="g-8vcpu-32gb", min_nodes=1, max_nodes=1),
    "user": DigitalOceanNodeGroup(instance="g-4vcpu-16gb", min_nodes=1, max_nodes=5),
    "worker": DigitalOceanNodeGroup(instance="g-4vcpu-16gb", min_nodes=1, max_nodes=5),
}


class DigitalOceanProvider(schema.Base):
    region: str
    kubernetes_version: Optional[str] = None
    # Digital Ocean image slugs are listed here https://slugs.do-api.dev/
    node_groups: Dict[str, DigitalOceanNodeGroup] = DEFAULT_DO_NODE_GROUPS
    tags: Optional[List[str]] = []

    @model_validator(mode="before")
    @classmethod
    def _check_input(cls, data: Any) -> Any:
        digital_ocean.check_credentials()

        # check if region is valid
        available_regions = set(_["slug"] for _ in digital_ocean.regions())
        if data["region"] not in available_regions:
            raise ValueError(
                f"Digital Ocean region={data['region']} is not one of {available_regions}"
            )

        # check if kubernetes version is valid
        available_kubernetes_versions = digital_ocean.kubernetes_versions()
        if len(available_kubernetes_versions) == 0:
            raise ValueError(
                "Request to Digital Ocean for available Kubernetes versions failed."
            )
        if data["kubernetes_version"] is None:
            data["kubernetes_version"] = available_kubernetes_versions[-1]
        elif data["kubernetes_version"] not in available_kubernetes_versions:
            raise ValueError(
                f"\nInvalid `kubernetes-version` provided: {data['kubernetes_version']}.\nPlease select from one of the following supported Kubernetes versions: {available_kubernetes_versions} or omit flag to use latest Kubernetes version available."
            )

        available_instances = {_["slug"] for _ in digital_ocean.instances()}
        if "node_groups" in data:
            for _, node_group in data["node_groups"].items():
                if node_group["instance"] not in available_instances:
                    raise ValueError(
                        f"Digital Ocean instance {node_group.instance} not one of available instance types={available_instances}"
                    )
        return data


class GCPIPAllocationPolicy(schema.Base):
    cluster_secondary_range_name: str
    services_secondary_range_name: str
    cluster_ipv4_cidr_block: str
    services_ipv4_cidr_block: str


class GCPCIDRBlock(schema.Base):
    cidr_block: str
    display_name: str


class GCPMasterAuthorizedNetworksConfig(schema.Base):
    cidr_blocks: List[GCPCIDRBlock]


class GCPPrivateClusterConfig(schema.Base):
    enable_private_endpoint: bool
    enable_private_nodes: bool
    master_ipv4_cidr_block: str


class GCPGuestAccelerator(schema.Base):
    """
    See general information regarding GPU support at:
    # TODO: replace with nebari.dev new URL
    https://docs.nebari.dev/en/stable/source/admin_guide/gpu.html?#add-gpu-node-group
    """

    name: str
    count: Annotated[int, Field(ge=1)] = 1


class GCPNodeGroup(schema.Base):
    instance: str
    min_nodes: Annotated[int, Field(ge=0)] = 0
    max_nodes: Annotated[int, Field(ge=1)] = 1
    preemptible: bool = False
    labels: Dict[str, str] = {}
    guest_accelerators: List[GCPGuestAccelerator] = []


DEFAULT_GCP_NODE_GROUPS = {
    "general": GCPNodeGroup(instance="e2-standard-8", min_nodes=1, max_nodes=1),
    "user": GCPNodeGroup(instance="e2-standard-4", min_nodes=0, max_nodes=5),
    "worker": GCPNodeGroup(instance="e2-standard-4", min_nodes=0, max_nodes=5),
}


class GoogleCloudPlatformProvider(schema.Base):
    region: str
    project: str
    kubernetes_version: str
    availability_zones: Optional[List[str]] = []
    release_channel: str = constants.DEFAULT_GKE_RELEASE_CHANNEL
    node_groups: Dict[str, GCPNodeGroup] = DEFAULT_GCP_NODE_GROUPS
    tags: Optional[List[str]] = []
    networking_mode: str = "ROUTE"
    network: str = "default"
    subnetwork: Optional[Union[str, None]] = None
    ip_allocation_policy: Optional[Union[GCPIPAllocationPolicy, None]] = None
    master_authorized_networks_config: Optional[Union[GCPCIDRBlock, None]] = None
    private_cluster_config: Optional[Union[GCPPrivateClusterConfig, None]] = None

    @model_validator(mode="before")
    @classmethod
    def _check_input(cls, data: Any) -> Any:
        available_regions = google_cloud.regions()
        if data["region"] not in available_regions:
            raise ValueError(
                f"Google Cloud region={data['region']} is not one of {available_regions}"
            )

        available_kubernetes_versions = google_cloud.kubernetes_versions(data["region"])
        print(available_kubernetes_versions)
        if data["kubernetes_version"] not in available_kubernetes_versions:
            raise ValueError(
                f"\nInvalid `kubernetes-version` provided: {data['kubernetes_version']}.\nPlease select from one of the following supported Kubernetes versions: {available_kubernetes_versions} or omit flag to use latest Kubernetes version available."
            )
        return data


class AzureNodeGroup(schema.Base):
    instance: str
    min_nodes: int
    max_nodes: int


DEFAULT_AZURE_NODE_GROUPS = {
    "general": AzureNodeGroup(instance="Standard_D8_v3", min_nodes=1, max_nodes=1),
    "user": AzureNodeGroup(instance="Standard_D4_v3", min_nodes=0, max_nodes=5),
    "worker": AzureNodeGroup(instance="Standard_D4_v3", min_nodes=0, max_nodes=5),
}


class AzureProvider(schema.Base):
    region: str
    kubernetes_version: Optional[str] = None
    storage_account_postfix: str
    resource_group_name: Optional[str] = None
    node_groups: Dict[str, AzureNodeGroup] = DEFAULT_AZURE_NODE_GROUPS
    storage_account_postfix: str
    vnet_subnet_id: Optional[str] = None
    private_cluster_enabled: bool = False
    resource_group_name: Optional[str] = None
    tags: Optional[Dict[str, str]] = {}
    network_profile: Optional[Dict[str, str]] = None
    max_pods: Optional[int] = None
    workload_identity_enabled: bool = False

    @model_validator(mode="before")
    @classmethod
    def _check_credentials(cls, data: Any) -> Any:
        azure_cloud.check_credentials()
        return data

    @field_validator("kubernetes_version")
    @classmethod
    def _validate_kubernetes_version(cls, value: Optional[str]) -> str:
        available_kubernetes_versions = azure_cloud.kubernetes_versions()
        if value is None:
            value = available_kubernetes_versions[-1]
        elif value not in available_kubernetes_versions:
            raise ValueError(
                f"\nInvalid `kubernetes-version` provided: {value}.\nPlease select from one of the following supported Kubernetes versions: {available_kubernetes_versions} or omit flag to use latest Kubernetes version available."
            )
        return value

    @field_validator("resource_group_name")
    @classmethod
    def _validate_resource_group_name(cls, value):
        if value is None:
            return value
        length = len(value) + len(AZURE_NODE_RESOURCE_GROUP_SUFFIX)
        if length < 1 or length > 90:
            raise ValueError(
                f"Azure Resource Group name must be between 1 and 90 characters long, when combined with the suffix `{AZURE_NODE_RESOURCE_GROUP_SUFFIX}`."
            )
        if not re.match(r"^[\w\-\.\(\)]+$", value):
            raise ValueError(
                "Azure Resource Group name can only contain alphanumerics, underscores, parentheses, hyphens, and periods."
            )
        if value[-1] == ".":
            raise ValueError("Azure Resource Group name can't end with a period.")

        return value

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: Optional[Dict[str, str]]) -> Dict[str, str]:
        return value if value is None else azure_cloud.validate_tags(value)


class AWSNodeGroup(schema.Base):
    instance: str
    min_nodes: int = 0
    max_nodes: int
    gpu: bool = False
    single_subnet: bool = False
    permissions_boundary: Optional[str] = None


DEFAULT_AWS_NODE_GROUPS = {
    "general": AWSNodeGroup(instance="m5.2xlarge", min_nodes=1, max_nodes=1),
    "user": AWSNodeGroup(
        instance="m5.xlarge", min_nodes=0, max_nodes=5, single_subnet=False
    ),
    "worker": AWSNodeGroup(
        instance="m5.xlarge", min_nodes=0, max_nodes=5, single_subnet=False
    ),
}


class AmazonWebServicesProvider(schema.Base):
    region: str
    kubernetes_version: str
    availability_zones: Optional[List[str]]
    node_groups: Dict[str, AWSNodeGroup] = DEFAULT_AWS_NODE_GROUPS
    eks_endpoint_access: Optional[
        Literal["private", "public", "public_and_private"]
    ] = "public"
    existing_subnet_ids: Optional[List[str]] = None
    existing_security_group_id: Optional[str] = None
    vpc_cidr_block: str = "10.10.0.0/16"
    permissions_boundary: Optional[str] = None
    tags: Optional[Dict[str, str]] = {}

    @model_validator(mode="before")
    @classmethod
    def _check_input(cls, data: Any) -> Any:
        amazon_web_services.check_credentials()

        # check if region is valid
        available_regions = amazon_web_services.regions(data["region"])
        if data["region"] not in available_regions:
            raise ValueError(
                f"Amazon Web Services region={data['region']} is not one of {available_regions}"
            )

        # check if kubernetes version is valid
        available_kubernetes_versions = amazon_web_services.kubernetes_versions(
            data["region"]
        )
        if len(available_kubernetes_versions) == 0:
            raise ValueError("Request to AWS for available Kubernetes versions failed.")
        if data["kubernetes_version"] is None:
            data["kubernetes_version"] = available_kubernetes_versions[-1]
        elif data["kubernetes_version"] not in available_kubernetes_versions:
            raise ValueError(
                f"\nInvalid `kubernetes-version` provided: {data['kubernetes_version']}.\nPlease select from one of the following supported Kubernetes versions: {available_kubernetes_versions} or omit flag to use latest Kubernetes version available."
            )

        # check if availability zones are valid
        available_zones = amazon_web_services.zones(data["region"])
        if "availability_zones" not in data:
            data["availability_zones"] = list(sorted(available_zones))[:2]
        else:
            for zone in data["availability_zones"]:
                if zone not in available_zones:
                    raise ValueError(
                        f"Amazon Web Services availability zone={zone} is not one of {available_zones}"
                    )

        # check if instances are valid
        available_instances = amazon_web_services.instances(data["region"])
        if "node_groups" in data:
            for _, node_group in data["node_groups"].items():
                instance = (
                    node_group["instance"]
                    if hasattr(node_group, "__getitem__")
                    else node_group.instance
                )
                if instance not in available_instances:
                    raise ValueError(
                        f"Amazon Web Services instance {node_group.instance} not one of available instance types={available_instances}"
                    )
        return data


class LocalProvider(schema.Base):
    kube_context: Optional[str] = None
    node_selectors: Dict[str, KeyValueDict] = {
        "general": KeyValueDict(key="kubernetes.io/os", value="linux"),
        "user": KeyValueDict(key="kubernetes.io/os", value="linux"),
        "worker": KeyValueDict(key="kubernetes.io/os", value="linux"),
    }


class ExistingProvider(schema.Base):
    kube_context: Optional[str] = None
    node_selectors: Dict[str, KeyValueDict] = {
        "general": KeyValueDict(key="kubernetes.io/os", value="linux"),
        "user": KeyValueDict(key="kubernetes.io/os", value="linux"),
        "worker": KeyValueDict(key="kubernetes.io/os", value="linux"),
    }


provider_enum_model_map = {
    schema.ProviderEnum.local: LocalProvider,
    schema.ProviderEnum.existing: ExistingProvider,
    schema.ProviderEnum.gcp: GoogleCloudPlatformProvider,
    schema.ProviderEnum.aws: AmazonWebServicesProvider,
    schema.ProviderEnum.azure: AzureProvider,
    schema.ProviderEnum.do: DigitalOceanProvider,
}

provider_enum_name_map: Dict[schema.ProviderEnum, str] = {
    schema.ProviderEnum.local: "local",
    schema.ProviderEnum.existing: "existing",
    schema.ProviderEnum.gcp: "google_cloud_platform",
    schema.ProviderEnum.aws: "amazon_web_services",
    schema.ProviderEnum.azure: "azure",
    schema.ProviderEnum.do: "digital_ocean",
}

provider_name_abbreviation_map: Dict[str, str] = {
    value: key.value for key, value in provider_enum_name_map.items()
}

provider_enum_default_node_groups_map: Dict[schema.ProviderEnum, Any] = {
    schema.ProviderEnum.gcp: node_groups_to_dict(DEFAULT_GCP_NODE_GROUPS),
    schema.ProviderEnum.aws: node_groups_to_dict(DEFAULT_AWS_NODE_GROUPS),
    schema.ProviderEnum.azure: node_groups_to_dict(DEFAULT_AZURE_NODE_GROUPS),
    schema.ProviderEnum.do: node_groups_to_dict(DEFAULT_DO_NODE_GROUPS),
}


class InputSchema(schema.Base):
    local: Optional[LocalProvider] = None
    existing: Optional[ExistingProvider] = None
    google_cloud_platform: Optional[GoogleCloudPlatformProvider] = None
    amazon_web_services: Optional[AmazonWebServicesProvider] = None
    azure: Optional[AzureProvider] = None
    digital_ocean: Optional[DigitalOceanProvider] = None

    @model_validator(mode="before")
    @classmethod
    def check_provider(cls, data: Any) -> Any:
        if "provider" in data:
            provider: str = data["provider"]
            if hasattr(schema.ProviderEnum, provider):
                # TODO: all cloud providers has required fields, but local and existing don't.
                #  And there is no way to initialize a model without user input here.
                #  We preserve the original behavior here, but we should find a better way to do this.
                if provider in ["local", "existing"] and provider not in data:
                    data[provider] = provider_enum_model_map[provider]()
            else:
                # if the provider field is invalid, it won't be set when this validator is called
                # so we need to check for it explicitly here, and set the `pre` to True
                # TODO: this is a workaround, check if there is a better way to do this in Pydantic v2
                raise ValueError(
                    f"'{provider}' is not a valid enumeration member; permitted: local, existing, do, aws, gcp, azure"
                )
        else:
            set_providers = [
                provider
                for provider in provider_name_abbreviation_map.keys()
                if provider in data
            ]
            num_providers = len(set_providers)
            if num_providers > 1:
                raise ValueError(f"Multiple providers set: {set_providers}")
            elif num_providers == 1:
                data["provider"] = provider_name_abbreviation_map[set_providers[0]]
            elif num_providers == 0:
                data["provider"] = schema.ProviderEnum.local.value
        return data


class NodeSelectorKeyValue(schema.Base):
    key: str
    value: str


class KubernetesCredentials(schema.Base):
    host: str
    cluster_ca_certifiate: str  # ignored for now.  More info in https://github.com/nebari-dev/nebari/issues/2597. # typos: ignore
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_certificate: Optional[str] = None
    client_key: Optional[str] = None
    config_path: Optional[str] = None
    config_context: Optional[str] = None


class OutputSchema(schema.Base):
    node_selectors: Dict[str, NodeSelectorKeyValue]
    kubernetes_credentials: KubernetesCredentials
    kubeconfig_filename: str
    nfs_endpoint: Optional[str] = None


class KubernetesInfrastructureStage(NebariTerraformStage):
    """Generalized method to provision infrastructure.

    After successful deployment the following properties are set on
    `stage_outputs[directory]`.
      - `kubernetes_credentials` which are sufficient credentials to
        connect with the kubernetes provider
      - `kubeconfig_filename` which is a path to a kubeconfig that can
        be used to connect to a kubernetes cluster
      - at least one node running such that resources in the
        node_group.general can be scheduled

    At a high level this stage is expected to provision a kubernetes
    cluster on a given provider.
    """

    name = "02-infrastructure"
    priority = 20

    input_schema = InputSchema
    output_schema = OutputSchema

    @property
    def template_directory(self):
        return (
            pathlib.Path(inspect.getfile(self.__class__)).parent
            / "template"
            / self.config.provider.value
        )

    @property
    def stage_prefix(self):
        return pathlib.Path("stages") / self.name / self.config.provider.value

    def state_imports(self) -> List[Tuple[str, str]]:
        if self.config.provider == schema.ProviderEnum.azure:
            if self.config.azure.resource_group_name is None:
                return []

            subscription_id = os.environ["ARM_SUBSCRIPTION_ID"]
            resource_group_name = construct_azure_resource_group_name(
                project_name=self.config.project_name,
                namespace=self.config.namespace,
                base_resource_group_name=self.config.azure.resource_group_name,
            )
            resource_url = (
                f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
            )
            return [
                (
                    "azurerm_resource_group.resource_group",
                    resource_url,
                )
            ]

    def tf_objects(self) -> List[Dict]:
        if self.config.provider == schema.ProviderEnum.gcp:
            return [
                terraform.Provider(
                    "google",
                    project=self.config.google_cloud_platform.project,
                    region=self.config.google_cloud_platform.region,
                ),
                NebariTerraformState(self.name, self.config),
            ]
        elif self.config.provider == schema.ProviderEnum.do:
            return [
                NebariTerraformState(self.name, self.config),
            ]
        elif self.config.provider == schema.ProviderEnum.azure:
            return [
                NebariTerraformState(self.name, self.config),
            ]
        elif self.config.provider == schema.ProviderEnum.aws:
            return [
                terraform.Provider(
                    "aws", region=self.config.amazon_web_services.region
                ),
                NebariTerraformState(self.name, self.config),
            ]
        else:
            return []

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.local:
            return LocalInputVars(
                kube_context=self.config.local.kube_context
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.existing:
            return ExistingInputVars(
                kube_context=self.config.existing.kube_context
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.do:
            return DigitalOceanInputVars(
                name=self.config.escaped_project_name,
                environment=self.config.namespace,
                region=self.config.digital_ocean.region,
                tags=self.config.digital_ocean.tags,
                kubernetes_version=self.config.digital_ocean.kubernetes_version,
                node_groups=self.config.digital_ocean.node_groups,
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.gcp:
            return GCPInputVars(
                name=self.config.escaped_project_name,
                environment=self.config.namespace,
                region=self.config.google_cloud_platform.region,
                project_id=self.config.google_cloud_platform.project,
                availability_zones=self.config.google_cloud_platform.availability_zones,
                node_groups=[
                    GCPNodeGroupInputVars(
                        name=name,
                        labels=node_group.labels,
                        instance_type=node_group.instance,
                        min_size=node_group.min_nodes,
                        max_size=node_group.max_nodes,
                        preemptible=node_group.preemptible,
                        guest_accelerators=node_group.guest_accelerators,
                    )
                    for name, node_group in self.config.google_cloud_platform.node_groups.items()
                ],
                tags=self.config.google_cloud_platform.tags,
                kubernetes_version=self.config.google_cloud_platform.kubernetes_version,
                release_channel=self.config.google_cloud_platform.release_channel,
                networking_mode=self.config.google_cloud_platform.networking_mode,
                network=self.config.google_cloud_platform.network,
                subnetwork=self.config.google_cloud_platform.subnetwork,
                ip_allocation_policy=self.config.google_cloud_platform.ip_allocation_policy,
                master_authorized_networks_config=self.config.google_cloud_platform.master_authorized_networks_config,
                private_cluster_config=self.config.google_cloud_platform.private_cluster_config,
                node_group_image_type=(
                    GCPNodeGroupImageTypeEnum.UBUNTU_CONTAINERD
                    if self.config.storage.type == SharedFsEnum.cephfs
                    else GCPNodeGroupImageTypeEnum.COS_CONTAINERD
                ),
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.azure:
            return AzureInputVars(
                name=self.config.escaped_project_name,
                environment=self.config.namespace,
                region=self.config.azure.region,
                kubernetes_version=self.config.azure.kubernetes_version,
                node_groups={
                    name: AzureNodeGroupInputVars(
                        instance=node_group.instance,
                        min_nodes=node_group.min_nodes,
                        max_nodes=node_group.max_nodes,
                    )
                    for name, node_group in self.config.azure.node_groups.items()
                },
                resource_group_name=construct_azure_resource_group_name(
                    project_name=self.config.project_name,
                    namespace=self.config.namespace,
                    base_resource_group_name=self.config.azure.resource_group_name,
                ),
                node_resource_group_name=construct_azure_resource_group_name(
                    project_name=self.config.project_name,
                    namespace=self.config.namespace,
                    base_resource_group_name=self.config.azure.resource_group_name,
                    suffix=AZURE_NODE_RESOURCE_GROUP_SUFFIX,
                ),
                vnet_subnet_id=self.config.azure.vnet_subnet_id,
                private_cluster_enabled=self.config.azure.private_cluster_enabled,
                tags=self.config.azure.tags,
                network_profile=self.config.azure.network_profile,
                max_pods=self.config.azure.max_pods,
                workload_identity_enabled=self.config.azure.workload_identity_enabled,
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.aws:
            return AWSInputVars(
                name=self.config.escaped_project_name,
                environment=self.config.namespace,
                eks_endpoint_access=self.config.amazon_web_services.eks_endpoint_access,
                existing_subnet_ids=self.config.amazon_web_services.existing_subnet_ids,
                existing_security_group_id=self.config.amazon_web_services.existing_security_group_id,
                region=self.config.amazon_web_services.region,
                kubernetes_version=self.config.amazon_web_services.kubernetes_version,
                node_groups=[
                    AWSNodeGroupInputVars(
                        name=name,
                        instance_type=node_group.instance,
                        gpu=node_group.gpu,
                        min_size=node_group.min_nodes,
                        desired_size=node_group.min_nodes,
                        max_size=node_group.max_nodes,
                        single_subnet=node_group.single_subnet,
                        permissions_boundary=node_group.permissions_boundary,
                    )
                    for name, node_group in self.config.amazon_web_services.node_groups.items()
                ],
                availability_zones=self.config.amazon_web_services.availability_zones,
                vpc_cidr_block=self.config.amazon_web_services.vpc_cidr_block,
                permissions_boundary=self.config.amazon_web_services.permissions_boundary,
                tags=self.config.amazon_web_services.tags,
                efs_enabled=self.config.storage.type == SharedFsEnum.efs,
            ).model_dump()
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException

        config.load_kube_config(
            config_file=stage_outputs["stages/02-infrastructure"][
                "kubeconfig_filename"
            ]["value"]
        )

        try:
            api_instance = client.CoreV1Api()
            result = api_instance.list_namespace()
        except ApiException:
            print(
                f"ERROR: After stage={self.name} unable to connect to kubernetes cluster"
            )
            sys.exit(1)

        if len(result.items) < 1:
            print(
                f"ERROR: After stage={self.name} no nodes provisioned within kubernetes cluster"
            )
            sys.exit(1)

        print(f"After stage={self.name} kubernetes cluster successfully provisioned")

    def set_outputs(
        self, stage_outputs: Dict[str, Dict[str, Any]], outputs: Dict[str, Any]
    ):
        outputs["node_selectors"] = _calculate_node_groups(self.config)
        super().set_outputs(stage_outputs, outputs)

    @contextlib.contextmanager
    def post_deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        asg_node_group_map = _calculate_asg_node_group_map(self.config)
        if asg_node_group_map:
            amazon_web_services.set_asg_tags(
                asg_node_group_map, self.config.amazon_web_services.region
            )

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        with super().deploy(stage_outputs, disable_prompt):
            with kubernetes_provider_context(
                stage_outputs["stages/" + self.name]["kubernetes_credentials"]["value"]
            ):
                yield

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        with super().destroy(stage_outputs, status):
            with kubernetes_provider_context(
                stage_outputs["stages/" + self.name]["kubernetes_credentials"]["value"]
            ):
                yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesInfrastructureStage]
