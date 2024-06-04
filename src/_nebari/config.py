import os
import pathlib
import re
import sys
from typing import Any, Dict, List, Union

import pydantic

from _nebari.utils import yaml


def set_nested_attribute(data: Any, attrs: List[str], value: Any):
    """Takes an arbitrary set of attributes and accesses the deep
    nested object config to set value
    """

    def _get_attr(d: Any, attr: str):
        if isinstance(d, list) and re.fullmatch(r"\d+", attr):
            return d[int(attr)]
        elif hasattr(d, "__getitem__"):
            return d[attr]
        else:
            return getattr(d, attr)

    def _set_attr(d: Any, attr: str, value: Any):
        if isinstance(d, list) and re.fullmatch(r"\d+", attr):
            d[int(attr)] = value
        elif hasattr(d, "__getitem__"):
            d[attr] = value
        else:
            setattr(d, attr, value)

    data_pos = data
    for attr in attrs[:-1]:
        data_pos = _get_attr(data_pos, attr)
    _set_attr(data_pos, attrs[-1], value)


def set_config_from_environment_variables(
    config: pydantic.BaseModel, keyword: str = "NEBARI_SECRET", separator: str = "__"
):
    """Setting nebari configuration values from environment variables

    For example `NEBARI_SECRET__ci_cd__branch=master` would set `ci_cd.branch = "master"`
    """
    nebari_secrets = [_ for _ in os.environ if _.startswith(keyword + separator)]
    for secret in nebari_secrets:
        attrs = secret[len(keyword + separator) :].split(separator)
        try:
            set_nested_attribute(config, attrs, os.environ[secret])
        except pydantic.ValidationError as e:
            print(
                f"ERROR: the provided environment variable {secret} causes the following pydantic validation error:\n\n",
                e,
            )
            sys.exit(1)
        except Exception as e:
            print(
                f"ERROR: the provided environment variable {secret} causes the following error:\n\n",
                e,
            )
            sys.exit(1)
    return config


def dump_nested_model(model_dict: Dict[str, Union[pydantic.BaseModel, str]]):
    result = {}
    for key, value in model_dict.items():
        result[key] = (
            value.model_dump() if isinstance(value, pydantic.BaseModel) else value
        )
    return result


def read_configuration(
    config_filename: pathlib.Path,
    config_schema: pydantic.BaseModel,
    read_environment: bool = True,
):
    """Read the nebari configuration from disk and apply validation"""
    filename = pathlib.Path(config_filename)

    if not filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} does not exist"
        )

    with filename.open() as f:
        config_dict = yaml.load(f)
        config = config_schema(**config_dict)

    if read_environment:
        config = set_config_from_environment_variables(config)

    return config


def write_configuration(
    config_filename: pathlib.Path,
    config: Union[pydantic.BaseModel, Dict],
    mode: str = "w",
):
    """Write the nebari configuration file to disk"""
    with config_filename.open(mode) as f:
        if isinstance(config, pydantic.BaseModel):
            config_dict = config.model_dump()
            yaml.dump(config_dict, f)
        else:
            config = dump_nested_model(config)
            yaml.dump(config, f)


def backup_configuration(filename: pathlib.Path, extrasuffix: str = ""):
    if not filename.exists():
        return

    # Backup old file
    backup_filename = pathlib.Path(f"{filename}{extrasuffix}.backup")

    if backup_filename.exists():
        i = 1
        while True:
            next_backup_filename = pathlib.Path(f"{backup_filename}~{i}")
            if not next_backup_filename.exists():
                backup_filename = next_backup_filename
                break
            i = i + 1

    filename.rename(backup_filename)
