from functools import partial
from unittest.mock import Mock

import pytest

from _nebari.initialize import render_config
from nebari import schema

INIT_INPUTS = [
    # project, namespace, domain, cloud_provider, ci_provider, auth_provider
    ("pytestdo", "dev", "do.nebari.dev", schema.ProviderEnum.do, schema.CiEnum.github_actions, schema.AuthenticationEnum.password),
    ("pytestaws", "dev", "aws.nebari.dev", schema.ProviderEnum.aws, schema.CiEnum.github_actions, schema.AuthenticationEnum.password),
    ("pytestgcp", "dev", "gcp.nebari.dev", schema.ProviderEnum.gcp, schema.CiEnum.github_actions, schema.AuthenticationEnum.password),
    ("pytestazure", "dev", "azure.nebari.dev", schema.ProviderEnum.azure, schema.CiEnum.github_actions, schema.AuthenticationEnum.password),
]

NEBARI_CONFIG_FN = "nebari-config.yaml"
PRESERVED_DIR = "preserved_dir"
DEFAULT_GH_REPO = "github.com/test/test"
DEFAULT_TERRAFORM_STATE = schema.TerraformStateEnum.remote


# use this partial function for all tests that need to call `render_config`
@pytest.fixture
def render_config_partial():
    def _render_config_partial(*args, **kwargs):
        print(args, kwargs)
        return schema.Main(**render_config(
            *args,
            **kwargs,
            repository=DEFAULT_GH_REPO,
            repository_auto_provision=False,
            auth_auto_provision=False,
            terraform_state=DEFAULT_TERRAFORM_STATE,
            disable_prompt=True,
        ))
    return _render_config_partial


@pytest.fixture(params=INIT_INPUTS)
def setup_fixture(request, monkeypatch, tmp_path):
    """This fixture helps simplify writing tests by:
    - parametrizing the different cloud provider inputs in a single place
    - creating a tmp directory (and file) for the `nebari-config.yaml` to be save to
    - monkeypatching functions that call out to external APIs.
    """
    render_config_inputs = request.param
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    def _mock_kubernetes_versions(grab_latest_version=False):
        # template for all `kubernetes_versions` calls
        # monkeypatched to avoid making outbound API calls in CI
        k8s_versions = ["1.18", "1.19", "1.20"]
        m = Mock()
        m.return_value = k8s_versions
        if grab_latest_version:
            m.return_value = k8s_versions[-1]
        return m

    def _mock_aws_availability_zones(region="us-west-2"):
        m = Mock()
        m.return_value = ['us-west-2a', 'us-west-2b']
        return m

    if cloud_provider == "aws":
        monkeypatch.setattr(
            "_nebari.provider.cloud.amazon_web_services.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
        monkeypatch.setattr(
            "_nebari.provider.cloud.amazon_web_services.zones",
            _mock_aws_availability_zones(),
        )
    elif cloud_provider == "azure":
        monkeypatch.setattr(
            "_nebari.provider.cloud.azure_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "do":
        monkeypatch.setattr(
            "_nebari.provider.cloud.digital_ocean.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "gcp":
        monkeypatch.setattr(
            "_nebari.provider.cloud.google_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
        monkeypatch.setenv("PROJECT_ID", "pytest-project")

    output_directory = tmp_path / f"{cloud_provider}_output_dir"
    output_directory.mkdir()
    nebari_config_loc = output_directory / NEBARI_CONFIG_FN

    # data that should NOT be deleted when `nebari render` is called
    # see test_render.py::test_remove_existing_renders
    preserved_directory = output_directory / PRESERVED_DIR
    preserved_directory.mkdir()
    preserved_filename = preserved_directory / "file.txt"
    preserved_filename.write_text("This is a test...")

    yield (nebari_config_loc, render_config_inputs)
