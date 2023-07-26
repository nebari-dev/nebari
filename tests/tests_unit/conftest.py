from unittest.mock import Mock

import pytest

from tests.tests_unit.utils import INIT_INPUTS, NEBARI_CONFIG_FN, PRESERVED_DIR


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

    if cloud_provider == "aws":
        monkeypatch.setattr(
            "_nebari.utils.amazon_web_services.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "azure":
        monkeypatch.setattr(
            "_nebari.utils.azure_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "do":
        monkeypatch.setattr(
            "_nebari.utils.digital_ocean.kubernetes_versions",
            _mock_kubernetes_versions(),
        )
    elif cloud_provider == "gcp":
        monkeypatch.setattr(
            "_nebari.utils.google_cloud.kubernetes_versions",
            _mock_kubernetes_versions(),
        )

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
