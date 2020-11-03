import pytest

from qhub.render import render_default_template


@pytest.mark.parametrize(
    "config_dir",
    [
        "qhub/template/configs/aws",
        "qhub/template/configs/gcp",
        "qhub/template/configs/do",
        # "tests/assets/config_gcp_gpu.yaml",
    ],
)
def test_render(config_dir, tmp_path):
    output_directory = tmp_path / "test"

    render_default_template(str(output_directory), config_dir)
