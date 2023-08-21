import contextlib
import enum
import json
import secrets
import string
import sys
import time
import typing
from abc import ABC
from typing import Any, Dict, List

import pydantic

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


@schema.yaml_object(schema.yaml)
class AuthenticationEnum(str, enum.Enum):
    password = "password"
    github = "GitHub"
    auth0 = "Auth0"
    custom = "custom"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class GitHubConfig(schema.Base):
    client_id: str
    client_secret: str


class Auth0Config(schema.Base):
    client_id: str
    client_secret: str
    auth0_subdomain: str


class Authentication(schema.Base, ABC):
    _types: typing.Dict[str, type] = {}

    type: AuthenticationEnum

    # Based on https://github.com/samuelcolvin/pydantic/issues/2177#issuecomment-739578307

    # This allows type field to determine which subclass of Authentication should be used for validation.

    # Used to register automatically all the submodels in `_types`.
    def __init_subclass__(cls):
        cls._types[cls._typ.value] = cls

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: typing.Dict[str, typing.Any]) -> "Authentication":
        if "type" not in value:
            raise ValueError("type field is missing from security.authentication")

        specified_type = value.get("type")
        sub_class = cls._types.get(specified_type, None)

        if not sub_class:
            raise ValueError(
                f"No registered Authentication type called {specified_type}"
            )

        # init with right submodel
        return sub_class(**value)


def random_secure_string(
    length: int = 16, chars: str = string.ascii_lowercase + string.digits
):
    return "".join(secrets.choice(chars) for i in range(length))


class PasswordAuthentication(Authentication):
    _typ = AuthenticationEnum.password


class Auth0Authentication(Authentication):
    _typ = AuthenticationEnum.auth0
    config: Auth0Config


class GitHubAuthentication(Authentication):
    _typ = AuthenticationEnum.github
    config: GitHubConfig


class Keycloak(schema.Base):
    initial_root_password: str = pydantic.Field(default_factory=random_secure_string)
    overrides: typing.Dict = {}
    realm_display_name: str = "Nebari"


class Security(schema.Base):
    authentication: Authentication = PasswordAuthentication(
        type=AuthenticationEnum.password
    )
    shared_users_group: bool = True
    keycloak: Keycloak = Keycloak()


class InputSchema(schema.Base):
    security: Security = Security()


class KeycloakCredentials(schema.Base):
    url: str
    client_id: str
    realm: str
    username: str
    password: str


class OutputSchema(schema.Base):
    keycloak_credentials: KeycloakCredentials
    keycloak_nebari_bot_password: str


class KubernetesKeycloakStage(NebariTerraformStage):
    name = "05-kubernetes-keycloak"
    priority = 50

    input_schema = InputSchema
    output_schema = OutputSchema

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
