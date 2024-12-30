import pathlib
from typing import Optional

from packaging.requirements import Requirement
from pydantic import BaseModel, ConfigDict, field_validator

from _nebari._version import __version__
from _nebari.utils import yaml


class ConfigSetMetadata(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    name: str  # for use with guided init
    description: Optional[str] = None
    nebari_version: str | Requirement

    @field_validator("nebari_version")
    @classmethod
    def validate_version_requirement(cls, version_req):
        if isinstance(version_req, str):
            version_req = Requirement(f"nebari{version_req}")
            version_req.specifier.prereleases = True

        return version_req

    def check_version(self, version):
        if version not in self.nebari_version.specifier:
            raise ValueError(
                f"Current Nebari version {__version__} is not compatible with "
                f'required version {self.nebari_version.specifier} for "{self.name}" config set.'
            )


class ConfigSet(BaseModel):
    metadata: ConfigSetMetadata
    config: dict


def read_config_set(config_set_filepath: str):
    """Read a config set from a config file."""

    filename = pathlib.Path(config_set_filepath)

    with filename.open() as f:
        config_set_yaml = yaml.load(f)

    config_set = ConfigSet(**config_set_yaml)

    # validation
    config_set.metadata.check_version(__version__)

    return config_set
