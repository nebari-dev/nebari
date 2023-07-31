import pytest
from kubernetes import client, config

from tests.tests_integration.deployment_fixtures import on_cloud


@pytest.mark.xfail(reason="Preemptible instances are not supported on AWS atm")
@on_cloud("aws")
def test_preemptible(deploy):
    config.load_kube_config(
        config_file=deploy["stages/02-infrastructure"]["kubeconfig_filename"][
            "value"
        ]
    )

    api_instance = client.CoreV1Api()
    nodes = api_instance.list_node()
    node_labels_map = {}
    for node in nodes.items:
        node_name = node.metadata.labels['eks.amazonaws.com/nodegroup']
        node_labels_map[node_name] = node.metadata.labels
    preemptible_node_group_labels = node_labels_map["preemptible-node-group"]
    assert preemptible_node_group_labels["eks.amazonaws.com/capacityType"] == "SPOT"
