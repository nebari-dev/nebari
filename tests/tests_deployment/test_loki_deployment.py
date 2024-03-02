import pytest

import six.moves.urllib.request as urllib_request
from kubernetes.client import V1Pod

from tests.common.kube_api import kubernetes_port_forward

LOKI_BACKEND_PORT = 3100
LOKI_BACKEND_POD_LABELS = {
    "app.kubernetes.io/instance": "nebari-loki",
    "app.kubernetes.io/component": "backend"
}


@pytest.fixture(scope="module")
def port_forward():
    """Pytest fixture to port forward loki backend pod to make it accessible
    on localhost so that we can run some tests on it.
    """
    return kubernetes_port_forward(
        pod_labels=LOKI_BACKEND_POD_LABELS,
        port=LOKI_BACKEND_PORT
    )


@pytest.mark.parametrize(
    "endpoint_path",
    (
            "metrics",
            "services",
            "config",
            "ready",
            "log_level",
    ),
)
def test_loki_endpoint(endpoint_path: str, port_forward: V1Pod):
    """This will hit some endpoints in the loki API and verify that we
    get a 200 status code, to make sure Loki is working properly.
    :param endpoint_path: a loki api endpoint path
    :param port_forward: pytest fixture to port forward.
    :return:
    """
    pod_name = port_forward.metadata.name
    url = f'http://{pod_name}.pod.dev.kubernetes:{LOKI_BACKEND_PORT}/{endpoint_path}'
    response = urllib_request.urlopen(url)
    response.read().decode('utf-8')
    assert response.code == 200
    response.close()
