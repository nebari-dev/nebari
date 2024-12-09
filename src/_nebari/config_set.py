import pathlib

import yaml
from pydantic import BaseModel, ConfigDict
from pytest import Config


class ConfigSetMetadata(BaseModel):
    model_config: ConfigDict = ConfigDict(
        extra=Config.extra.allow,
    )
    name: str = None
    description: str = None
    nebari_version: str = None


class ConfigSet(BaseModel):
    metadata: ConfigSetMetadata
    config: dict


def read_config_set(config_set_filepath: str):
    """Read a config set from a config file."""

    filename = pathlib.Path(config_set_filepath)

    with filename.open() as f:
        config_set = yaml.load(f)

    # TODO: Validation e.g. Check Nebari version

    return config_set
