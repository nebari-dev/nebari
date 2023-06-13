from typing import List, Dict
import pathlib
import sys

from nebari.hookspecs import NebariStage, hookimpl
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import NebariTerraformState, NebariKubernetesProvider, NebariHelmProvider

from _nebari import schema


class NebariTFExtensionsStage(NebariTerraformStage):
    @property
    def name(self):
        return "08-nebari-tf-extensions"

    @property
    def priority(self):
        return 80

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
            "tf_extensions": self.config.tf_extensions,
            "nebari_config_yaml": self.config,
            "keycloak_nebari_bot_password": stage_outputs["stages/05-kubernetes-keycloak"][
                "keycloak_nebari_bot_password"
            ]["value"],
            "helm_extensions": self.config.helm_extensions,
        }


@hookimpl
def nebari_stage(install_directory: pathlib.Path, config: schema.Main) -> List[NebariStage]:
    return [
        NebariTFExtensionsStage(
            install_directory,
            config,
            template_directory=(pathlib.Path(__file__).parent / "template"),
            stage_prefix=pathlib.Path("stages/08-nebari-tf-extensions"),
        )
    ]
