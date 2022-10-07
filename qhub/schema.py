import enum
import typing
from abc import ABC

import pydantic
from pydantic import root_validator, validator

from qhub.utils import namestr_regex

from .version import __version__, rounded_ver_parse


class CertificateEnum(str, enum.Enum):
    letsencrypt = "lets-encrypt"
    selfsigned = "self-signed"
    existing = "existing"
    disabled = "disabled"


class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"
    existing = "existing"


class ProviderEnum(str, enum.Enum):
    local = "local"
    existing = "existing"
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


class AccessEnum(str, enum.Enum):
    all = "all"
    yaml = "yaml"
    keycloak = "keycloak"


class Base(pydantic.BaseModel):
    ...

    class Config:
        extra = "forbid"


# ============== CI/CD =============


class CICD(Base):
    type: CiEnum
    branch: str
    commit_render: typing.Optional[bool] = True
    before_script: typing.Optional[typing.List[str]]
    after_script: typing.Optional[typing.List[str]]


# ======== Generic Helm Extensions ========
class HelmExtension(Base):
    name: str
    repository: str
    chart: str
    version: str
    overrides: typing.Optional[typing.Dict]


# ============== Argo-Workflows =========


class ArgoWorkflows(Base):
    enabled: bool
    overrides: typing.Optional[typing.Dict]


# ============== kbatch =============


class KBatch(Base):
    enabled: bool


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


# =========== Conda-Store ==============


class CondaStore(Base):
    extra_settings: typing.Optional[typing.Dict[str, typing.Any]] = {}
    extra_config: typing.Optional[str] = ""
    image_tag: typing.Optional[str] = ""


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
    guest_accelerators: typing.Optional[typing.List[typing.Dict]] = []

    class Config:
        extra = "allow"

    @validator("guest_accelerators")
    def validate_guest_accelerators(cls, v):
        if not v:
            return v
        if not isinstance(v, list):
            raise ValueError("guest_accelerators must be a list")
        for i in v:
            assertion_error_message = """
                In order to successfully use guest accelerators, you must specify the following parameters:

                name (str): Machine type name of the GPU, available at https://cloud.google.com/compute/docs/gpus
                count (int): Number of GPUs to attach to the instance

                See general information regarding GPU support at:
                https://docs.qhub.dev/en/stable/source/admin_guide/gpu.html?#add-gpu-node-group
            """
            try:
                assert "name" in i and "count" in i
                assert isinstance(i["name"], str) and isinstance(i["count"], int)
            except AssertionError:
                raise ValueError(assertion_error_message)


class DigitalOceanProvider(Base):
    region: str
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]
    terraform_overrides: typing.Any


class GoogleCloudPlatformProvider(Base):
    project: str
    region: str
    zone: typing.Optional[str]  # No longer used
    availability_zones: typing.Optional[typing.List[str]]  # Genuinely optional
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]
    terraform_overrides: typing.Any


class AzureProvider(Base):
    region: str
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]
    storage_account_postfix: str
    terraform_overrides: typing.Any


class AmazonWebServicesProvider(Base):
    region: str
    availability_zones: typing.Optional[typing.List[str]]
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]
    terraform_overrides: typing.Any


class LocalProvider(Base):
    kube_context: typing.Optional[str]
    node_selectors: typing.Dict[str, KeyValueDict]


class ExistingProvider(Base):
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
    access: AccessEnum = AccessEnum.all
    display_name: str
    description: str
    default: typing.Optional[bool]
    users: typing.Optional[typing.List[str]]
    groups: typing.Optional[typing.List[str]]
    kubespawner_override: typing.Optional[KubeSpawner]

    @root_validator
    def only_yaml_can_have_groups_and_users(cls, values):
        if values["access"] != AccessEnum.yaml:
            if (
                values.get("users", None) is not None
                or values.get("groups", None) is not None
            ):
                raise ValueError(
                    "Profile must not contain groups or users fields unless access = yaml"
                )
        return values


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

    @validator("jupyterlab")
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


class Ingress(Base):
    terraform_overrides: typing.Any


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


def project_name_convention(value: typing.Any, values):
    convention = """
    There are some project naming conventions which need to be followed.
    First, ensure your name is compatible with the specific one for
    your chosen Cloud provider. In addition, the project name should also obey the following
    format requirements:
    - Letters from A to Z (upper and lower case) and numbers;
    - Maximum accepted length of the name string is 16 characters.
    - If using AWS: names should not start with the string "aws";
    - If using Azure: names should not contain "-".
    """
    if len(value) > 16:
        raise ValueError(
            "\n".join(
                [
                    convention,
                    "Maximum accepted length of the project name string is 16 characters.",
                ]
            )
        )
    elif values["provider"] == "azure" and ("-" in value):
        raise ValueError(
            "\n".join(
                [convention, "Provider [azure] does not allow '-' in project name."]
            )
        )
    elif values["provider"] == "aws" and value.startswith("aws"):
        raise ValueError(
            "\n".join(
                [
                    convention,
                    "Provider [aws] does not allow 'aws' as starting sequence in project name.",
                ]
            )
        )
    else:
        return letter_dash_underscore_pydantic


# CLEAN UP
class InitInputs(Base):
    cloud_provider: typing.Type[ProviderEnum] = "local"
    project_name: str = ""
    domain_name: str = ""
    namespace: typing.Optional[letter_dash_underscore_pydantic] = "dev"
    auth_provider: typing.Type[AuthenticationEnum] = "password"
    auth_auto_provision: bool = False
    repository: typing.Union[str, None] = None
    repository_auto_provision: bool = False
    ci_provider: typing.Optional[CiEnum] = None
    terraform_state: typing.Optional[TerraformStateEnum] = None
    kubernetes_version: typing.Union[str, None] = None
    ssl_cert_email: typing.Union[str, None] = None
    disable_prompt: bool = False
    # TODO remove when Typer CLI is out of BETA
    nebari: bool = False


class Main(Base):
    provider: ProviderEnum
    project_name: str
    namespace: typing.Optional[letter_dash_underscore_pydantic]
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
    existing: typing.Optional[ExistingProvider]
    google_cloud_platform: typing.Optional[GoogleCloudPlatformProvider]
    amazon_web_services: typing.Optional[AmazonWebServicesProvider]
    azure: typing.Optional[AzureProvider]
    digital_ocean: typing.Optional[DigitalOceanProvider]
    theme: Theme
    profiles: Profiles
    environments: typing.Dict[str, CondaEnvironment]
    conda_store: typing.Optional[CondaStore]
    argo_workflows: typing.Optional[ArgoWorkflows]
    kbatch: typing.Optional[KBatch]
    monitoring: typing.Optional[Monitoring]
    clearml: typing.Optional[ClearML]
    tf_extensions: typing.Optional[typing.List[QHubExtension]]
    jupyterhub: typing.Optional[JupyterHub]
    prevent_deploy: bool = (
        False  # Optional, but will be given default value if not present
    )
    ingress: typing.Optional[Ingress]

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

    @validator("project_name")
    def _project_name_convention(cls, value: typing.Any, values):
        project_name_convention(value=value, values=values)


def verify(config):
    return Main(**config)


def is_version_accepted(v):
    """
    Given a version string, return boolean indicating whether
    qhub_version in the qhub-config.yaml would be acceptable
    for deployment with the current QHub package.
    """
    return Main.is_version_accepted(v)
