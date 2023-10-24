import contextlib
import enum
import inspect
import os
import pathlib
import re
import typing
from typing import Any, Dict, List, Tuple, Type

import pydantic

from _nebari.provider import terraform
from _nebari.provider.cloud import azure_cloud
from _nebari.stages.base import NebariTerraformStage
from _nebari.utils import (
    AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
    construct_azure_resource_group_name,
    modified_environ,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class DigitalOceanInputVars(schema.Base):
    name: str
    namespace: str
    region: str


class GCPInputVars(schema.Base):
    name: str
    namespace: str
    region: str


class AzureInputVars(schema.Base):
    name: str
    namespace: str
    region: str
    storage_account_postfix: str
    state_resource_group_name: str
    tags: Dict[str, str] = {}

    @pydantic.validator("state_resource_group_name")
    def _validate_resource_group_name(cls, value):
        if value is None:
            return value
        length = len(value) + len(AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX)
        if length < 1 or length > 90:
            raise ValueError(
                f"Azure Resource Group name must be between 1 and 90 characters long, when combined with the suffix `{AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX}`."
            )
        if not re.match(r"^[\w\-\.\(\)]+$", value):
            raise ValueError(
                "Azure Resource Group name can only contain alphanumerics, underscores, parentheses, hyphens, and periods."
            )
        if value[-1] == ".":
            raise ValueError("Azure Resource Group name can't end with a period.")

        return value

    @pydantic.validator("tags")
    def _validate_tags(cls, tags):
        return azure_cloud.validate_tags(tags)


class AWSInputVars(schema.Base):
    name: str
    namespace: str


@schema.yaml_object(schema.yaml)
class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"
    existing = "existing"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class TerraformState(schema.Base):
    type: TerraformStateEnum = TerraformStateEnum.remote
    backend: typing.Optional[str]
    config: typing.Dict[str, str] = {}


class InputSchema(schema.Base):
    terraform_state: TerraformState = TerraformState()


class OutputSchema(schema.Base):
    pass


class TerraformStateStage(NebariTerraformStage):
    name = "01-terraform-state"
    priority = 10

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
            state_resource_group_name = construct_azure_resource_group_name(
                project_name=self.config.project_name,
                namespace=self.config.namespace,
                base_resource_group_name=self.config.azure.resource_group_name,
                suffix=AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
            )
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
        else:
            return []

    def tf_objects(self) -> List[Dict]:
        if self.config.provider == schema.ProviderEnum.gcp:
            return [
                terraform.Provider(
                    "google",
                    project=self.config.google_cloud_platform.project,
                    region=self.config.google_cloud_platform.region,
                ),
            ]
        elif self.config.provider == schema.ProviderEnum.aws:
            return [
                terraform.Provider(
                    "aws", region=self.config.amazon_web_services.region
                ),
            ]
        else:
            return []

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.do:
            return DigitalOceanInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
                region=self.config.digital_ocean.region,
            ).dict()
        elif self.config.provider == schema.ProviderEnum.gcp:
            return GCPInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
                region=self.config.google_cloud_platform.region,
            ).dict()
        elif self.config.provider == schema.ProviderEnum.aws:
            return AWSInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
            ).dict()
        elif self.config.provider == schema.ProviderEnum.azure:
            return AzureInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
                region=self.config.azure.region,
                storage_account_postfix=self.config.azure.storage_account_postfix,
                state_resource_group_name=construct_azure_resource_group_name(
                    project_name=self.config.project_name,
                    namespace=self.config.namespace,
                    base_resource_group_name=self.config.azure.resource_group_name,
                    suffix=AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
                ),
                tags=self.config.azure.tags,
            ).dict()
        elif (
            self.config.provider == schema.ProviderEnum.local
            or self.config.provider == schema.ProviderEnum.existing
        ):
            return {}
        else:
            ValueError(f"Unknown provider: {self.config.provider}")

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        with super().deploy(stage_outputs, disable_prompt):
            env_mapping = {}
            # DigitalOcean terraform remote state using Spaces Bucket
            # assumes aws credentials thus we set them to match spaces credentials
            if self.config.provider == schema.ProviderEnum.do:
                env_mapping.update(
                    {
                        "AWS_ACCESS_KEY_ID": os.environ["SPACES_ACCESS_KEY_ID"],
                        "AWS_SECRET_ACCESS_KEY": os.environ["SPACES_SECRET_ACCESS_KEY"],
                    }
                )

            with modified_environ(**env_mapping):
                yield

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        with super().destroy(stage_outputs, status):
            env_mapping = {}
            # DigitalOcean terraform remote state using Spaces Bucket
            # assumes aws credentials thus we set them to match spaces credentials
            if self.config.provider == schema.ProviderEnum.do:
                env_mapping.update(
                    {
                        "AWS_ACCESS_KEY_ID": os.environ["SPACES_ACCESS_KEY_ID"],
                        "AWS_SECRET_ACCESS_KEY": os.environ["SPACES_SECRET_ACCESS_KEY"],
                    }
                )

            with modified_environ(**env_mapping):
                yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [TerraformStateStage]
