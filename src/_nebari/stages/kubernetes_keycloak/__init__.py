import json
import pathlib
import sys
from typing import Dict, List

from _nebari import schema
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from _nebari.utils import modified_environ
from nebari.hookspecs import NebariStage, hookimpl


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


def _calculate_node_groups(config: schema.Main):
    if config.provider == schema.ProviderEnum.aws:
        return {
            group: {"key": "eks.amazonaws.com/nodegroup", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.gcp:
        return {
            group: {"key": "cloud.google.com/gke-nodepool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.azure:
        return {
            group: {"key": "azure-node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.do:
        return {
            group: {"key": "doks.digitalocean.com/node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.existing:
        return config.existing.node_selectors
    else:
        return config.local.node_selectors


class KubernetesKeycloakStage(NebariTerraformStage):
    @property
    def name(self):
        return "05-kubernetes-keycloak"

    @property
    def priority(self):
        return 50

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return {
            "name": self.config.project_name,
            "environment": self.config.namespace,
            "endpoint": self.config.domain,
            "initial-root-password": self.config.security.keycloak.initial_root_password,
            "overrides": [
                json.dumps(self.config.security.keycloak.overrides)
            ],
            "node-group": _calculate_node_groups(self.config)["general"],
        }


    def check(self, stage_outputs: stage_outputs: Dict[str, Dict[str, Any]]):
        from keycloak import KeycloakAdmin
        from keycloak.exceptions import KeycloakError

        keycloak_url = (
            f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"
        )

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
                    self.log.info(f"Attempt {i+1} succeeded connecting to keycloak master realm")
                    return True
                except KeycloakError:
                    self.log.info(f"Attempt {i+1} failed connecting to keycloak master realm")
                time.sleep(timeout)
            return False

        if not _attempt_keycloak_connection(
            keycloak_url,
            stage_outputs['stages/' + self.name]["keycloak_credentials"]["value"]["username"],
            stage_outputs['stages/' + self.name]["keycloak_credentials"]["value"]["password"],
            stage_outputs['stages/' + self.name]["keycloak_credentials"]["value"]["realm"],
            stage_outputs['stages/' + self.name]["keycloak_credentials"]["value"]["client_id"],
            verify=False,
        ):
            self.log.error(
                f"ERROR: unable to connect to keycloak master realm at url={keycloak_url} with root credentials"
            )
            sys.exit(1)

        self.log.info("Keycloak service successfully started")

    @contextlib.contextmanager
    def deploy(self, stage_outputs: Dict[str, Dict[str, Any]]):
        with super().deploy(stage_outputs):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"][
                    "value"
                ]
            ):
                yield

    @contextlib.contextmanager
    def destroy(self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]):
        with super().destroy(stage_outputs, status):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"][
                    "value"
                ]
            ):
                yield


@hookimpl
def nebari_stage(install_directory: pathlib.Path, config: schema.Main) -> [NebariStage]:
    return [
        KubernetesKeycloakStage(
            install_directory,
            config,
            template_directory=(pathlib.Path(__file__).parent / "template"),
            stage_prefix=pathlib.Path("stages/05-kubernetes-keycloak"),
        )
    ]
