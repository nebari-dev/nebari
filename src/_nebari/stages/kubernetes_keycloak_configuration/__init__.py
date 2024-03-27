import sys
import time
from typing import Any, Dict, List, Type

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.kubernetes_keycloak import Authentication
from _nebari.stages.tf_objects import NebariTerraformState
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

NUM_ATTEMPTS = 10
TIMEOUT = 10


class InputVars(schema.Base):
    realm: str = "nebari"
    realm_display_name: str
    authentication: Authentication
    keycloak_groups: List[str] = ["superadmin", "admin", "developer", "analyst"]
    default_groups: List[str] = ["analyst"]


class KubernetesKeycloakConfigurationStage(NebariTerraformStage):
    name = "06-kubernetes-keycloak-configuration"
    priority = 60

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        input_vars = InputVars(
            realm_display_name=self.config.security.keycloak.realm_display_name,
            authentication=self.config.security.authentication,
        )

        users_group = ["users"] if self.config.security.shared_users_group else []

        input_vars.keycloak_groups += users_group
        input_vars.default_groups += users_group

        return input_vars.model_dump()

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        directory = "stages/05-kubernetes-keycloak"

        from keycloak import KeycloakAdmin
        from keycloak.exceptions import KeycloakError

        keycloak_url = (
            f"{stage_outputs[directory]['keycloak_credentials']['value']['url']}/auth/"
        )

        def _attempt_keycloak_connection(
            keycloak_url,
            username,
            password,
            realm_name,
            client_id,
            nebari_realm,
            verify=False,
            num_attempts=NUM_ATTEMPTS,
            timeout=TIMEOUT,
        ):
            for i in range(num_attempts):
                try:
                    realm_admin = KeycloakAdmin(
                        keycloak_url,
                        username=username,
                        password=password,
                        realm_name=realm_name,
                        client_id=client_id,
                        verify=verify,
                    )
                    existing_realms = {_["id"] for _ in realm_admin.get_realms()}
                    if nebari_realm in existing_realms:
                        print(
                            f"Attempt {i+1} succeeded connecting to keycloak and nebari realm={nebari_realm} exists"
                        )
                        return True
                    else:
                        print(
                            f"Attempt {i+1} succeeded connecting to keycloak but nebari realm did not exist"
                        )
                except KeycloakError:
                    print(f"Attempt {i+1} failed connecting to keycloak master realm")
                time.sleep(timeout)
            return False

        if not _attempt_keycloak_connection(
            keycloak_url,
            stage_outputs[directory]["keycloak_credentials"]["value"]["username"],
            stage_outputs[directory]["keycloak_credentials"]["value"]["password"],
            stage_outputs[directory]["keycloak_credentials"]["value"]["realm"],
            stage_outputs[directory]["keycloak_credentials"]["value"]["client_id"],
            nebari_realm=stage_outputs["stages/06-kubernetes-keycloak-configuration"][
                "realm_id"
            ]["value"],
            verify=False,
        ):
            print(
                "ERROR: unable to connect to keycloak master realm and ensure that nebari realm exists"
            )
            sys.exit(1)

        print("Keycloak service successfully started with nebari realm")


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesKeycloakConfigurationStage]
