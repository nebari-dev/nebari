import socket

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.stream import portforward


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
