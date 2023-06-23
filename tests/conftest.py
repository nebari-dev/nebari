import typing
from unittest.mock import Mock

import pytest

from _nebari.initialize import render_config
from _nebari.render import render_template
from _nebari.stages.base import get_available_stages
from nebari import schema


@pytest.fixture(autouse=True)
def mock_all_cloud_methods(monkeypatch):
    def _mock_kubernetes_versions(
        k8s_versions: typing.List[str] = ["1.18", "1.19", "1.20"],
        grab_latest_version=False,
    ):
        # template for all `kubernetes_versions` calls
        # monkeypatched to avoid making outbound API calls in CI
        m = Mock()
        m.return_value = k8s_versions
        if grab_latest_version:
            m.return_value = k8s_versions[-1]
        return m

    def _mock_aws_availability_zones(region="us-west-2"):
        m = Mock()
        m.return_value = ["us-west-2a", "us-west-2b"]
        return m

    monkeypatch.setattr(
        "_nebari.provider.cloud.amazon_web_services.kubernetes_versions",
        _mock_kubernetes_versions(),
    )
    monkeypatch.setattr(
        "_nebari.provider.cloud.amazon_web_services.zones",
        _mock_aws_availability_zones(),
    )
    monkeypatch.setattr(
        "_nebari.provider.cloud.azure_cloud.kubernetes_versions",
        _mock_kubernetes_versions(),
    )
    monkeypatch.setattr(
        "_nebari.provider.cloud.digital_ocean.kubernetes_versions",
        _mock_kubernetes_versions(["1.19.2-do.3", "1.20.2-do.0", "1.21.5-do.0"]),
    )
    monkeypatch.setattr(
        "_nebari.provider.cloud.google_cloud.kubernetes_versions",
        _mock_kubernetes_versions(),
    )
    monkeypatch.setenv("PROJECT_ID", "pytest-project")


@pytest.fixture(
    params=[
        # project, namespace, domain, cloud_provider, ci_provider, auth_provider
        (
            "pytestdo",
            "dev",
            "do.nebari.dev",
            schema.ProviderEnum.do,
            schema.CiEnum.github_actions,
            schema.AuthenticationEnum.password,
        ),
        (
            "pytestaws",
            "dev",
            "aws.nebari.dev",
            schema.ProviderEnum.aws,
            schema.CiEnum.github_actions,
            schema.AuthenticationEnum.password,
        ),
        (
            "pytestgcp",
            "dev",
            "gcp.nebari.dev",
            schema.ProviderEnum.gcp,
            schema.CiEnum.github_actions,
            schema.AuthenticationEnum.password,
        ),
        (
            "pytestazure",
            "dev",
            "azure.nebari.dev",
            schema.ProviderEnum.azure,
            schema.CiEnum.github_actions,
            schema.AuthenticationEnum.password,
        ),
    ]
)
def nebari_config_options(request) -> schema.Main:
    """This fixtures creates a set of nebari configurations for tests"""
    DEFAULT_GH_REPO = "github.com/test/test"
    DEFAULT_TERRAFORM_STATE = schema.TerraformStateEnum.remote

    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = request.param

    return dict(
        project_name=project,
        namespace=namespace,
        nebari_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        auth_provider=auth_provider,
        repository=DEFAULT_GH_REPO,
        repository_auto_provision=False,
        auth_auto_provision=False,
        terraform_state=DEFAULT_TERRAFORM_STATE,
        disable_prompt=True,
    )


@pytest.fixture
def nebari_config(nebari_config_options):
    return schema.Main(**render_config(**nebari_config_options))


@pytest.fixture
def nebari_stages():
    return get_available_stages()


@pytest.fixture
def nebari_render(nebari_config, nebari_stages, tmp_path):
    NEBARI_CONFIG_FN = "nebari-config.yaml"

    config_filename = tmp_path / NEBARI_CONFIG_FN
    schema.write_configuration(config_filename, nebari_config)
    render_template(tmp_path, nebari_config, nebari_stages)
    return tmp_path, config_filename
