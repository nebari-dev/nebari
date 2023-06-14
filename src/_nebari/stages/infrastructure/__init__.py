import contextlib
import pathlib
import sys
from typing import Any, Dict, List

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariAWSProvider,
    NebariGCPProvider,
    NebariTerraformState,
)
from _nebari.utils import modified_environ
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


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
    name = "02-infrastructure"
    priority = 20

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
            return {
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "NEBARI_KUBECONFIG"
                ),
                "kube_context": self.config.local.kube_context,
            }
        elif self.config.provider == schema.ProviderEnum.existing:
            return {"kube_context": self.config.existing.kube_context}
        elif self.config.provider == schema.ProviderEnum.do:
            return {
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "region": self.config.digital_ocean.region,
                "kubernetes_version": self.config.digital_ocean.kubernetes_version,
                "node_groups": self.config.digital_ocean.node_groups,
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "NEBARI_KUBECONFIG"
                ),
                **self.config.do.terraform_overrides,
            }
        elif self.config.provider == schema.ProviderEnum.gcp:
            return {
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "region": self.config.google_cloud_platform.region,
                "project_id": self.config.google_cloud_platform.project,
                "kubernetes_version": self.config.google_cloud_platform.kubernetes_version,
                "release_channel": self.config.google_cloud_platform.release_channel,
                "node_groups": [
                    {
                        "name": key,
                        "instance_type": value["instance"],
                        "min_size": value["min_nodes"],
                        "max_size": value["max_nodes"],
                        "guest_accelerators": value["guest_accelerators"]
                        if "guest_accelerators" in value
                        else [],
                        **value,
                    }
                    for key, value in self.config.google_cloud_platform.node_groups.items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "NEBARI_KUBECONFIG"
                ),
                **self.config.gcp.terraform_overrides,
            }
        elif self.config.provider == schema.ProviderEnum.azure:
            return {
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "region": self.config.azure.region,
                "kubernetes_version": self.config.azure.kubernetes_version,
                "node_groups": self.config.azure.node_groups,
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "NEBARI_KUBECONFIG"
                ),
                "resource_group_name": f"{self.config.project_name}-{self.config.namespace}",
                "node_resource_group_name": f"{self.config.project_name}-{self.config.namespace}-node-resource-group",
                **self.config.azure.terraform_overrides,
            }
        elif self.config.provider == schema.ProviderEnum.aws:
            return {
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "region": self.config.amazon_web_services.region,
                "kubernetes_version": self.config.amazon_web_services.kubernetes_version,
                "node_groups": [
                    {
                        "name": key,
                        "min_size": value["min_nodes"],
                        "desired_size": max(value["min_nodes"], 1),
                        "max_size": value["max_nodes"],
                        "gpu": value.get("gpu", False),
                        "instance_type": value["instance"],
                        "single_subnet": value.get("single_subnet", False),
                    }
                    for key, value in self.config.amazon_web_services.node_groups.items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "NEBARI_KUBECONFIG"
                ),
                **self.config.amazon_web_services.terraform_overrides,
            }
        else:
            return {}

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
            self.log.error(
                f"ERROR: After stage={self.name} unable to connect to kubernetes cluster"
            )
            sys.exit(1)

        if len(result.items) < 1:
            self.log.error(
                f"ERROR: After stage={self.name} no nodes provisioned within kubernetes cluster"
            )
            sys.exit(1)

        self.log.info(
            f"After stage={self.name} kubernetes cluster successfully provisioned"
        )

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
def nebari_stage(
    install_directory: pathlib.Path, config: schema.Main
) -> List[NebariStage]:
    template_directory = (
        pathlib.Path(__file__).parent / "template" / config.provider.value
    )
    stage_prefix = pathlib.Path("stages/02-infrastructure") / config.provider.value

    return [
        KubernetesInfrastructureStage(
            install_directory,
            config,
            template_directory=template_directory,
            stage_prefix=stage_prefix,
        )
    ]
