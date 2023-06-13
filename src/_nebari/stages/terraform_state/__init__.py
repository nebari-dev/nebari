import os
import pathlib
from typing import List, Tuple

from _nebari import schema
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari.hookspecs import NebariStage, hookimpl


class KubernetesInitializeStage(NebariTerraformStage):
    @property
    def name(self):
        return "01-terraform-state"

    @property
    def priority(self):
        return 10

    def state_imports(self) -> List[Tuple[str, str]]:
        if self.config.provider == schema.ProviderEnum.do:
            return [
                (
                    "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                    f"{self.config.digital_ocean.region},{self.config.project_name}-{self.config.namespace}-terraform-state",
                )
            ]
        elif self.config.provider == schema.ProviderEnum.gcp:
            return [
                (
                    "module.terraform-state.module.gcs.google_storage_bucket.static-site",
                    f"{self.config.project_name}-{self.config.namespace}-terraform-state",
                )
            ]
        elif self.config.provider == schema.ProviderEnum.azure:
            subscription_id = os.environ["ARM_SUBSCRIPTION_ID"]
            resource_name_prefix = f"{self.config.project_name}-{self.config.namespace}"
            state_resource_group_name = f"{resource_name_prefix}-state"
            state_resource_name_prefix_safe = resource_name_prefix.replace("-", "")
            resource_group_url = f"/subscriptions/{subscription_id}/resourceGroups/{state_resource_group_name}"

            return [
                (
                    "module.terraform-state.azurerm_resource_group.terraform-state-resource-group",
                    resource_group_url,
                ),
                (
                    "module.terraform-state.azurerm_storage_account.terraform-state-storage-account",
                    f"{resource_group_url}/providers/Microsoft.Storage/storageAccounts/{state_resource_name_prefix_safe}{self.config.azure.storage_account_postfix}",
                ),
                (
                    "module.terraform-state.azurerm_storage_container.storage_container",
                    f"https://{state_resource_name_prefix_safe}{self.config.azure.storage_account_postfix}.blob.core.windows.net/{resource_name_prefix}-state",
                ),
            ]
        elif self.config.provider == schema.ProviderEnum.aws:
            return [
                (
                    "module.terraform-state.aws_s3_bucket.terraform-state",
                    f"{self.config.project_name}-{self.config.namespace}-terraform-state",
                ),
                (
                    "module.terraform-state.aws_dynamodb_table.terraform-state-lock",
                    f"{self.config.project_name}-{self.config.namespace}-terraform-state-lock",
                ),
            ]

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.do:
            return {
                "name": self.config.project_name,
                "namespace": self.config.namespace,
                "region": self.config.digital_ocean.region,
            }
        elif self.config.provider == schema.ProviderEnum.gcp:
            return {
                "name": self.config.project_name,
                "namespace": self.config.namespace,
                "region": self.config.google_cloud_platform.region,
            }
        elif self.config.provider == schema.ProviderEnum.aws:
            return {
                "name": self.config.project_name,
                "namespace": self.config.namespace,
            }
        elif self.config.provider == schema.ProviderEnum.azure:
            return {
                "name": self.config.project_name,
                "namespace": self.config.namespace,
                "region": self.config.azure.region,
                "storage_account_postfix": self.config.azure.storage_account_postfix,
                "state_resource_group_name": f"{self.config.project_name}-{self.config.namespace}-state",
            }
        else:
            return {}


@hookimpl
def nebari_stage(
    install_directory: pathlib.Path, config: schema.Main
) -> List[NebariStage]:
    if config.provider in [schema.ProviderEnum.local, schema.ProviderEnum.existing]:
        return []

    template_directory = (
        pathlib.Path(__file__).parent / "template" / config.provider.value
    )
    stage_prefix = pathlib.Path("stages/01-terraform-state") / config.provider.value

    return [
        TerraformStateStage(
            install_directory,
            config,
            template_directory=template_directory,
            stage_prefix=stage_prefix,
        )
    ]
