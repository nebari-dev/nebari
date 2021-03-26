import enum
import typing

import pydantic


class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"


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


class Base(pydantic.BaseModel):
    ...


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
    config: typing.Optional[typing.Union[Auth0Config, GitHubConfig]]


# =========== Users and Groups =============


class User(Base):
    uid: str
    primary_group: str
    secondary_groups: typing.Optional[typing.List[str]]


class Group(Base):
    gid: int


# ============== Security ================


class Security(Base):
    # authentication
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


class JupyterLabProfile(Base):
    display_name: str
    description: str
    groups: typing.List[str]
    kubespawner_override: KubeSpawner


class DaskWorkerProfile(Base):
    worker_cores_limit: int
    worker_cores: int
    worker_memory_limit: str
    worker_memory: str
    image: str


class Profiles(Base):
    jupyterlab: typing.List[JupyterLabProfile]
    dask_worker: typing.Dict[str, DaskWorkerProfile]


# ================ Environment ================


class CondaEnvironment(Base):
    name: str
    channels: typing.Optional[typing.List[str]]
    dependencies: typing.List[typing.Union[str, typing.Dict[str, str]]]


# ==================== Main ===================

project_name_regex_type = pydantic.constr(regex="^[A-Za-z-_]+$")


class Main(Base):
    project_name: project_name_regex_type
    provider: ProviderEnum
    ci_cd: CiEnum
    domain: str
    terraform_state: TerraformStateEnum
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
