# Day-to-day Maintenance

All modifications to the infrastructure should be done with GitHub
Pull-Requests.

## Common Modifications

### Modifying docker images: jupyterlab, jupyterhub, dask-workers

The docker images used for dask-worker and jupyterlab user
environments are pulled from a docker container registry. The images
are built based on the images specified in
[image](../image). There are four images that are currently built

- jupyterlab :: modification of jupyterlab instances for each user
- dask-worker :: modification of dask workers and dask scheduler
- jupyterhub :: the jupyterhub server (allows for customization of hub UI)

Each docker image is customized with its respective directory
(e.g. `image/Dockerfile.jupyterlab` -> `image/jupyterlab/*`. For
jupyterlab the environment is located at
`image/jupyterlab/environment.yaml`. Thus to add a package to the
environment simply submit a pull request with the new package.

At this current point in time once a user submits a pull request to
create the given docker image and the PR is accepted with images
built, a PR must follow that adds the image to the qhub
deployment. This can be done by modifying
`infrastructure/variables.tf` and the configuration file.

### Adding additional worker nodegroups

Adding additional nodegroups can be done by editing the configuration
file. While a `general`, `user`, and `worker` nodegroup are required
you may create any additional node group. Take for example the Digital
Ocean configuration.

```yaml
digital_ocean:
  region: nyc3
  kubernetes_version: "1.18.8-do.0"
  node_groups:
    general:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 4
    worker:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 4
```

To add a node group for a node group called `worker-high-mem` simply
add to the configuration. The same applies for AWS, GCP, and DO.

```yaml
digital_ocean:
  region: nyc3
  kubernetes_version: "1.18.8-do.0"
  node_groups:
    general:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 4
    worker:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 4
    worker-high-memory:
      instance: "m6-2vcpu-16gb"
      min_nodes: 1
      max_nodes: 4
```

### Setting specific JupyterLab profile to run on a nodegroup

Sometimes we would like a profile to execute on nodes that are not in
the normal nodegroup. In the example above we created a high memory
node group. To make the jupyterlab profile `small worker` use the high
memory nodegroup do the following.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      groups:
        - admin
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
        image: "quansight/qhub-jupyterlab:d52cea07f70cc8b35c29b327bbd2682f29d576ad"
```

We add the `node_selector` attribute. Note that for AWS, GCP, and DO they have different keys for the nodegroup name.

- AWS :: `eks.amazonaws.com/nodegroup`
- GCP :: `cloud.google.com/gke-nodepool`
- DO :: `doks.digitalocean.com/node-pool`

Since we are using digital ocean in this example we then need to set the following.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      groups:
        - admin
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
        image: "quansight/qhub-jupyterlab:d52cea07f70cc8b35c29b327bbd2682f29d576ad"
        node_selector:
          "doks.digitalocean.com/node-pool": worker-high-memory
```

### Setting specific dask workers to run on a nodegroup

Suppose we want a specific dask worker profile to run on a specific
node group. Here we demonstrate annotating the DO example configuration.

```yaml
profiles:
  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:d52cea07f70cc8b35c29b327bbd2682f29d576ad"
```

[Dask-gateway](https:/d52cea07f70cc8b35c29b327bbd2682f29d576ad/gateway.dask.org/api-server.html#kube-cluster-config)
takes additional configuration for the scheduler pods and
workers. Remember similar to assigning node groups to specific
jupyterlab instances we must get the key for the node pool.

- AWS :: `eks.amazonaws.com/nodegroup`
- GCP :: `cloud.google.com/gke-nodepool`
- DO :: `doks.digitalocean.com/node-pool`

Since we are using digital ocean in this example we then need to set the following.

```yaml
profiles:
  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:d52cea07f70cc8b35c29b327bbd2682f29d576ad"
      scheduler_extra_pod_config:
        nodeSelector:
          "doks.digitalocean.com/node-pool": worker-high-memory
      worker_extra_pod_config:
        nodeSelector:
          "doks.digitalocean.com/node-pool": worker-high-memory
```

## General Modifications

The infrastructure was designed with the goal in mind that each
`module` is orthogonal.
