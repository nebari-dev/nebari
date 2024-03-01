import pytest

import socket

import six.moves.urllib.request as urllib_request

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.stream import portforward


LOKI_BACKEND_PORT = 3100
LOKI_BACKEND_POD_LABELS = {
    "app.kubernetes.io/instance": "nebari-loki",
    "app.kubernetes.io/component": "backend"
}


def kubernetes_port_forward(pod_labels, port, namespace="dev"):
    """Given pod labels and port, finds the pod name and port forwards to
    the given port.
    """
    config.load_kube_config()
    Configuration.set_default(Configuration.get_default_copy())
    core_v1 = core_v1_api.CoreV1Api()

    pods = core_v1.list_namespaced_pod(
        namespace=namespace,
        label_selector=pod_labels
    )
    assert pods.items
    pod = pods.items[0]
    pod_name = pod.metadata.name

    def kubernetes_create_connection(address, *args, **kwargs):
        pf = portforward(
            core_v1.connect_get_namespaced_pod_portforward,
            pod_name, namespace, ports=str(port)
        )
        return pf.socket(port)

    socket.create_connection = kubernetes_create_connection
    return pod


@pytest.fixture(scope="module")
def port_forward():
    labels = [f"{k}={v}" for k, v in LOKI_BACKEND_POD_LABELS.items()]
    return kubernetes_port_forward(
        pod_labels=",".join(labels),
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
def test_loki_endpoint(endpoint_path, port_forward):
    pod_name = port_forward.metadata.name
    url = f'http://{pod_name}.pod.dev.kubernetes:{LOKI_BACKEND_PORT}/{endpoint_path}'
    response = urllib_request.urlopen(url)
    response.read().decode('utf-8')
    assert response.code == 200
    response.close()
