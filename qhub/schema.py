import enum
import typing
from abc import ABC

import pydantic
from pydantic import validator, root_validator
from qhub.utils import namestr_regex, check_for_duplicates


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
    before_script: typing.Optional[typing.List[str]]
    after_script: typing.Optional[typing.List[str]]


# ============== Monitoring =============


class Monitoring(Base):
    enabled: bool


# ============== ClearML =============


class ClearML(Base):
    enabled: bool
    enable_forward_auth: typing.Optional[bool]


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


class TerraformModules(Base):
    # No longer used, so ignored, but could still be in qhub-config.yaml
    repository: str
    rev: str


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
    conda_store: str


# =========== Authentication ==============


class GitHubConfig(Base):
    oauth_callback_url: str
    client_id: str
    client_secret: str


class Auth0Config(Base):
    client_id: str
    client_secret: str
    oauth_callback_url: str
    scope: typing.List[str]
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


class CustomAuthentication(Authentication):
    _typ = AuthenticationEnum.custom
    authentication_class: str
    config: typing.Dict[str, typing.Any]


# =========== Users and Groups =============


class User(Base):
    uid: str
    password: typing.Optional[str]
    primary_group: str
    secondary_groups: typing.Optional[typing.List[str]]


class Group(Base):
    gid: int


# ============== Security ================


class Security(Base):
    authentication: Authentication
    users: typing.Dict[str, User]
    groups: typing.Dict[str, Group]

    @validator("users", pre=True)
    def validate_uderids(cls, v):
        # raise TypeError if duplicated
        return check_for_duplicates(v)


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
    project: str
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
    jupyterhub: typing.Dict[str, str]


# ================== Profiles ==================


class KubeSpawner(Base):
    cpu_limit: int
    cpu_guarantee: int
    mem_limit: str
    mem_guarantee: str
    image: str

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
    image: str

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
    ci_cd: typing.Optional[CICD]
    domain: str
    terraform_state: typing.Optional[TerraformState]
    terraform_modules: typing.Optional[
        TerraformModules
    ]  # No longer used, so ignored, but could still be in qhub-config.yaml
    certificate: Certificate
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


def verify(config):
    Main(**config)
