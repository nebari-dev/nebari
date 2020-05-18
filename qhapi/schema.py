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


class Profile(Base):
    ...


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


class Main(Base):
    """"""

    project_name: str
    provider: ProviderEnum
    ci_cd: CiEnum
    security: Security


class Providers(Main):
    digital_ocean: Provider = None
