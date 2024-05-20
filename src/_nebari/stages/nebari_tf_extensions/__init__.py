from typing import Any, Dict, List, Optional, Type

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


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
    logout: Optional[str] = None
    envs: Optional[List[NebariExtensionEnv]] = None


class HelmExtension(schema.Base):
    name: str
    repository: str
    chart: str
    version: str
    overrides: Dict = {}


class InputSchema(schema.Base):
    helm_extensions: List[HelmExtension] = []
    tf_extensions: List[NebariExtension] = []


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
            "tf_extensions": [_.model_dump() for _ in self.config.tf_extensions],
            "nebari_config_yaml": self.config.model_dump(),
            "keycloak_nebari_bot_password": stage_outputs[
                "stages/05-kubernetes-keycloak"
            ]["keycloak_nebari_bot_password"]["value"],
            "helm_extensions": [_.model_dump() for _ in self.config.helm_extensions],
            "forwardauth_middleware_name": stage_outputs[
                "stages/07-kubernetes-services"
            ]["forward-auth-middleware"]["value"]["name"],
        }


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [NebariTFExtensionsStage]
