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


def add_gpu_config(config):
    gpu_node = {
        "instance": "g4dn.xlarge",
        "min_nodes": 1,
        "max_nodes": 4,
        "single_subnet": False,
        "gpu": True,
    }
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
                "beta.kubernetes.io/instance-type": "g4dn.xlarge",
            },
        },
    }
    config["amazon_web_services"]["node_groups"]["gpu-tesla-g4"] = gpu_node
    config["profiles"]["jupyterlab"].append(jupyterlab_profile)

    config["environments"]["environment-gpu.yaml"] = _create_gpu_environment()
    return config


def add_preemptible_node_group(config, cloud="amazon_web_services"):
    config[cloud]["node_groups"][PREEMPTIBLE_NODE_GROUP_NAME] = {
        "instance": "m5.xlarge",
        "min_nodes": 1,
        "max_nodes": 5,
        "single_subnet": False,
        "preemptible": True,
    }
    return config
