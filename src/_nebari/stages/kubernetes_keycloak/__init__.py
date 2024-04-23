import contextlib
import enum
import json
import os
import secrets
import string
import sys
import time
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import Field, ValidationInfo, field_validator

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

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class GitHubConfig(schema.Base):
    client_id: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_CLIENT_ID"),
        validate_default=True,
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_CLIENT_SECRET"),
        validate_default=True,
    )

    @field_validator("client_id", "client_secret", mode="before")
    @classmethod
    def validate_credentials(cls, value: Optional[str], info: ValidationInfo) -> str:
        variable_mapping = {
            "client_id": "GITHUB_CLIENT_ID",
            "client_secret": "GITHUB_CLIENT_SECRET",
        }
        if value is None:
            raise ValueError(
                f"Missing the following required environment variable: {variable_mapping[info.field_name]}"
            )
        return value


class Auth0Config(schema.Base):
    client_id: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_CLIENT_ID"),
        validate_default=True,
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_CLIENT_SECRET"),
        validate_default=True,
    )
    auth0_subdomain: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_DOMAIN"),
        validate_default=True,
    )

    @field_validator("client_id", "client_secret", "auth0_subdomain", mode="before")
    @classmethod
    def validate_credentials(cls, value: Optional[str], info: ValidationInfo) -> str:
        variable_mapping = {
            "client_id": "AUTH0_CLIENT_ID",
            "client_secret": "AUTH0_CLIENT_SECRET",
            "auth0_subdomain": "AUTH0_DOMAIN",
        }
        if value is None:
            raise ValueError(
                f"Missing the following required environment variable: {variable_mapping[info.field_name]} "
            )
        return value


class BaseAuthentication(schema.Base):
    type: AuthenticationEnum


class PasswordAuthentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.password


class Auth0Authentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.auth0
    config: Auth0Config = Field(default_factory=lambda: Auth0Config())


class GitHubAuthentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.github
    config: GitHubConfig = Field(default_factory=lambda: GitHubConfig())


Authentication = Union[
    PasswordAuthentication, Auth0Authentication, GitHubAuthentication
]


def random_secure_string(
    length: int = 16, chars: str = string.ascii_lowercase + string.digits
):
    return "".join(secrets.choice(chars) for i in range(length))


class Keycloak(schema.Base):
    initial_root_password: str = Field(default_factory=random_secure_string)
    overrides: Dict = {}
    realm_display_name: str = "Nebari"


auth_enum_to_model = {
    AuthenticationEnum.password: PasswordAuthentication,
    AuthenticationEnum.auth0: Auth0Authentication,
    AuthenticationEnum.github: GitHubAuthentication,
}

auth_enum_to_config = {
    AuthenticationEnum.auth0: Auth0Config,
    AuthenticationEnum.github: GitHubConfig,
}


class Security(schema.Base):
    authentication: Authentication = PasswordAuthentication()
    shared_users_group: bool = True
    keycloak: Keycloak = Keycloak()

    @field_validator("authentication", mode="before")
    @classmethod
    def validate_authentication(cls, value: Optional[Dict]) -> Authentication:
        if value is None:
            return PasswordAuthentication()
        if "type" not in value:
            raise ValueError(
                "Authentication type must be specified if authentication is set"
            )
        auth_type = value["type"] if hasattr(value, "__getitem__") else value.type
        if auth_type in auth_enum_to_model:
            if auth_type == AuthenticationEnum.password:
                return auth_enum_to_model[auth_type]()
            else:
                if "config" in value:
                    config_dict = (
                        value["config"]
                        if hasattr(value, "__getitem__")
                        else value.config
                    )
                    config = auth_enum_to_config[auth_type](**config_dict)
                else:
                    config = auth_enum_to_config[auth_type]()
                return auth_enum_to_model[auth_type](config=config)
        else:
            raise ValueError(f"Unsupported authentication type {auth_type}")


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
        ).model_dump()

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_check: bool = False
    ):
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
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        with super().deploy(stage_outputs, disable_prompt):
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
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesKeycloakStage]
