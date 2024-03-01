import pytest

import socket

import six.moves.urllib.request as urllib_request

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.stream import portforward


def kubernetes_port_forward(pod_name, port, namespace):
    config.load_kube_config()
    Configuration.set_default(Configuration.get_default_copy())
    core_v1 = core_v1_api.CoreV1Api()

    def kubernetes_create_connection(address, *args, **kwargs):
        pf = portforward(
            core_v1.connect_get_namespaced_pod_portforward,
            pod_name, namespace, ports=str(port)
        )
        return pf.socket(port)

    socket.create_connection = kubernetes_create_connection


@pytest.fixture(scope="module", autouse=True)
def port_forward():
    return kubernetes_port_forward(
        pod_name="loki-backend-0",
        port=3100,
        namespace="dev"
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
def test_loki_endpoint(endpoint_path):
    url = f'http://loki-backend-0.pod.dev.kubernetes:3100/{endpoint_path}'
    response = urllib_request.urlopen(url)
    response.read().decode('utf-8')
    assert response.code == 200
    response.close()
