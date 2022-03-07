import enum
import typing
from abc import ABC

import pydantic
from pydantic import validator, root_validator
from qhub.utils import namestr_regex
from .version import rounded_ver_parse, __version__


class CertificateEnum(str, enum.Enum):
    letsencrypt = "lets-encrypt"
    selfsigned = "self-signed"
    existing = "existing"


class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"
    existing = "existing"


class ProviderEnum(str, enum.Enum):
    local = "local"
    do = "do"
    aws = "aws"
    gcp = "gcp"
    azure = "azure"


class CiEnum(str, enum.Enum):
    github_actions = "github-actions"
    gitlab_ci = "gitlab-ci"
    none = "none"


class AuthenticationEnum(str, enum.Enum):
    password = "password"
    github = "GitHub"
    auth0 = "Auth0"
    custom = "custom"


class Base(pydantic.BaseModel):
    ...

    class Config:
        extra = "forbid"


# ============== CI/CD =============


class CICD(Base):
    type: CiEnum
    branch: str
    commit_render: bool
    before_script: typing.Optional[typing.List[str]]
    after_script: typing.Optional[typing.List[str]]


# ======== Generic Helm Extensions ========
class HelmExtension(Base):
    name: str
    repository: str
    chart: str
    version: str
    overrides: typing.Optional[typing.Dict]


# ============== Monitoring =============


class Monitoring(Base):
    enabled: bool


# ============== ClearML =============


class ClearML(Base):
    enabled: bool
    enable_forward_auth: typing.Optional[bool]
    overrides: typing.Optional[typing.Dict]


# ============== Prefect =============


class Prefect(Base):
    enabled: bool
    image: typing.Optional[str]
    overrides: typing.Optional[typing.Dict]


# ============= Terraform ===============


class TerraformState(Base):
    type: TerraformStateEnum
    backend: typing.Optional[str]
    config: typing.Optional[typing.Dict[str, str]]


# ============ Certificate =============


class Certificate(Base):
    type: CertificateEnum
    # existing
    secret_name: typing.Optional[str]
    # lets-encrypt
    acme_email: typing.Optional[str]
    acme_server: typing.Optional[str]


# ========== Default Images ==============


class DefaultImages(Base):
    jupyterhub: str
    jupyterlab: str
    dask_worker: str
    dask_gateway: str


# =========== Authentication ==============


class GitHubConfig(Base):
    client_id: str
    client_secret: str


class Auth0Config(Base):
    client_id: str
    client_secret: str
    auth0_subdomain: str


class Authentication(Base, ABC):
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


class PasswordAuthentication(Authentication):
    _typ = AuthenticationEnum.password


class Auth0Authentication(Authentication):
    _typ = AuthenticationEnum.auth0
    config: Auth0Config


class GitHubAuthentication(Authentication):
    _typ = AuthenticationEnum.github
    config: GitHubConfig


# ================= Keycloak ==================


class Keycloak(Base):
    initial_root_password: typing.Optional[str]
    overrides: typing.Optional[typing.Dict]
    realm_display_name: typing.Optional[str]


# ============== Security ================


class Security(Base):
    authentication: Authentication
    shared_users_group: typing.Optional[bool]
    keycloak: typing.Optional[Keycloak]


# ================ Providers ===============


class KeyValueDict(Base):
    key: str
    value: str


class NodeSelector(Base):
    general: KeyValueDict
    user: KeyValueDict
    worker: KeyValueDict


class NodeGroup(Base):
    instance: str
    min_nodes: int
    max_nodes: int
    gpu: typing.Optional[bool] = False

    class Config:
        extra = "allow"


class DigitalOceanProvider(Base):
    region: str
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]


class GoogleCloudPlatformProvider(Base):
    project: str
    region: str
    zone: typing.Optional[str]  # No longer used
    availability_zones: typing.Optional[typing.List[str]]  # Genuinely optional
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]


class AzureProvider(Base):
    region: str
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]
    storage_account_postfix: str


class AmazonWebServicesProvider(Base):
    region: str
    availability_zones: typing.Optional[typing.List[str]]
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]


class LocalProvider(Base):
    kube_context: typing.Optional[str]
    node_selectors: typing.Dict[str, KeyValueDict]


# ================= Theme ==================


class Theme(Base):
    jupyterhub: typing.Dict[str, typing.Union[str, list]]


# ================= Theme ==================


class JupyterHub(Base):
    overrides: typing.Optional[typing.Dict]


# ================== Profiles ==================


class KubeSpawner(Base):
    cpu_limit: int
    cpu_guarantee: int
    mem_limit: str
    mem_guarantee: str
    image: typing.Optional[str]

    class Config:
        extra = "allow"


class JupyterLabProfile(Base):
    display_name: str
    description: str
    default: typing.Optional[bool]
    users: typing.Optional[typing.List[str]]
    groups: typing.Optional[typing.List[str]]
    kubespawner_override: typing.Optional[KubeSpawner]


class DaskWorkerProfile(Base):
    worker_cores_limit: int
    worker_cores: int
    worker_memory_limit: str
    worker_memory: str
    image: typing.Optional[str]

    class Config:
        extra = "allow"


class Profiles(Base):
    jupyterlab: typing.List[JupyterLabProfile]
    dask_worker: typing.Dict[str, DaskWorkerProfile]

    @validator("jupyterlab", pre=True)
    def check_default(cls, v, values):
        """Check if only one default value is present"""
        default = [attrs["default"] for attrs in v if "default" in attrs]
        if default.count(True) > 1:
            raise TypeError(
                "Multiple default Jupyterlab profiles may cause unexpected problems."
            )
        return v


# ================ Environment ================


class CondaEnvironment(Base):
    name: str
    channels: typing.Optional[typing.List[str]]
    dependencies: typing.List[typing.Union[str, typing.Dict[str, typing.List[str]]]]


# =============== CDSDashboards ==============


class CDSDashboards(Base):
    enabled: bool
    cds_hide_user_named_servers: typing.Optional[bool]
    cds_hide_user_dashboard_servers: typing.Optional[bool]


# =============== Extensions = = ==============


class QHubExtensionEnv(Base):
    name: str
    value: str


class QHubExtension(Base):
    name: str
    image: str
    urlslug: str
    private: bool = False
    oauth2client: bool = False
    keycloakadmin: bool = False
    jwt: bool = False
    qhubconfigyaml: bool = False
    logout: typing.Optional[str]
    envs: typing.Optional[typing.List[QHubExtensionEnv]]


# ======== External Container Registry ========

# This allows the user to set a private AWS ECR as a replacement for
# Docker Hub for some images - those where you provide the full path
# to the image on the ECR.
# extcr_account and extcr_region are the AWS account number and region
# of the ECR respectively. access_key_id and secret_access_key are
# AWS access keys that should have read access to the ECR.


class ExtContainerReg(Base):
    enabled: bool
    access_key_id: typing.Optional[str]
    secret_access_key: typing.Optional[str]
    extcr_account: typing.Optional[str]
    extcr_region: typing.Optional[str]

    @root_validator
    def enabled_must_have_fields(cls, values):
        if values["enabled"]:
            for fldname in (
                "access_key_id",
                "secret_access_key",
                "extcr_account",
                "extcr_region",
            ):
                if (
                    fldname not in values
                    or values[fldname] is None
                    or values[fldname].strip() == ""
                ):
                    raise ValueError(
                        f"external_container_reg must contain a non-blank {fldname} when enabled is true"
                    )
        return values


# ==================== Main ===================

letter_dash_underscore_pydantic = pydantic.constr(regex=namestr_regex)


class Main(Base):
    project_name: letter_dash_underscore_pydantic
    namespace: typing.Optional[letter_dash_underscore_pydantic]
    provider: ProviderEnum
    qhub_version: str = ""
    ci_cd: typing.Optional[CICD]
    domain: str
    terraform_state: typing.Optional[TerraformState]
    certificate: Certificate
    helm_extensions: typing.Optional[typing.List[HelmExtension]]
    prefect: typing.Optional[Prefect]
    cdsdashboards: CDSDashboards
    security: Security
    external_container_reg: typing.Optional[ExtContainerReg]
    default_images: DefaultImages
    storage: typing.Dict[str, str]
    local: typing.Optional[LocalProvider]
    google_cloud_platform: typing.Optional[GoogleCloudPlatformProvider]
    amazon_web_services: typing.Optional[AmazonWebServicesProvider]
    azure: typing.Optional[AzureProvider]
    digital_ocean: typing.Optional[DigitalOceanProvider]
    theme: Theme
    profiles: Profiles
    environments: typing.Dict[str, CondaEnvironment]
    monitoring: typing.Optional[Monitoring]
    clearml: typing.Optional[ClearML]
    tf_extensions: typing.Optional[typing.List[QHubExtension]]
    jupyterhub: typing.Optional[JupyterHub]
    prevent_deploy: bool = (
        False  # Optional, but will be given default value if not present
    )

    # If the qhub_version in the schema is old
    # we must tell the user to first run qhub upgrade
    @validator("qhub_version", pre=True, always=True)
    def check_default(cls, v):
        """
        Always called even if qhub_version is not supplied at all (so defaults to ''). That way we can give a more helpful error message.
        """
        if not cls.is_version_accepted(v):
            if v == "":
                v = "not supplied"
            raise ValueError(
                f"qhub_version in the config file must be equivalent to {__version__} to be processed by this version of qhub (your config file version is {v})."
                " Install a different version of qhub or run qhub upgrade to ensure your config file is compatible."
            )
        return v

    @classmethod
    def is_version_accepted(cls, v):
        return v != "" and rounded_ver_parse(v) == rounded_ver_parse(__version__)


def verify(config):
    return Main(**config)


def is_version_accepted(v):
    """
    Given a version string, return boolean indicating whether
    qhub_version in the qhub-config.yaml would be acceptable
    for deployment with the current QHub package.
    """
    return Main.is_version_accepted(v)
