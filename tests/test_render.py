import pytest

from qhub.render import render_default_template


@pytest.mark.parametrize(
    "config_filename",
    [
        "tests/assets/config_aws.yaml",
        "tests/assets/config_gcp.yaml",
        "tests/assets/config_do.yaml",
        "tests/assets/config_do_patch.yaml",
    ],
)
def test_render(config_filename, tmp_path):
    output_directory = tmp_path / "test"

    render_default_template(str(output_directory), config_filename)
