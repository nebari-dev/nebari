import pytest
from kubernetes import client, config

from tests.common.config_mod_utils import PREEMPTIBLE_NODE_GROUP_NAME


@pytest.mark.preemptible
def test_preemptible(nebari_config):
    if nebari_config.provider == "aws":
        name_label = "eks.amazonaws.com/nodegroup"
        preemptible_key = "eks.amazonaws.com/capacityType"
        expected_value = "SPOT"
        pytest.xfail("Preemptible instances are not supported on AWS atm")

    elif nebari_config.provider == "gcp":
        name_label = "cloud.google.com/gke-nodepool"
        preemptible_key = "cloud.google.com/gke-preemptible"
        expected_value = "true"
    else:
        pytest.skip("Unsupported cloud for preemptible")

    api_instance = client.CoreV1Api()
    nodes = api_instance.list_node()
    node_labels_map = {}
    for node in nodes.items:
        node_name = node.metadata.labels[name_label]
        node_labels_map[node_name] = node.metadata.labels
    preemptible_node_group_labels = node_labels_map[PREEMPTIBLE_NODE_GROUP_NAME]
    assert preemptible_node_group_labels.get(preemptible_key) == expected_value
