import pytest

import six.moves.urllib.request as urllib_request
from kubernetes.client import V1Pod

from tests.common.kube_api import kubernetes_port_forward

MINIO_PORT = 9000
MINIO_POD_LABELS = {
    "app.kubernetes.io/instance": "nebari-loki-minio",
    "app.kubernetes.io/name": "minio"
}


@pytest.fixture(scope="module")
def port_forward():
    """Pytest fixture to port forward loki backend pod to make it accessible
    on localhost so that we can run some tests on it.
    """
    return kubernetes_port_forward(
        pod_labels=MINIO_POD_LABELS,
        port=MINIO_PORT
    )


def test_minio_accessible(port_forward: V1Pod):
    """This will hit liveness endpoint of minio  API and verify that we
    get a 200 status code, to make sure minio is up and running.
    :param endpoint_path: a loki api endpoint path
    :param port_forward: pytest fixture to port forward.
    :return:
    """
    pod_name = port_forward.metadata.name
    url = f'http://{pod_name}.pod.dev.kubernetes:{MINIO_PORT}/minio/health/live'
    response = urllib_request.urlopen(url)
    response.read().decode('utf-8')
    assert response.code == 200
    response.close()
