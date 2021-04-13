import enum
import typing

import pydantic


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


class AuthenticationEnum(str, enum.Enum):
    password = "password"
    github = "GitHub"
    auth0 = "Auth0"
    custom = "custom"


class Base(pydantic.BaseModel):
    ...

    class Config:
        extra = "forbid"


# ============= Terraform ===============


class TerraformState(Base):
    type: TerraformStateEnum = "remote"
    backend: typing.Optional[str]
    config: typing.Optional[typing.Dict[str, str]]


class TerraformModules(Base):
    repository: str = "github.com/quansight/qhub-terraform-modules"
    rev: str = "dev"


# ============ Certificate =============


class Certificate(Base):
    type: CertificateEnum
    # existing
    secret_name: typing.Optional[str]
    # lets-encrypt
    acme_email: typing.Optional[str]
    acme_server: typing.Optional[str]


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


class Authentication(Base):
    type: AuthenticationEnum
    authentication_class: typing.Optional[str]
    config: typing.Optional[
        typing.Union[Auth0Config, GitHubConfig, typing.Dict[str, typing.Any]]
    ]


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


# ================ Providers ===============


class KeyValueDict(Base):
    key: str
    value: str


class NodeSelector(Base):
    general: KeyValueDict
    user: KeyValueDict
    worker: KeyValueDict


class NodeGroup(Base):
    instance: str = "s-2vcpu-4gb"
    min_nodes: int = 1
    max_nodes: int = 1

    class Config:
        extra = "allow"


class DigitalOceanProvider(Base):
    region: str
    kubernetes_version: str
    node_groups: typing.Dict[str, NodeGroup]


class GoogleCloudPlatformProvider(Base):
    project: str
    region: str
    zone: str
    availability_zones: typing.List[str]
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
    availability_zones: typing.List[str]
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


# ================ Environment ================


class CondaEnvironment(Base):
    name: str
    channels: typing.Optional[typing.List[str]]
    dependencies: typing.List[typing.Union[str, typing.Dict[str, str]]]


# =============== CDSDashboards ==============


class CDSDashboards(Base):
    enabled: bool
    cds_hide_user_named_servers: typing.Optional[bool]
    cds_hide_user_dashboard_servers: typing.Optional[bool]


# ==================== Main ===================

letter_dash_underscore_regex = pydantic.constr(regex=r"^[A-Za-z-_]+$")


class Main(Base):
    project_name: letter_dash_underscore_regex
    namespace: typing.Optional[letter_dash_underscore_regex]
    provider: ProviderEnum
    ci_cd: CiEnum
    domain: str
    terraform_state: typing.Optional[TerraformState]
    terraform_modules: typing.Optional[TerraformModules]
    certificate: Certificate
    cdsdashboards: CDSDashboards
    security: Security
    default_images: typing.Dict[str, str]
    storage: typing.Dict[str, str]
    local: typing.Optional[LocalProvider]
    google_cloud_platform: typing.Optional[GoogleCloudPlatformProvider]
    amazon_web_services: typing.Optional[AmazonWebServicesProvider]
    azure: typing.Optional[AzureProvider]
    digital_ocean: typing.Optional[DigitalOceanProvider]
    theme: Theme
    profiles: Profiles
    environments: typing.Dict[str, CondaEnvironment]


def verify(config):
    Main(**config)
