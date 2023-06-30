import typing
from unittest.mock import Mock

import pytest

from _nebari.config import write_configuration
from _nebari.initialize import render_config
from _nebari.render import render_template
from _nebari.stages.bootstrap import CiEnum
from _nebari.stages.kubernetes_keycloak import AuthenticationEnum
from _nebari.stages.terraform_state import TerraformStateEnum
from nebari import schema

# from _nebari.stages.base import get_available_stages
from nebari.plugins import nebari_plugin_manager


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

    def _mock_return_value(return_value):
        m = Mock()
        m.return_value = return_value
        return m

    def _mock_aws_availability_zones(region="us-west-2"):
        m = Mock()
        m.return_value = ["us-west-2a", "us-west-2b"]
        return m

    MOCK_VALUES = {
        # AWS
        "_nebari.provider.cloud.amazon_web_services.kubernetes_versions": ["1.18", "1.19", "1.20"],
        "_nebari.provider.cloud.amazon_web_services.check_credentials": None,
        "_nebari.provider.cloud.amazon_web_services.regions": ["us-east-1", "us-west-2"],
        "_nebari.provider.cloud.amazon_web_services.zones": ["us-west-2a", "us-west-2b"],
        "_nebari.provider.cloud.amazon_web_services.instances": {
            "m5.xlarge": "m5.xlarge",
            "m5.2xlarge": "m5.2xlarge",
        },
        # Azure
        "_nebari.provider.cloud.azure_cloud.kubernetes_versions": ["1.18", "1.19", "1.20"],
        "_nebari.provider.cloud.azure_cloud.check_credentials": None,
        # Digital Ocean
        "_nebari.provider.cloud.digital_ocean.kubernetes_versions": ["1.19.2-do.3", "1.20.2-do.0", "1.21.5-do.0"],
        "_nebari.provider.cloud.digital_ocean.check_credentials": None,
        "_nebari.provider.cloud.digital_ocean.regions": [
            {'name': 'New York 3', 'slug': 'nyc3'},
        ],
        "_nebari.provider.cloud.digital_ocean.instances": [
            {'name': 's-2vcpu-4gb', 'slug': 's-2vcpu-4gb'},
            {'name': 'g-2vcpu-8gb', 'slug': 'g-2vcpu-8gb'},
            {'name': 'g-8vcpu-32gb', 'slug': 'g-8vcpu-32gb'},
            {'name': 'g-4vcpu-16gb', 'slug': 'g-4vcpu-16gb'}
        ],
        # Google Cloud
        "_nebari.provider.cloud.google_cloud.kubernetes_versions": ["1.18", "1.19", "1.20"],
        "_nebari.provider.cloud.google_cloud.check_credentials": None,
    }

    for attribute_path, return_value in MOCK_VALUES.items():
        monkeypatch.setattr(attribute_path, _mock_return_value(return_value))

    monkeypatch.setenv("PROJECT_ID", "pytest-project")


@pytest.fixture(
    params=[
        # project, namespace, domain, cloud_provider, ci_provider, auth_provider
        (
            "pytestdo",
            "dev",
            "do.nebari.dev",
            schema.ProviderEnum.do,
            CiEnum.github_actions,
            AuthenticationEnum.password,
        ),
        (
            "pytestaws",
            "dev",
            "aws.nebari.dev",
            schema.ProviderEnum.aws,
            CiEnum.github_actions,
            AuthenticationEnum.password,
        ),
        (
            "pytestgcp",
            "dev",
            "gcp.nebari.dev",
            schema.ProviderEnum.gcp,
            CiEnum.github_actions,
            AuthenticationEnum.password,
        ),
        (
            "pytestazure",
            "dev",
            "azure.nebari.dev",
            schema.ProviderEnum.azure,
            CiEnum.github_actions,
            AuthenticationEnum.password,
        ),
    ]
)
def nebari_config_options(request) -> schema.Main:
    """This fixtures creates a set of nebari configurations for tests"""
    DEFAULT_GH_REPO = "github.com/test/test"
    DEFAULT_TERRAFORM_STATE = TerraformStateEnum.remote

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
    return nebari_plugin_manager.config_schema.parse_obj(
        render_config(**nebari_config_options)
    )


@pytest.fixture
def nebari_stages():
    return nebari_plugin_manager.ordered_stages


@pytest.fixture
def nebari_render(nebari_config, nebari_stages, tmp_path):
    NEBARI_CONFIG_FN = "nebari-config.yaml"

    config_filename = tmp_path / NEBARI_CONFIG_FN
    write_configuration(config_filename, nebari_config)
    render_template(tmp_path, nebari_config, nebari_stages)
    return tmp_path, config_filename
