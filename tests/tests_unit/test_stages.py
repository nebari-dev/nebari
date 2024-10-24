import pathlib
from unittest.mock import patch

import pytest

from _nebari.stages.terraform_state import TerraformStateStage
from _nebari.utils import yaml
from _nebari.version import __version__
from nebari import schema
from nebari.plugins import nebari_plugin_manager

HERE = pathlib.Path(__file__).parent


@pytest.fixture
def mock_config():
    with open(HERE / "./cli_validate/local.happy.yaml", "r") as f:
        mock_config_file = yaml.load(f)
        mock_config_file["nebari_version"] = __version__

    config = nebari_plugin_manager.config_schema.model_validate(mock_config_file)
    return config


@pytest.fixture
def terraform_state_stage(mock_config, tmp_path):
    return TerraformStateStage(tmp_path, mock_config)


@patch.object(TerraformStateStage, "get_nebari_config_state")
def test_check_immutable_fields_no_changes(mock_get_state, terraform_state_stage):
    mock_get_state.return_value = terraform_state_stage.config

    # This should not raise an exception
    terraform_state_stage.check_immutable_fields()


@patch.object(TerraformStateStage, "get_nebari_config_state")
def test_check_immutable_fields_mutable_change(
    mock_get_state, terraform_state_stage, mock_config
):
    old_config = mock_config.model_copy(deep=True)
    old_config.namespace = "old-namespace"
    mock_get_state.return_value = old_config

    # This should not raise an exception (namespace is mutable)
    terraform_state_stage.check_immutable_fields()


@patch.object(TerraformStateStage, "get_nebari_config_state")
@patch.object(schema.Main, "model_fields")
def test_check_immutable_fields_immutable_change(
    mock_model_fields, mock_get_state, terraform_state_stage, mock_config
):
    old_config = mock_config.model_copy(deep=True)
    old_config.provider = schema.ProviderEnum.gcp
    mock_get_state.return_value = old_config

    # Mock the provider field to be immutable
    mock_model_fields.__getitem__.return_value.json_schema_extra = {"immutable": True}

    with pytest.raises(ValueError) as exc_info:
        terraform_state_stage.check_immutable_fields()

    assert 'Attempting to change immutable field "provider"' in str(exc_info.value)


@patch.object(TerraformStateStage, "get_nebari_config_state")
def test_check_immutable_fields_no_prior_state(mock_get_state, terraform_state_stage):
    mock_get_state.return_value = None

    # This should not raise an exception
    terraform_state_stage.check_immutable_fields()


@patch.object(TerraformStateStage, "get_nebari_config_state")
def test_check_dict_value_change(mock_get_state, terraform_state_stage, mock_config):
    old_config = mock_config.model_copy(deep=True)
    terraform_state_stage.config.local.node_selectors["worker"].value += "new_value"
    mock_get_state.return_value = old_config

    # should not throw an exception
    terraform_state_stage.check_immutable_fields()


@patch.object(TerraformStateStage, "get_nebari_config_state")
def test_check_list_change(mock_get_state, terraform_state_stage, mock_config):
    old_config = mock_config.model_copy(deep=True)
    old_config.environments["environment-dask.yaml"].channels.append("defaults")
    mock_get_state.return_value = old_config

    # should not throw an exception
    terraform_state_stage.check_immutable_fields()
