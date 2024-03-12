import socket
import typing

from kubernetes import config
from kubernetes.client.api import core_v1_api
from kubernetes.client.models import V1Pod
from kubernetes.stream import portforward


def kubernetes_port_forward(
    pod_labels: typing.Dict[str, str], port: int, namespace: str = "dev"
) -> V1Pod:
    """Given pod labels and port, finds the pod name and port forwards to
    the given port.
    :param pod_labels: dict of labels, by which to search the pod
    :param port: port number to forward
    :param namespace: kubernetes namespace name
    :return: kubernetes pod object
    """
    config.load_kube_config()
    core_v1 = core_v1_api.CoreV1Api()
    label_selector = ",".join([f"{k}={v}" for k, v in pod_labels.items()])
    pods = core_v1.list_namespaced_pod(
        namespace=namespace, label_selector=label_selector
    )
    assert pods.items
    pod = pods.items[0]
    pod_name = pod.metadata.name

    def kubernetes_create_connection(address, *args, **kwargs):
        pf = portforward(
            core_v1.connect_get_namespaced_pod_portforward,
            pod_name,
            namespace,
            ports=str(port),
        )
        return pf.socket(port)

    socket.create_connection = kubernetes_create_connection
    return pod
