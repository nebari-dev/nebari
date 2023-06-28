import enum
import os
import pathlib
import re
import sys
import typing

import pydantic
from pydantic import validator
from ruamel.yaml import YAML, yaml_object

from _nebari.version import __version__, rounded_ver_parse

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

# Regex for suitable project names
namestr_regex = r"^[A-Za-z][A-Za-z\-_]*[A-Za-z]$"


@yaml_object(yaml)
class TerraformStateEnum(str, enum.Enum):
    remote = "remote"
    local = "local"
    existing = "existing"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


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
class GitRepoEnum(str, enum.Enum):
    github = "github.com"
    gitlab = "gitlab.com"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


@yaml_object(yaml)
class CiEnum(str, enum.Enum):
    github_actions = "github-actions"
    gitlab_ci = "gitlab-ci"
    none = "none"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


@yaml_object(yaml)
class AuthenticationEnum(str, enum.Enum):
    password = "password"
    github = "GitHub"
    auth0 = "Auth0"
    custom = "custom"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class Base(pydantic.BaseModel):
    ...

    class Config:
        extra = "forbid"
        validate_assignment = True
        allow_population_by_field_name = True


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


class InitInputs(Base):
    cloud_provider: ProviderEnum = ProviderEnum.local
    project_name: str = ""
    domain_name: typing.Optional[str] = None
    namespace: typing.Optional[letter_dash_underscore_pydantic] = "dev"
    auth_provider: AuthenticationEnum = AuthenticationEnum.password
    auth_auto_provision: bool = False
    repository: typing.Union[str, None] = None
    repository_auto_provision: bool = False
    ci_provider: CiEnum = CiEnum.none
    terraform_state: TerraformStateEnum = TerraformStateEnum.remote
    kubernetes_version: typing.Union[str, None] = None
    ssl_cert_email: typing.Union[str, None] = None
    disable_prompt: bool = False
    output: pathlib.Path = pathlib.Path("nebari-config.yaml")


class Main(Base):
    project_name: str
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

    @validator("project_name")
    def _project_name_convention(cls, value: typing.Any, values):
        project_name_convention(value=value, values=values)
        return value


def is_version_accepted(v):
    """
    Given a version string, return boolean indicating whether
    nebari_version in the nebari-config.yaml would be acceptable
    for deployment with the current Nebari package.
    """
    return Main.is_version_accepted(v)


def set_nested_attribute(data: typing.Any, attrs: typing.List[str], value: typing.Any):
    """Takes an arbitrary set of attributes and accesses the deep
    nested object config to set value

    """

    def _get_attr(d: typing.Any, attr: str):
        if hasattr(d, "__getitem__"):
            if re.fullmatch(r"\d+", attr):
                try:
                    return d[int(attr)]
                except Exception:
                    return d[attr]
            else:
                return d[attr]
        else:
            return getattr(d, attr)

    def _set_attr(d: typing.Any, attr: str, value: typing.Any):
        if hasattr(d, "__getitem__"):
            if re.fullmatch(r"\d+", attr):
                try:
                    d[int(attr)] = value
                except Exception:
                    d[attr] = value
            else:
                d[attr] = value
        else:
            return setattr(d, attr, value)

    data_pos = data
    for attr in attrs[:-1]:
        data_pos = _get_attr(data_pos, attr)
    _set_attr(data_pos, attrs[-1], value)


def set_config_from_environment_variables(
    config: Base, keyword: str = "NEBARI_SECRET", separator: str = "__"
):
    """Setting nebari configuration values from environment variables

    For example `NEBARI_SECRET__ci_cd__branch=master` would set `ci_cd.branch = "master"`
    """
    nebari_secrets = [_ for _ in os.environ if _.startswith(keyword + separator)]
    for secret in nebari_secrets:
        attrs = secret[len(keyword + separator) :].split(separator)
        try:
            set_nested_attribute(config, attrs, os.environ[secret])
        except Exception as e:
            print(
                f"FAILED: setting secret from environment variable={secret} due to the following error\n {e}"
            )
            sys.exit(1)
    return config
