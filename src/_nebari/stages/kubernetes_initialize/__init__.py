import sys
import typing
from typing import Any, Dict, List, Union

import pydantic

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.infrastructure import InfrastructureOutputSchema
from _nebari.stages.terraform_state import TerraformStateOutputSchema
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class ExtContainerReg(schema.Base):
    enabled: bool = False
    access_key_id: typing.Optional[str]
    secret_access_key: typing.Optional[str]
    extcr_account: typing.Optional[str]
    extcr_region: typing.Optional[str]

    @pydantic.root_validator
    def enabled_must_have_fields(cls, values):
        if values["enabled"]:
            for fldname in (
                "access_key_id",
                "secret_access_key",
                "extcr_account",
                "extcr_region",
            ):
                if (
                    fldname not in values
                    or values[fldname] is None
                    or values[fldname].strip() == ""
                ):
                    raise ValueError(
                        f"external_container_reg must contain a non-blank {fldname} when enabled is true"
                    )
        return values


class InputVars(schema.Base):
    name: str
    environment: str
    cloud_provider: str
    aws_region: Union[str, None] = None
    external_container_reg: Union[ExtContainerReg, None] = None
    gpu_enabled: bool = False
    gpu_node_group_names: List[str] = []


class InputSchema(schema.Base):
    external_container_reg: ExtContainerReg = ExtContainerReg()


class KubernetesInitializeStage(NebariTerraformStage):
    name = "03-kubernetes-initialize"
    priority = 30

    input_schema = InputSchema

    dependencies = [
        TerraformStateOutputSchema,
        InfrastructureOutputSchema,
    ]

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        input_vars = InputVars(
            name=self.config.project_name,
            environment=self.config.namespace,
            cloud_provider=self.config.provider.value,
            external_container_reg=self.config.external_container_reg.dict(),
        )

        if self.config.provider == schema.ProviderEnum.gcp:
            input_vars.gpu_enabled = any(
                node_group.guest_accelerators
                for node_group in self.config.google_cloud_platform.node_groups.values()
            )

        elif self.config.provider == schema.ProviderEnum.aws:
            input_vars.gpu_enabled = any(
                node_group.gpu
                for node_group in self.config.amazon_web_services.node_groups.values()
            )
            input_vars.gpu_node_group_names = [
                group for group in self.config.amazon_web_services.node_groups.keys()
            ]
            input_vars.aws_region = self.config.amazon_web_services.region

        return input_vars.dict()

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

        namespaces = {_.metadata.name for _ in result.items}
        if self.config.namespace not in namespaces:
            print(
                f"ERROR: After stage={self.name} namespace={self.config.namespace} not provisioned within kubernetes cluster"
            )
            sys.exit(1)

        print(f"After stage={self.name} kubernetes initialized successfully")


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [KubernetesInitializeStage]
