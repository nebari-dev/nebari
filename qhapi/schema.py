import enum
import typing

import pydantic


class ProviderEnum(str, enum.Enum):
    do = "do"
    aws = "aws"
    gcp = "gcp"


class CiEnum(str, enum.Enum):
    github_actions = "github-actions"


class Base(pydantic.BaseModel):
    ...


class NodeGroup(Base):
    ...


class Provider(Base):
    ...


class KubeSpawner(pydantic.BaseModel):
    cpu_limit: int
    cpu_guarentee: int
    mem_limit: str
    mem_guarentee: str
    image: str

    class Config:
        schema_extra = dict(
            examples=[
                dict(
                    cpu_limit=1,
                    cpu_guarentee=1,
                    mem_limit="1G",
                    mem_guarentee="1G",
                    image="quansight/qhub-jupyterlab:398e040a7d26bcc1d04fc3576f452bfa261032bc",
                )
            ]
        )


class LabProfile(Base):
    "Stable environment with 1 cpu / 1 GB ram"
    display_name: str
    groups: typing.List[str]
    kubespawner_override: KubeSpawner


class Project(Base):
    project_name: str
    provider: Provider


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
    config: AuthConfig


class Security(Base):
    authentication: Authentication
    users: typing.Dict[str, User]
    group: typing.Dict[str, Group]


class DaskWorker(Base):
    worker_cores_limit: int
    worker_cores: int
    worker_memory_limit: str
    worker_memory: str
    image: str


class JupyterLabProfile(Base):
    display_name: str
    description: str
    groups: typing.List[str]
    kubespawner_override: KubeSpawner


class Profiles:
    jupyterlab: typing.List[JupyterLabProfile]
    dask_worker: typing.Dict[str, DaskWorker]


class Main(Base):
    """"""

    project_name: str
    provider: ProviderEnum
    ci_cd: CiEnum
    security: Security
    profiles: Profiles


class Providers(Main):
    digital_ocean: Provider = None
