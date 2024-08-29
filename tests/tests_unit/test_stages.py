from unittest.mock import patch

import pytest

from _nebari.stages.terraform_state import TerraformStateStage
from _nebari.utils import yaml
from _nebari.version import __version__
from nebari import schema
from nebari.plugins import nebari_plugin_manager


class TestTerraformStateStage:
    @pytest.fixture
    def mock_config(self):
        mock_config_file = yaml.load(
            f"""
provider: local
namespace: dev
nebari_version: {__version__}
project_name: test
domain: test.example.com
ci_cd:
  type: none
terraform_state:
  type: local
security:
  keycloak:
    initial_root_password: muwti3n4d7m81c1svcgaahwhfi869yhg
  authentication:
    type: password
theme:
  jupyterhub:
    hub_title: Nebari - test
    welcome: Welcome! Learn about Nebari's features and configurations in <a href="https://www.nebari.dev/docs">the
      documentation</a>. If you have any questions or feedback, reach the team on
      <a href="https://www.nebari.dev/docs/community#getting-support">Nebari's support
      forums</a>.
    hub_subtitle: Your open source data science platform, hosted
certificate:
  type: lets-encrypt
  acme_email: test@example.com
"""
        )

        config = nebari_plugin_manager.config_schema.model_validate(mock_config_file)
        return config

    @pytest.fixture
    def terraform_state_stage(self, mock_config, tmp_path):
        return TerraformStateStage(tmp_path, mock_config)

    @patch.object(TerraformStateStage, "get_nebari_config_state")
    def test_check_immutable_fields_no_changes(
        self, mock_get_state, terraform_state_stage
    ):
        # breakpoint()
        mock_get_state.return_value = terraform_state_stage.config

        # This should not raise an exception
        # breakpoint()
        terraform_state_stage.check_immutable_fields()

    @patch.object(TerraformStateStage, "get_nebari_config_state")
    def test_check_immutable_fields_mutable_change(
        self, mock_get_state, terraform_state_stage, mock_config
    ):
        old_config = mock_config.model_copy()
        old_config.project_name = "old-project"
        mock_get_state.return_value = old_config

        # This should not raise an exception (project_name is mutable)
        terraform_state_stage.check_immutable_fields()

    @patch.object(TerraformStateStage, "get_nebari_config_state")
    @patch.object(schema.Main, "model_fields")
    def test_check_immutable_fields_immutable_change(
        self, mock_model_fields, mock_get_state, terraform_state_stage, mock_config
    ):
        old_config = mock_config.model_copy()
        old_config.provider = schema.ProviderEnum.gcp
        mock_get_state.return_value = old_config

        # Mock the provider field to be immutable
        mock_model_fields.__getitem__.return_value.json_schema_extra = {
            "immutable": True
        }

        with pytest.raises(ValueError) as exc_info:
            terraform_state_stage.check_immutable_fields()

        assert 'Attempting to change immutable field "provider"' in str(exc_info.value)

    @patch.object(TerraformStateStage, "get_nebari_config_state")
    def test_check_immutable_fields_no_prior_state(
        self, mock_get_state, terraform_state_stage
    ):
        mock_get_state.return_value = None

        # This should not raise an exception
        terraform_state_stage.check_immutable_fields()


if __name__ == "__main__":
    pytest.main([__file__])
