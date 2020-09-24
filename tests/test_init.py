import pytest

from qhub.cli.initialize import generate_qhub_config


@pytest.mark.parametrize(
    "config_filename",
    [
        "qhub/template/configs/config_aws.yaml",
        "qhub/template/configs/config_gcp.yaml",
        "qhub/template/configs/config_do.yaml",
    ],
)
def test_init(config_filename, tmp_path):
    out = tmp_path / "test"

    generate_qhub_config(config_filename, out)
