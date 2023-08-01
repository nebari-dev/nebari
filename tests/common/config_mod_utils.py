PREEMPTIBLE_NODE_GROUP_NAME = "preemptible-node-group"


def _create_gpu_environment():
    return {
        "name": "gpu",
        "channels": ["pytorch", "nvidia", "conda-forge"],
        "dependencies": [
            "python=3.10.8",
            "ipykernel=6.21.0",
            "ipywidgets==7.7.1",
            "torchvision",
            "torchaudio",
            "cudatoolkit",
            "pytorch-cuda=11.7",
            "pytorch::pytorch",
        ],
    }


def add_gpu_config(config, cloud="aws"):

    gpu_node_group = "gpu-node"
    if cloud == "aws":
        cloud_name = "amazon_web_services"
        gpu_name = "g4dn.xlarge"
        node_selector = "beta.kubernetes.io/instance-type"
        extra_config = {
            "single_subnet": False,
            "gpu": True,
        }
        node_selector_val = "g4dn.xlarge"
    elif cloud == "gcp":
        cloud_name = "google_cloud_platform"
        gpu_name = "n1-standard-16"
        node_selector = "cloud.google.com/gke-nodepool"
        extra_config = {"guest_accelerators": [{"name": "nvidia-tesla-t4", "count": 1}]}
        node_selector_val = gpu_node_group
    else:
        raise ValueError(f"GPU not supported/tested on {cloud}")

    gpu_node = {"instance": gpu_name, "min_nodes": 0, "max_nodes": 4, **extra_config}
    gpu_docker_image = "quay.io/nebari/nebari-jupyterlab-gpu:2023.7.1"
    jupyterlab_profile = {
        "display_name": "GPU Instance",
        "description": "4 CPU / 16GB RAM / 1 NVIDIA T4 GPU (16 GB GPU RAM)",
        "groups": ["gpu-access"],
        "kubespawner_override": {
            "image": gpu_docker_image,
            "cpu_limit": 4,
            "cpu_guarantee": 3,
            "mem_limit": "16G",
            "mem_guarantee": "10G",
            "extra_resource_limits": {"nvidia.com/gpu": 1},
            "node_selector": {
                node_selector: node_selector_val,
            },
        },
    }
    config[cloud_name]["node_groups"][gpu_node_group] = gpu_node
    config["profiles"]["jupyterlab"].append(jupyterlab_profile)

    config["environments"]["environment-gpu.yaml"] = _create_gpu_environment()
    return config


def add_preemptible_node_group(config, cloud="aws"):
    if cloud == "aws":
        cloud_name = "amazon_web_services"
        instance_name = "m5.xlarge"
    elif cloud == "gcp":
        cloud_name = "google_cloud_platform"
        instance_name = "n1-standard-8"
    else:
        raise ValueError("Invalid cloud for preemptible config")
    config[cloud_name]["node_groups"][PREEMPTIBLE_NODE_GROUP_NAME] = {
        "instance": instance_name,
        "min_nodes": 1,
        "max_nodes": 5,
        "single_subnet": False,
        "preemptible": True,
    }
    return config
