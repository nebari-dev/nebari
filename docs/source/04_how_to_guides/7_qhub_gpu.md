# GPUs on QHub

Having access to  GPUs is of prime importance for speeding up many computations
by several orders of magnitude. QHub provides a way to achieve that, we will go
through achieving that for each Cloud provider.

## Clouds

### Google Cloud Platform

By default the quota to spin up GPUs on GCP is 0. Make sure you have requested
GCP Support to increase quota of allowed GPUs for your billing account to be the
number of GPUs you need access to.

See GCP Pre-requisites here: https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#requirements

Here are the steps you need to follow to get GPUs working with GCP:

#### 1. Add GPU node group in `qhub-config.yml` file

Add a node group for GPU instance in the `node_groups` section of `google_cloud_platform` section,
and under the `guest_accelerators` section add the name of the GPU. A comprehensive list of GPU
types can be found in at the Official GCP docs here: https://cloud.google.com/compute/docs/gpus

An example of getting GPUs on GCP:

```yml
google_cloud_platform:
  project: project-name
  region: us-central1
  zone: us-central1-c
  availability_zones:
  - us-central1-c
  kubernetes_version: 1.18.16-gke.502
  node_groups:
    # ....
    gpu-tesla-t4:
      instance: "n1-standard-8"     # 8 vCPUs, 30 GB: Skylake, Broadwell, Haswell, Sandy Bridge, and Ivy Bridge
      min_nodes: 0
      max_nodes: 5
      guest_accelerators:
        - name: nvidia-tesla-k80    # 12 GB GDDR5: Nividia Tesla K80
          count: 1

```

Notes:

- One of the restrictions regarding GPUs on GCP is they can only be used
with general-purpose *[N1 machine types](https://cloud.google.com/compute/docs/machine-types#n1_machine_types)*,
except A100 GPUs, which are only supported on *[a2 machine types](https://cloud.google.com/blog/products/compute/announcing-google-cloud-a2-vm-family-based-on-nvidia-a100-gpu)*

- If you are not using the gcp provider in QHub but are using gcp (let's say deploying
  on an existing gcp cluster). You will need to manually install NVIDIA drivers to the
  cluster, See documentation for the same here: https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#installing_drivers


See limitations here: https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#limitations


#### 2. Add GPU instance in the JupyterLab profiles

```yml
profiles:
  jupyterlab:
# ....
  - display_name: Large GPU Instance
    description: Stable environment with 8 cpu / 32 GB ram and 1 Nvidia Tesla T4
    kubespawner_override:
      cpu_limit: 8
      cpu_guarantee: 7.25
      mem_limit: 32G
      mem_guarantee: 24G
      image: quansight/qhub-jupyterlab:v0.3.11
      extra_resource_limits:
        nvidia.com/gpu: 1
      node_selector:
          "cloud.google.com/gke-nodepool": "gpu-tesla-t4"
```

### Amazon Web Services

#### 1. Add GPU node group in `qhub-config.yml` file

```yaml
amazon_web_services:
  region: us-west-2
#   ...
    gpu-g4:
      instance: g4dn.2xlarge     # NVIDIA Tesla T4
      min_nodes: 1
      max_nodes: 5
      gpu: true     # This marks the given instance type is gpu enabled.
```

#### 2. Add GPU instance in the JupyterLab profiles

```yml
profiles:
  jupyterlab:
# ....
    - display_name: GPU Instance
      description: Stable environment with 8 cpu / 32 GB ram and 1 Nvidia Tesla T4
      kubespawner_override:
        cpu_limit: 8
        cpu_guarantee: 7.25
        mem_limit: 32G
        mem_guarantee: 24G
        image: quansight/qhub-jupyterlab:main
        extra_resource_limits:
          nvidia.com/gpu: 1
        node_selector:
          "eks.amazonaws.com/nodegroup": "gpu-g4"
```

Notes:

- If you are not using the gcp provider in QHub but are using aws (let's say deploying
  on an existing aws cluster). You will need to manually install NVIDIA drivers to the
    cluster, See documentation for the same here: https://github.com/NVIDIA/k8s-device-plugin

### DigitalOcean

DigitalOcean does not support GPUs at the time of writing this.

## Create conda environment to take advantage of gpus

First you need to consult the driver version of nvidia being
used. This can easily be checked via the command `nvidia-smi`.

```shell
$ nvidia-smi
Thu May 20 18:05:14 2021       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 450.51.06    Driver Version: 450.51.06    CUDA Version: 11.0     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  Tesla K80           Off  | 00000000:00:04.0 Off |                    0 |
| N/A   32C    P8    29W / 149W |      0MiB / 11441MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

The important section is `CUDA Version`. In general you should install
a version of cudatoolkit that is less than or equal to the cuda
version (but not too old).  If you install `cudatoolkit-dev` and
`cudatoolkit` make sure that they are the same version exactly
including minor version. Also in the near future cuda should have
better [ABI
compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/index.html).

Bellow is an example gpu environment. 

```yaml
name: gpu-environment
channels:
 - conda-forge
dependencies:
 - python
 - cudatoolkit ==11.0.3
 - cudatoolkit-dev ==11.0.3
 - cupy
 - numba
```

We are working hard to make the GPU expeirence on Qhub as streamlined
as possible. There are many small gotchas when working with GPUs and
getting all the drivers installed properly.
