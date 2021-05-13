# GPUs on QHub

Having access to  GPUs is of prime importance for speeding up many computations
by several orders of magnitude. QHub provides a way to achieve that, we will go
through achieving that for each Cloud provider.

## Google Cloud Platform

### Pre-requisites

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

Note: One of the restrictions regarding GPUs on GCP is they can only be used
with general-purpose *[N1 machine types](https://cloud.google.com/compute/docs/machine-types#n1_machine_types)*,
except A100 GPUs, which are only supported on *[a2 machine types](https://cloud.google.com/blog/products/compute/announcing-google-cloud-a2-vm-family-based-on-nvidia-a100-gpu)*

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

## DigitalOcean

DigitalOcean does not support GPUs at the time of writing this.
