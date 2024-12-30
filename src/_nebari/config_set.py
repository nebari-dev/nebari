import logging
import pathlib
from typing import Optional

from packaging.requirements import SpecifierSet
from pydantic import BaseModel, ConfigDict, field_validator

from _nebari._version import __version__
from _nebari.utils import yaml

logger = logging.getLogger(__name__)


class ConfigSetMetadata(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    name: str  # for use with guided init
    description: Optional[str] = None
    nebari_version: str | SpecifierSet

    @field_validator("nebari_version")
    @classmethod
    def validate_version_requirement(cls, version_req):
        if isinstance(version_req, str):
            version_req = SpecifierSet(version_req, prereleases=True)

        return version_req

    def check_version(self, version):
        if not self.nebari_version.contains(version, prereleases=True):
            raise ValueError(
                f'Nebari version "{version}" is not compatible with '
                f'version requirement {self.nebari_version} for "{self.name}" config set.'
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
