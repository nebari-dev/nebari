import pytest

import qhub.schema


@pytest.mark.parametrize(
    "config_filename",
    [
        "qhub/template/configs/aws/qhub-config.yaml",
        "qhub/template/configs/gcp/qhub-config.yaml",
        "qhub/template/configs/do/qhub-config.yaml",
    ],
)
def test_validation(config_filename):
    import yaml

    with open(config_filename) as f:
        data = yaml.safe_load(f.read())

    assert qhub.schema.verify(data) is None
