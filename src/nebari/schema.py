import enum
from typing import Annotated

import pydantic
from pydantic import ConfigDict, Field, StringConstraints, field_validator
from ruamel.yaml import yaml_object

from _nebari.utils import escape_string, yaml
from _nebari.version import __version__, rounded_ver_parse

# Regex for suitable project names
project_name_regex = r"^[A-Za-z][A-Za-z0-9\-_]{1,14}[A-Za-z0-9]$"
project_name_pydantic = Annotated[str, StringConstraints(pattern=project_name_regex)]

# Regex for suitable namespaces
namespace_regex = r"^[A-Za-z][A-Za-z\-_]*[A-Za-z]$"
namespace_pydantic = Annotated[str, StringConstraints(pattern=namespace_regex)]

email_regex = "^[^ @]+@[^ @]+\\.[^ @]+$"
email_pydantic = Annotated[str, StringConstraints(pattern=email_regex)]

github_url_regex = r"^(https://)?github\.com/([^/]+)/([^/]+)/?$"
github_url_pydantic = Annotated[str, StringConstraints(pattern=github_url_regex)]


class Base(pydantic.BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )


@yaml_object(yaml)
class ProviderEnum(str, enum.Enum):
    local = "local"
    existing = "existing"
    do = "do"
    aws = "aws"
    gcp = "gcp"
    azure = "azure"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class ExtraFieldSchema(Base):
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        populate_by_name=True,
    )
    immutable: bool = (
        False  # Whether field supports being changed after initial deployment
    )


class Main(Base):
    project_name: project_name_pydantic = Field(json_schema_extra={"immutable": True})
    namespace: namespace_pydantic = "dev"
    provider: ProviderEnum = Field(
        default=ProviderEnum.local,
        json_schema_extra={"immutable": True},
    )
    # In nebari_version only use major.minor.patch version - drop any pre/post/dev suffixes
    nebari_version: Annotated[str, Field(validate_default=True)] = __version__

    prevent_deploy: bool = (
        False  # Optional, but will be given default value if not present
    )

    # If the nebari_version in the schema is old
    # we must tell the user to first run nebari upgrade
    @field_validator("nebari_version")
    @classmethod
    def check_default(cls, value):
        assert cls.is_version_accepted(
            value
        ), f"nebari_version={value} is not an accepted version, it must be equivalent to {__version__}.\nInstall a different version of nebari or run nebari upgrade to ensure your config file is compatible."
        return value

    @classmethod
    def is_version_accepted(cls, v):
        return v != "" and rounded_ver_parse(v) == rounded_ver_parse(__version__)

    @property
    def escaped_project_name(self):
        """Escaped project-name know to be compatible with all clouds"""
        project_name = self.project_name

        if self.provider == ProviderEnum.azure and "-" in project_name:
            project_name = escape_string(project_name, escape_char="a")

        if self.provider == ProviderEnum.aws and project_name.startswith("aws"):
            project_name = "a" + project_name

        return project_name


def is_version_accepted(v):
    """
    Given a version string, return boolean indicating whether
    nebari_version in the nebari-config.yaml would be acceptable
    for deployment with the current Nebari package.
    """
    return Main.is_version_accepted(v)
