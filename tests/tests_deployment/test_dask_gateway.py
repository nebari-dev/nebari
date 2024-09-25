import os

import dask_gateway
import pytest

from tests.tests_deployment import constants
from tests.tests_deployment.utils import get_jupyterhub_token


@pytest.fixture
def dask_gateway_object():
    """Connects to Dask Gateway cluster from outside the cluster."""
    os.environ["JUPYTERHUB_API_TOKEN"] = get_jupyterhub_token(
        "dask-gateway-pytest-token"
    )

    # Create custom class from Gateway that disables the tls/ssl verification
    # to do that we will override the self._request_kwargs dictionary within the
    # __init__, targeting aiohttp.ClientSession.request method

    class DaskGateway(dask_gateway.Gateway):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._request_kwargs.update({"ssl": False})

    return DaskGateway(
        address=f"https://{constants.NEBARI_HOSTNAME}/{constants.GATEWAY_ENDPOINT}",
        auth="jupyterhub",
        proxy_address=f"tcp://{constants.NEBARI_HOSTNAME}:8786",
    )


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_dask_gateway(dask_gateway_object):
    """This test checks if we're able to connect to dask gateway."""
    assert dask_gateway_object.list_clusters() == []


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_dask_gateway_cluster_options(dask_gateway_object):
    """Tests Dask Gateway's cluster options."""
    cluster_options = dask_gateway_object.cluster_options()
    # # dask conda environment is not built in time to be available
    # assert cluster_options.conda_environment == "dask"
    assert cluster_options.profile in {"Small Worker", "Medium Worker"}
    assert cluster_options.environment_vars == {}
