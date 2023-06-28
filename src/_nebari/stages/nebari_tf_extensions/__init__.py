import typing
from typing import Any, Dict, List

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari.hookspecs import NebariStage, hookimpl
from nebari import schema


class NebariExtensionEnv(schema.Base):
    name: str
    value: str


class NebariExtension(schema.Base):
    name: str
    image: str
    urlslug: str
    private: bool = False
    oauth2client: bool = False
    keycloakadmin: bool = False
    jwt: bool = False
    nebariconfigyaml: bool = False
    logout: typing.Optional[str]
    envs: typing.Optional[typing.List[NebariExtensionEnv]]


class HelmExtension(schema.Base):
    name: str
    repository: str
    chart: str
    version: str
    overrides: typing.Dict = {}


class InputSchema(schema.Base):
    helm_extensions: typing.List[HelmExtension] = []
    tf_extensions: typing.List[NebariExtension] = []


class OutputSchema(schema.Base):
    pass


class NebariTFExtensionsStage(NebariTerraformStage):
    name = "08-nebari-tf-extensions"
    priority = 80

    input_schema = InputSchema
    output_schema = OutputSchema

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return {
            "environment": self.config.namespace,
            "endpoint": self.config.domain,
            "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
                "realm_id"
            ]["value"],
            "tf_extensions": [_.dict() for _ in self.config.tf_extensions],
            "nebari_config_yaml": self.config.dict(),
            "keycloak_nebari_bot_password": stage_outputs[
                "stages/05-kubernetes-keycloak"
            ]["keycloak_nebari_bot_password"]["value"],
            "helm_extensions": [_.dict() for _ in self.config.helm_extensions],
        }


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [NebariTFExtensionsStage]
