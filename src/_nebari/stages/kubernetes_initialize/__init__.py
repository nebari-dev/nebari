import sys
from typing import Any, Dict, List

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class KubernetesInitializeStage(NebariTerraformStage):
    name = "03-kubernetes-initialize"
    priority = 30

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.gcp:
            gpu_enabled = any(
                node_group.guest_accelerators
                for node_group in self.config.google_cloud_platform.node_groups.values()
            )
            gpu_node_group_names = []

        elif self.config.provider == schema.ProviderEnum.aws:
            gpu_enabled = any(
                node_group.gpu
                for node_group in self.config.amazon_web_services.node_groups.values()
            )
            gpu_node_group_names = [
                group for group in self.config.amazon_web_services.node_groups.keys()
            ]
        else:
            gpu_enabled = False
            gpu_node_group_names = []

        return {
            "name": self.config.project_name,
            "environment": self.config.namespace,
            "cloud-provider": self.config.provider.value,
            "aws-region": self.config.amazon_web_services.region if self.config.provider == schema.ProviderEnum.aws else None,
            "external_container_reg": self.config.external_container_reg.dict(),
            "gpu_enabled": gpu_enabled,
            "gpu_node_group_names": gpu_node_group_names,
        }

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

        namespaces = {_.metadata.name for _ in result.items}
        if self.config.namespace not in namespaces:
            self.log.error(
                f"ERROR: After stage={self.name} namespace={self.config.namespace} not provisioned within kubernetes cluster"
            )
            sys.exit(1)

        self.log.info(f"After stage={self.name} kubernetes initialized successfully")


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [KubernetesInitializeStage]
