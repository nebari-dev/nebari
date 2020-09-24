import pytest

from qhub.render import render_default_template


@pytest.mark.parametrize(
    "config_filename",
    [
        "qhub/template/configs/config_aws.yaml",
        "qhub/template/configs/config_gcp.yaml",
        "qhub/template/configs/config_do.yaml",
    ],
)
def test_render(config_filename, tmp_path):
    output_directory = tmp_path / "test"

    render_default_template(str(output_directory), config_filename)
