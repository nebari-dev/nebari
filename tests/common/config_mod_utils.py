import dataclasses
import typing

from _nebari.stages.infrastructure import AWSNodeGroup, GCPNodeGroup
from _nebari.stages.kubernetes_services import (
    AccessEnum,
    CondaEnvironment,
    JupyterLabProfile,
    KubeSpawner,
)

PREEMPTIBLE_NODE_GROUP_NAME = "preemptible-node-group"


@dataclasses.dataclass
class GPUConfig:
    cloud: str
    gpu_name: str
    node_selector: str
    node_selector_val: str
    extra_config: dict
    min_nodes: typing.Optional[int] = 0
    max_nodes: typing.Optional[int] = 2
    node_group_name: typing.Optional[str] = "gpu-node"
    docker_image: typing.Optional[str] = "quay.io/nebari/nebari-jupyterlab-gpu:2023.7.1"

    def node(self):
        return {
            "instance": self.gpu_name,
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            **self.extra_config,
        }


AWS_GPU_CONF = GPUConfig(
    cloud="amazon_web_services",
    gpu_name="g4dn.xlarge",
    node_selector="beta.kubernetes.io/instance-type",
    node_selector_val="g4dn.xlarge",
    extra_config={
        "single_subnet": False,
        "gpu": True,
    },
)


GCP_GPU_CONF = GPUConfig(
    cloud="google_cloud_platform",
    gpu_name="n1-standard-16",
    node_selector="cloud.google.com/gke-nodepool",
    node_selector_val="g4dn.xlarge",
    extra_config={"guest_accelerators": [{"name": "nvidia-tesla-t4", "count": 1}]},
)


GPU_CONFIG = {
    "aws": AWS_GPU_CONF,
    "gcp": GCP_GPU_CONF,
}


def _create_gpu_environment():
    return CondaEnvironment(
        name="gpu",
        channels=["pytorch", "nvidia", "conda-forge"],
        dependencies=[
            "python=3.10.8",
            "ipykernel=6.21.0",
            "ipywidgets==7.7.1",
            "torchvision",
            "torchaudio",
            "cudatoolkit",
            "pytorch-cuda=11.7",
            "pytorch::pytorch",
        ],
    )


def add_gpu_config(config, cloud="aws"):
    gpu_config = GPU_CONFIG.get(cloud)
    if not gpu_config:
        raise ValueError(f"GPU not supported/tested on {cloud}")

    if cloud == "aws":
        gpu_node_group = AWSNodeGroup(
            instance=gpu_config.gpu_name,
            min_nodes=gpu_config.min_nodes,
            max_nodes=gpu_config.max_nodes,
            single_subnet=gpu_config.extra_config["single_subnet"],
            gpu=gpu_config.extra_config["gpu"],
        )
        kubespawner_overrides = KubeSpawner(
            image=gpu_config.docker_image,
            cpu_limit=4,
            cpu_guarantee=3,
            mem_limit="16G",
            mem_guarantee="10G",
            extra_resource_limits={"nvidia.com/gpu": 1},
            node_selector={
                gpu_config.node_selector: gpu_config.node_selector_val,
            },
        )
    else:
        gpu_node_group = None
        kubespawner_overrides = None

    jupyterlab_profile = JupyterLabProfile(
        display_name="GPU Instance",
        description="4 CPU / 16GB RAM / 1 NVIDIA T4 GPU (16 GB GPU RAM)",
        access=AccessEnum.all,
        groups=None,
        kubespawner_override=kubespawner_overrides,
    )

    cloud_section = getattr(config, gpu_config.cloud, None)
    cloud_section.node_groups[gpu_config.node_group_name] = gpu_node_group
    config.profiles.jupyterlab.append(jupyterlab_profile)
    config.environments["environment-gpu.yaml"] = _create_gpu_environment()

    return config


def add_preemptible_node_group(config, cloud="aws"):
    node_group = None
    if cloud == "aws":
        cloud_name = "amazon_web_services"
        # TODO: how to make preemptible?
        node_group = AWSNodeGroup(
            instance="m5.xlarge",
            min_nodes=1,
            max_nodes=5,
            single_subnet=False,
        )
    elif cloud == "gcp":
        cloud_name = "google_cloud_platform"
        node_group = GCPNodeGroup(
            instance="n1-standard-8",
            min_nodes=1,
            max_nodes=5,
            preemptible=True,
        )
    else:
        raise ValueError("Invalid cloud for preemptible config")

    cloud_section = getattr(config, cloud_name, None)
    if node_group:
        cloud_section.node_groups[PREEMPTIBLE_NODE_GROUP_NAME] = node_group

    return config
