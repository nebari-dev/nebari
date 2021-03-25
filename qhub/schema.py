import enum
import typing

import pydantic


class ProviderEnum(str, enum.Enum):
    local = "local"
    do = "do"
    aws = "aws"
    gcp = "gcp"


class CiEnum(str, enum.Enum):
    github_actions = "github-actions"


class Base(pydantic.BaseModel):
    ...


class NodeGroup(Base):
    instance: str = "s-2vcpu-4gb"
    min_nodes: int = 1
    max_nodes: int = 1

    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema.update(
                examples=[
                    NodeGroup(instance="s-2vcpu-4gb", min_nodes=1, max_nodes=1).dict(),
                    NodeGroup(instance="s-2vcpu-4gb", min_nodes=1, max_nodes=4).dict(),
                ]
            )
            return schema


class Provider(Base):
    region: str
    node_groups: typing.Dict[str, NodeGroup]

    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema.update(
                examples=[
                    {
                        "general": NodeGroup(
                            instance="s-2vcpu-4gb", min_nodes=1, max_nodes=1
                        ).dict(),
                        "user": NodeGroup(
                            instance="s-2vcpu-4gb", min_nodes=1, max_nodes=1
                        ).dict(),
                        "work": NodeGroup(
                            instance="s-2vcpu-4gb", min_nodes=1, max_nodes=1
                        ).dict(),
                    }
                ]
            )
            return schema


class KubeSpawner(pydantic.BaseModel):
    cpu_limit: int
    cpu_guarantee: int
    mem_limit: str
    mem_guarantee: str
    image: str

    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema.update(
                examples=[
                    KubeSpawner(
                        cpu_limit=1,
                        cpu_guarantee=1,
                        mem_limit="1G",
                        mem_guarantee="1G",
                        image="quansight/qhub-jupyterlab:398e040a7d26bcc1d04fc3576f452bfa261032bc",
                    ).dict(),
                    KubeSpawner(
                        cpu_limit=1.5,
                        cpu_guarantee=1.25,
                        mem_limit="2G",
                        mem_guarantee="2G",
                        image="quansight/qhub-jupyterlab:398e040a7d26bcc1d04fc3576f452bfa261032bc",
                    ).dict(),
                ]
            )
            return schema


class LabProfile(Base):
    "Stable environment with 1 cpu / 1 GB ram"
    display_name: str
    groups: typing.List[str]
    kubespawner_override: KubeSpawner


class User(Base):
    uid: str
    primary_group: str
    secondary_group: str = None


class Group(Base):
    gid: int


class AuthConfig(Base):
    oauth_callback_url: str = "https://jupyter.do.qhub.dev/hub/oauth_callback"


class GithubAuth(Base):
    """
    >>> assert Authentication(type='Github', config = GithubAuth(client_id="", client_secret=""))
    """

    client_id: str
    client_secret: str


class Authentication(Base):
    type: str
    config: typing.Optional[AuthConfig]


class Security(Base):
    authentication: Authentication
    users: typing.Dict[str, User]
    group: typing.Dict[str, Group] = {}


class DaskWorker(Base):
    worker_cores_limit: int
    worker_cores: int
    worker_memory_limit: str
    worker_memory: str
    image: str

    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema.update(
                examples=[
                    DaskWorker(
                        worker_cores_limit=1,
                        worker_cores=1,
                        worker_memory_limit="1G",
                        worker_memory="1G",
                        image="quansight/qhub-dask-worker:398e040a7d26bcc1d04fc3576f452bfa261032bc",
                    ).dict(),
                    DaskWorker(
                        worker_cores_limit=1.5,
                        worker_cores=1.25,
                        worker_memory_limit="2G",
                        worker_memory="2G",
                        image="quansight/qhub-dask-worker:398e040a7d26bcc1d04fc3576f452bfa261032bc",
                    ).dict(),
                ]
            )
            return schema


class JupyterLabProfile(Base):
    display_name: str
    description: str
    groups: typing.List[str] = []
    kubespawner_override: KubeSpawner


class Profiles(Base):
    jupyterlab: typing.List[JupyterLabProfile] = []
    dask_worker: typing.Dict[str, DaskWorker] = {}


project_name_regex_type = pydantic.constr(regex="^[A-Za-z-_]+$")


class Main(Base):
    project_name: project_name_regex_type
    provider: ProviderEnum
    ci_cd: CiEnum
    security: Security
    profiles: Profiles = []


class DigitalOcean(Main):
    digital_ocean: Provider = None


def verify(config):
    Main(**config)
