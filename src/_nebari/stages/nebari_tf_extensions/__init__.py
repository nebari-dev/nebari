from typing import Any, Dict, List

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari.hookspecs import NebariStage, hookimpl


class NebariTFExtensionsStage(NebariTerraformStage):
    name = "08-nebari-tf-extensions"
    priority = 80

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
