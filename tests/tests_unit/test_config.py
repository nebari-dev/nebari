import os
import pathlib

import pytest

from _nebari.config import (
    backup_configuration,
    read_configuration,
    set_config_from_environment_variables,
    set_nested_attribute,
    write_configuration,
)


def test_set_nested_attribute():
    data = {"a": {"b": {"c": 1}}}
    set_nested_attribute(data, ["a", "b", "c"], 2)
    assert data["a"]["b"]["c"] == 2

    data = {"a": [1, 2, 3]}
    set_nested_attribute(data, ["a", "1"], 4)
    assert data["a"][1] == 4

    data = {"a": {"1": "value"}}
    set_nested_attribute(data, ["a", "1"], "new_value")
    assert data["a"]["1"] == "new_value"

    class Dummy:
        pass

    obj = Dummy()
    obj.a = Dummy()
    obj.a.b = 1
    set_nested_attribute(obj, ["a", "b"], 2)
    assert obj.a.b == 2

    data = {"a": [{"b": 1}, {"b": 2}]}
    set_nested_attribute(data, ["a", "1", "b"], 3)
    assert data["a"][1]["b"] == 3

    with pytest.raises(Exception):
        set_nested_attribute(data, ["a", "2", "b"], 3)


def test_set_config_from_environment_variables(nebari_config):
    secret_key = "NEBARI_SECRET__namespace"
    secret_value = "test"
    os.environ[secret_key] = secret_value

    secret_key_nested = "NEBARI_SECRET__theme__jupyterhub__welcome"
    secret_value_nested = "Hi from test_set_config_from_environment_variables"
    os.environ[secret_key_nested] = secret_value_nested

    updated_config = set_config_from_environment_variables(
        nebari_config, "NEBARI_SECRET"
    )

    assert updated_config.namespace == secret_value
    assert updated_config.theme.jupyterhub.welcome == secret_value_nested

    del os.environ[secret_key]
    del os.environ[secret_key_nested]


def test_set_config_from_environment_invalid_secret(nebari_config):
    invalid_secret_key = "NEBARI_SECRET__nonexistent__attribute"
    os.environ[invalid_secret_key] = "some_value"

    with pytest.raises(SystemExit) as excinfo:
        set_config_from_environment_variables(nebari_config, "NEBARI_SECRET")

    assert excinfo.value.code == 1

    del os.environ[invalid_secret_key]


def test_write_and_read_configuration(nebari_config, tmp_path):
    config_file = tmp_path / "nebari-config.yaml"

    write_configuration(config_file, nebari_config)
    nebari_config_new = read_configuration(config_file, nebari_config.__class__)

    # TODO: determine a way to compare the two objects directly
    assert nebari_config.namespace == nebari_config_new.namespace
    assert (
        nebari_config.theme.jupyterhub.welcome
        == nebari_config_new.theme.jupyterhub.welcome
    )


def test_read_configuration_non_existent_file(nebari_config):
    non_existent_file = pathlib.Path("/path/to/nonexistent/file.yaml")

    with pytest.raises(ValueError, match="does not exist"):
        read_configuration(non_existent_file, nebari_config.__class__)


def test_write_configuration_with_dict(nebari_config, tmp_path):
    config_file = tmp_path / "nebari-config-dict.yaml"
    config_dict = nebari_config.model_dump()

    write_configuration(config_file, config_dict)
    read_config = read_configuration(config_file, nebari_config.__class__)

    # TODO: determine a way to compare the two objects directly
    assert nebari_config.namespace == read_config.namespace
    assert (
        nebari_config.theme.jupyterhub.welcome == read_config.theme.jupyterhub.welcome
    )


def test_backup_non_existent_file(tmp_path):
    non_existent_file = tmp_path / "non_existent_config.yaml"
    backup_configuration(non_existent_file)
    assert not (tmp_path / "non_existent_config.yaml.backup").exists()


def test_backup_existing_file_no_previous_backup(nebari_config, tmp_path):
    config_file = tmp_path / "nebari-config.yaml"
    extrasuffix = "-abc"

    write_configuration(config_file, nebari_config)

    backup_configuration(config_file, extrasuffix)

    assert not config_file.exists()
    assert (tmp_path / f"nebari-config.yaml{extrasuffix}.backup").exists()


def test_backup_existing_file_with_previous_backup(nebari_config, tmp_path):
    fn = "nebari-config.yaml"
    backup_fn = f"{fn}.backup"
    config_file = tmp_path / fn
    backup_file = tmp_path / backup_fn

    write_configuration(config_file, nebari_config)
    write_configuration(backup_file, nebari_config)

    backup_configuration(config_file)

    assert not config_file.exists()
    assert (tmp_path / f"{backup_fn}~1").exists()


def test_backup_multiple_existing_backups(nebari_config, tmp_path):
    fn = "nebari-config.yaml"
    backup_fn = f"{fn}.backup"
    config_file = tmp_path / fn
    backup_fn = tmp_path / backup_fn

    # create and write to `nebari-config.yaml` and `nebari-config.yaml.backup`
    write_configuration(config_file, nebari_config)
    write_configuration(backup_fn, nebari_config)

    for i in range(1, 5):
        backup_fn_i = tmp_path / f"{backup_fn}~{i}"
        # create and write to `nebari-config.yaml.backup~i`
        write_configuration(backup_fn_i, nebari_config)

    backup_configuration(config_file)

    assert (tmp_path / f"{backup_fn}~5").exists()
