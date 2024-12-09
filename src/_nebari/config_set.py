import pathlib

import yaml


def read_config_set(config_set_filepath: str):
    """Read a config set from a config file."""

    filename = pathlib.Path(config_set_filepath)

    with filename.open() as f:
        config_dict = yaml.load(f)

    return config_dict
