import os
import pytest

from qhub.cli.initialize import generate_qhub_config


@pytest.mark.parametrize(
    "config_dir",
    [
        "qhub/template/configs/aws",
        "qhub/template/configs/gcp",
        "qhub/template/configs/do",
    ],
)
def test_init(config_dir, tmp_path):
    out = tmp_path / "test"
    os.mkdir(out)
    generate_qhub_config(config_dir, out)
