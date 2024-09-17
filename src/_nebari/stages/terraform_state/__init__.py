import contextlib
import enum
import inspect
import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import field_validator

from _nebari import utils
from _nebari.provider import terraform
from _nebari.provider.cloud import azure_cloud
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import NebariConfig
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
    tags: Dict[str, str]

    @field_validator("state_resource_group_name")
    @classmethod
    def _validate_resource_group_name(cls, value: str) -> str:
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

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: Dict[str, str]) -> Dict[str, str]:
        return azure_cloud.validate_tags(value)


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
    backend: Optional[str] = None
    config: Dict[str, str] = {}


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
        resources = [NebariConfig(self.config)]
        if self.config.provider == schema.ProviderEnum.gcp:
            return resources + [
                terraform.Provider(
                    "google",
                    project=self.config.google_cloud_platform.project,
                    region=self.config.google_cloud_platform.region,
                ),
            ]
        elif self.config.provider == schema.ProviderEnum.aws:
            return resources + [
                terraform.Provider(
                    "aws", region=self.config.amazon_web_services.region
                ),
            ]
        else:
            return resources

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        if self.config.provider == schema.ProviderEnum.do:
            return DigitalOceanInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
                region=self.config.digital_ocean.region,
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.gcp:
            return GCPInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
                region=self.config.google_cloud_platform.region,
            ).model_dump()
        elif self.config.provider == schema.ProviderEnum.aws:
            return AWSInputVars(
                name=self.config.project_name,
                namespace=self.config.namespace,
            ).model_dump()
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
            ).model_dump()
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
        self.check_immutable_fields()

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

    def check_immutable_fields(self):
        nebari_config_state = self.get_nebari_config_state()
        if not nebari_config_state:
            return

        # compute diff of remote/prior and current nebari config
        nebari_config_diff = utils.JsonDiff(
            nebari_config_state.model_dump(), self.config.model_dump()
        )

        # check if any changed fields are immutable
        for keys, old, new in nebari_config_diff.modified():
            bottom_level_schema = self.config
            if len(keys) > 1:
                for key in keys[:-1]:
                    try:
                        bottom_level_schema = getattr(bottom_level_schema, key)
                    except AttributeError as e:
                        if isinstance(bottom_level_schema, dict):
                            # handle case where value is a dict
                            bottom_level_schema = bottom_level_schema[key]
                        else:
                            raise e
            extra_field_schema = schema.ExtraFieldSchema(
                **bottom_level_schema.model_fields[keys[-1]].json_schema_extra or {}
            )
            if extra_field_schema.immutable:
                key_path = ".".join(keys)
                raise ValueError(
                    f'Attempting to change immutable field "{key_path}" ("{old}"->"{new}") in Nebari config file.  Immutable fields cannot be changed after initial deployment.'
                )

    def get_nebari_config_state(self):
        directory = str(self.output_directory / self.stage_prefix)
        tf_state = terraform.show(directory)
        nebari_config_state = None

        # get nebari config from state
        for resource in (
            tf_state.get("values", {}).get("root_module", {}).get("resources", [])
        ):
            if resource["address"] == "terraform_data.nebari_config":
                from nebari.plugins import nebari_plugin_manager

                nebari_config_state = nebari_plugin_manager.config_schema(
                    **resource["values"]["input"]
                )
                break
        return nebari_config_state

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
