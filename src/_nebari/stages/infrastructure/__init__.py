import contextlib
import inspect
import pathlib
import sys
import tempfile
from typing import Any, Dict, List, Optional

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariAWSProvider,
    NebariGCPProvider,
    NebariTerraformState,
)
from _nebari.utils import modified_environ
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


def get_kubeconfig_filename():
    return str(pathlib.Path(tempfile.gettempdir()) / "NEBARI_KUBECONFIG")


# TODO:
# - create schema for node group for each provider


class LocalInputVars(schema.Base):
    kubeconfig_filename: str = get_kubeconfig_filename()
    kube_context: Optional[str]


class ExistingInputVars(schema.Base):
    kube_context: str


class BaseCloudProviderInputVars(schema.Base):
    name: str
    environment: str
    kubeconfig_filename: str = get_kubeconfig_filename()


class DigitalOceanInputVars(BaseCloudProviderInputVars, schema.DigitalOceanProvider):
    pass


class GCPGuestAccelerators(schema.Base):
    type: str
    count: int


class GCPNodeGroupInputVars(schema.Base):
    name: str
    instance_type: str
    min_size: int
    max_size: int
    labels: Dict[str, str] = {}
    preemptible: bool = False
    guest_accelerators: List[GCPGuestAccelerators]


class GCPPrivateClusterConfig(schema.Base):
    enable_private_nodes: bool
    enable_private_endpoint: bool
    master_ipv4_cidr_block: str


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
    subnetwork: str = None
    ip_allocation_policy: Dict[str, str] = None
    master_authorized_networks_config: Dict[str, str] = None
    private_cluster_config: GCPPrivateClusterConfig = None


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
    vnet_subnet_id: str = None
    private_cluster_enabled: bool


class AWSNodeGroupInputVars(schema.Base):
    name: str
    instance_type: str
    gpu: bool = False
    min_size: int
    desired_size: int
    max_size: int
    single_subnet: bool


class AWSInputVars(schema.Base):
    name: str
    environment: str
    existing_security_group_id: str = None
    existing_subnet_ids: List[str] = None
    region: str
    kubernetes_version: str
    node_groups: List[AWSNodeGroupInputVars]
    availability_zones: List[str]
    vpc_cidr_block: str
    kubeconfig_filename: str = get_kubeconfig_filename()


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

    def tf_objects(self) -> List[Dict]:
        if self.config.provider == schema.ProviderEnum.gcp:
            return [
                NebariGCPProvider(self.config),
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
                NebariAWSProvider(self.config),
                NebariTerraformState(self.name, self.config),
            ]
        else:
            return []

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.local:
            return LocalInputVars(kube_context=self.config.local.kube_context).dict()
        elif self.config.provider == schema.ProviderEnum.existing:
            return ExistingInputVars(
                kube_context=self.config.existing.kube_context
            ).dict()
        elif self.config.provider == schema.ProviderEnum.do:
            return DigitalOceanInputVars(
                name=self.config.project_name,
                environment=self.config.namespace,
                region=self.config.digital_ocean.region,
                tags=self.config.digital_ocean.tags,
                kubernetes_version=self.config.digital_ocean.kubernetes_version,
                node_groups=self.config.digital_ocean.node_groups,
            ).dict()
        elif self.config.provider == schema.ProviderEnum.gcp:
            return GCPInputVars(
                name=self.config.project_name,
                environment=self.config.namespace,
                region=self.config.google_cloud_platform.region,
                project_id=self.config.google_cloud_platform.project,
                availability_zones=self.config.google_cloud_platform.availability_zones,
                node_groups=[
                    GCPNodeGroupInputVars(
                        name=name,
                        instance_type=node_group.instance,
                        min_size=node_group.min_nodes,
                        max_size=node_group.max_nodes,
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
            ).dict()
        elif self.config.provider == schema.ProviderEnum.azure:
            return AzureInputVars(
                name=self.config.project_name,
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
                resource_group_name=f"{self.config.project_name}-{self.config.namespace}",
                node_resource_group_name=f"{self.config.project_name}-{self.config.namespace}-node-resource-group",
                vnet_subnet_id=self.config.azure.vnet_subnet_id,
                private_cluster_enabled=self.config.azure.private_cluster_enabled,
            ).dict()
        elif self.config.provider == schema.ProviderEnum.aws:
            return AWSInputVars(
                name=self.config.project_name,
                environment=self.config.namespace,
                existing_subnet_ids=self.config.amazon_web_services.existing_subnet_ids,
                existing_security_group_id=self.config.amazon_web_services.existing_security_group_ids,
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
                    )
                    for name, node_group in self.config.amazon_web_services.node_groups.items()
                ],
                availability_zones=self.config.amazon_web_services.availability_zones,
                vpc_cidr_block=self.config.amazon_web_services.vpc_cidr_block,
            ).dict()
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
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

    @contextlib.contextmanager
    def deploy(self, stage_outputs: Dict[str, Dict[str, Any]]):
        with super().deploy(stage_outputs):
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
def nebari_stage() -> List[NebariStage]:
    return [KubernetesInfrastructureStage]
