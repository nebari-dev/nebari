from functools import partial
from unittest.mock import Mock

import pytest

from qhub.initialize import render_config

INIT_INPUTS = [
    # project, namespace, domain, cloud_provider, ci_provider, auth_provider
    ("pytestdo", "dev", "do.qhub.dev", "do", "github-actions", "github"),
    ("pytestaws", "dev", "aws.qhub.dev", "aws", "github-actions", "github"),
    ("pytestgcp", "dev", "gcp.qhub.dev", "gcp", "github-actions", "github"),
    ("pytestazure", "dev", "azure.qhub.dev", "azure", "github-actions", "github"),
]

QHUB_CONFIG_FN = "qhub-config.yaml"
PRESERVED_DIR = "preserved_dir"
DEFAULT_GH_REPO = "github.com/test/test"
DEFAULT_TERRAFORM_STATE = "remote"


# use this partial function for all tests that need to call `render_config`
render_config_partial = partial(
    render_config,
    repository=DEFAULT_GH_REPO,
    repository_auto_provision=False,
    auth_auto_provision=False,
    terraform_state=DEFAULT_TERRAFORM_STATE,
    disable_prompt=True,
)


@pytest.fixture(params=INIT_INPUTS)
def setup_fixture(request, monkeypatch, tmp_path):
    """This fixture helps simplify writing tests by:
    - parametrizing the different cloud provider inputs in a single place
    - creating a tmp directory (and file) for the `qhub-config.yaml` to be save to
    - monkeypatching functions that call out to external APIs
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

    if cloud_provider == "aws":
        monkeypatch.setattr(
            "qhub.utils.amazon_web_services.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "azure":
        monkeypatch.setattr(
            "qhub.utils.azure_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "do":
        monkeypatch.setattr(
            "qhub.utils.digital_ocean.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "gcp":
        monkeypatch.setattr(
            "qhub.utils.google_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )

    output_directory = tmp_path / f"{cloud_provider}_output_dir"
    output_directory.mkdir()
    qhub_config_loc = output_directory / QHUB_CONFIG_FN

    # data that should NOT be deleted when `qhub render` is called
    # see test_render.py::test_remove_existing_renders
    preserved_directory = output_directory / PRESERVED_DIR
    preserved_directory.mkdir()
    preserved_filename = preserved_directory / "file.txt"
    preserved_filename.write_text("This is a test...")

    yield (qhub_config_loc, render_config_inputs)
