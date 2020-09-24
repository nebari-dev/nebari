import pytest

import qhub.schema


@pytest.mark.parametrize(
    "config_filename",
    [
        'qhub/template/configs/config_aws.yaml',
        'qhub/template/configs/config_gcp.yaml',
        'qhub/template/configs/config_do.yaml',
    ],
)
def test_validation(config_filename):
    import yaml

    with open(config_filename) as f:
        data = yaml.safe_load(f.read())

    assert qhub.schema.verify(data) is None
