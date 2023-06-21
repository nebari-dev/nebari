import contextlib
import json
import sys
import time
from typing import Any, Dict, List

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from _nebari.utils import modified_environ
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

NUM_ATTEMPTS = 10
TIMEOUT = 10


class InputVars(schema.Base):
    name: str
    environment: str
    endpoint: str
    initial_root_password: str
    overrides: List[str]
    node_group: Dict[str, str]


@contextlib.contextmanager
def keycloak_provider_context(keycloak_credentials: Dict[str, str]):
    credential_mapping = {
        "client_id": "KEYCLOAK_CLIENT_ID",
        "url": "KEYCLOAK_URL",
        "username": "KEYCLOAK_USER",
        "password": "KEYCLOAK_PASSWORD",
        "realm": "KEYCLOAK_REALM",
    }

    credentials = {credential_mapping[k]: v for k, v in keycloak_credentials.items()}
    with modified_environ(**credentials):
        yield


class KubernetesKeycloakStage(NebariTerraformStage):
    name = "05-kubernetes-keycloak"
    priority = 50

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return InputVars(
            name=self.config.project_name,
            environment=self.config.namespace,
            endpoint=stage_outputs["stages/04-kubernetes-ingress"]["domain"],
            initial_root_password=self.config.security.keycloak.initial_root_password,
            overrides=[json.dumps(self.config.security.keycloak.overrides)],
            node_group=stage_outputs["stages/02-infrastructure"]["node_selectors"][
                "general"
            ],
        ).dict()

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
        from keycloak import KeycloakAdmin
        from keycloak.exceptions import KeycloakError

        keycloak_url = f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"

        def _attempt_keycloak_connection(
            keycloak_url,
            username,
            password,
            realm_name,
            client_id,
            verify=False,
            num_attempts=NUM_ATTEMPTS,
            timeout=TIMEOUT,
        ):
            for i in range(num_attempts):
                try:
                    KeycloakAdmin(
                        keycloak_url,
                        username=username,
                        password=password,
                        realm_name=realm_name,
                        client_id=client_id,
                        verify=verify,
                    )
                    print(
                        f"Attempt {i+1} succeeded connecting to keycloak master realm"
                    )
                    return True
                except KeycloakError:
                    print(f"Attempt {i+1} failed connecting to keycloak master realm")
                time.sleep(timeout)
            return False

        if not _attempt_keycloak_connection(
            keycloak_url,
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "username"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "password"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "realm"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "client_id"
            ],
            verify=False,
        ):
            print(
                f"ERROR: unable to connect to keycloak master realm at url={keycloak_url} with root credentials"
            )
            sys.exit(1)

        print("Keycloak service successfully started")

    @contextlib.contextmanager
    def deploy(self, stage_outputs: Dict[str, Dict[str, Any]]):
        with super().deploy(stage_outputs):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"]
            ):
                yield

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        with super().destroy(stage_outputs, status):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"]
            ):
                yield


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [KubernetesKeycloakStage]
