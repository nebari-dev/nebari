import enum

import pydantic
from pydantic import validator
from ruamel.yaml import yaml_object

from _nebari.utils import yaml
from _nebari.version import __version__, rounded_ver_parse

# Regex for suitable project names
namestr_regex = r"^[A-Za-z][A-Za-z\-_]*[A-Za-z]$"
letter_dash_underscore_pydantic = pydantic.constr(regex=namestr_regex)

email_regex = "^[^ @]+@[^ @]+\\.[^ @]+$"
email_pydantic = pydantic.constr(regex=email_regex)


class Base(pydantic.BaseModel):
    ...

    class Config:
        extra = "forbid"
        validate_assignment = True
        allow_population_by_field_name = True


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


@yaml_object(yaml)
class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"
    existing = "existing"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class Main(Base):
    project_name: letter_dash_underscore_pydantic
    namespace: letter_dash_underscore_pydantic = "dev"
    # In nebari_version only use major.minor.patch version - drop any pre/post/dev suffixes
    nebari_version: str = __version__

    prevent_deploy: bool = (
        False  # Optional, but will be given default value if not present
    )

    # If the nebari_version in the schema is old
    # we must tell the user to first run nebari upgrade
    @validator("nebari_version", pre=True, always=True)
    def check_default(cls, v):
        """
        Always called even if nebari_version is not supplied at all (so defaults to ''). That way we can give a more helpful error message.
        """
        if not cls.is_version_accepted(v):
            if v == "":
                v = "not supplied"
            raise ValueError(
                f"nebari_version in the config file must be equivalent to {__version__} to be processed by this version of nebari (your config file version is {v})."
                " Install a different version of nebari or run nebari upgrade to ensure your config file is compatible."
            )
        return v

    @classmethod
    def is_version_accepted(cls, v):
        return v != "" and rounded_ver_parse(v) == rounded_ver_parse(__version__)


def is_version_accepted(v):
    """
    Given a version string, return boolean indicating whether
    nebari_version in the nebari-config.yaml would be acceptable
    for deployment with the current Nebari package.
    """
    return Main.is_version_accepted(v)


# from _nebari.config import read_configuration, write_configuration
