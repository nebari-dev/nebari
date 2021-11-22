import dask_gateway
import os

import pytest
from tests_deployment import constants
from tests_deployment.utils import monkeypatch_ssl_context, get_jupyterhub_token

monkeypatch_ssl_context()


@pytest.fixture
def dask_gateway_object():
    """Connects to Dask Gateway cluster from outside the cluster."""
    os.environ['JUPYTERHUB_API_TOKEN'] = get_jupyterhub_token()
    return dask_gateway.Gateway(
        address=f'https://{constants.QHUB_HOSTNAME}/{constants.GATEWAY_ENDPOINT}',
        auth='jupyterhub',
        proxy_address=f'tcp://{constants.QHUB_HOSTNAME}:8786'
    )


def test_dask_gateway(dask_gateway_object):
    """This test checks if we're able to connect to dask gateway."""
    assert dask_gateway_object.list_clusters() == []


def test_dask_gateway_cluster_options(dask_gateway_object):
    """Tests Dask Gateway's cluster options."""
    cluster_options = dask_gateway_object.cluster_options()
    assert cluster_options.conda_environment == "dask"
    assert cluster_options.profile == "Small Worker"
    assert cluster_options.environment_vars == {}
