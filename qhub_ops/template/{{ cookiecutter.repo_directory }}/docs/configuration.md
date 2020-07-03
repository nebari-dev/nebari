# Configuration

The configuration file is split into several sections.

## General

```yaml
project_name: do-jupyterhub
provider: do
ci_cd: github-actions
domain: "do.qhub.dev"
```

`project_name` is the name that resources within the cloud
deployment/kubernetes will be deployed with.

`provider` determines which cloud provider to use for the
deployment. Possible values are `do`, `aws`, `gcp`.

`ci_cd` is the continuous integration and continuous deployment
framework to use. Currently `github-actions` is supported.

`domain` is the top level url to put jupyterlab and future services
under such a monitoring. For example `jupyter.do.qhub.dev` would be
the domain for jupyterhub to be exposed under.

## Security

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://jupyter.do.qhub.dev/hub/oauth_callback
  users:
    costrouc:
      uid: 1000
      primary_group: users
      secondary_groups:
        - billing
    dharhas:
      uid: 1001
      primary_group: admin
  groups:
    users:
      gid: 100
    admin:
      gid: 101
    billing:
      gid: 102
```

The security section is for configuring security relating to the qhub
deployment.

`security.authentication` is for configuring the oauth provider used
for authentication. Currently the configuration shows github but Auth0
is also supported.

```yaml
security:
  authentication:
    type: Auth0
    config:
      client_id: ...
      client_secret: ...
      oauth_callback_url: ...
      scope: ['openid', 'email', 'profile']
      auth0_subdomain: ...
```

`users` and `groups` allows you to provision unix permissions to each
user. Any user is assigned a `uid`, `primary_group`, and optionally
any number of `secondary_groups`. The `primary_group` is the group
name assigned to files that are written for the user. `groups` is
simply a mapping of group name to group ids. It is recommended to not
change the ids assigned to groups and users after creation since it
may lead to login issues. While the demo shows ids around `100` and
`1000` it is recommended to start with high uid numbers
e.g. `10000000`. `ids` technically supports 2 billion `ids`.

## Provider Infrastructure

Finally comes the kubernetes infrastructure deployment. Each provider
has different configuration but they are similar. The following
configuration sets up a kubernetes deployment with autoscaling node
groups. Depending on the cloud provider there may be restrictions that
are detailed in each section.

For any of the providers adding an additional node group is as easy as
adding a node group such as `high-memory`

```yaml
high-memory:
  instance: "s-2vcpu-4gb"
  min_nodes: 1
  max_nodes: 50
```

Note that for each provider the instance names, availability zones,
and kubernetes versions will be different.

### Digital Ocean

Digital Ocean has a restriction with autoscaling in that `min_nodes`
cannot be less than 1. Here is a recommended setup. Note that digital
ocean regularly updates the kubernetes versions so this field will
likely have to be changed. [See available instance types for digital
ocean.](https://www.digitalocean.com/docs/droplets/).

```yaml
digital_ocean:
  region: nyc3
  kubernetes_version: "1.16.6-do.2"
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

### Google Cloud Provider

Google Cloud has the best support for QHub. I allows auto-scaling to
zero within the node group. There are no major restrictions. [To see
available instance types refer to gcp docs.](https://cloud.google.com/compute/docs/machine-types)

```yaml
google_cloud_platform:
  project: test-test-test
  region: us-central1
  zone: us-central1-c
  availability_zones: ["us-central1-c"]
  kubernetes_version: "1.14.10-gke.31"
  node_groups:
    general:
      instance: n1-standard-2
      min_nodes: 1
      max_nodes: 1
    user:
      instance: n1-standard-2
      min_nodes: 0
      max_nodes: 2
    worker:
      instance: n1-standard-2
      min_nodes: 0
      max_nodes: 5
```

### Amazon Web Services

Amazon Web Services has similar support to Digital Ocean and does not
allow auto-scaling below 1 node. Additionally AWS requires that a
kubernetes cluster run in two availability zones. [Consult aws instance
types for possible options.](https://aws.amazon.com/ec2/instance-types/)

```yaml
amazon_web_services:
  region: us-west-2
  availability_zones: ["us-west-2a", "us-west-2b"]
  kubernetes_version: "1.14"
  node_groups:
    general:
      instance: "m5.large"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "m5.large"
      min_nodes: 1
      max_nodes: 2
    worker:
      instance: "m5.large"
      min_nodes: 1
      max_nodes: 2
```

## Default Images

Default images are to the default image run if not specified in a
profile (described in the next section). The `jupyterhub` key controls
the jupyterhub image run.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
  jupyterlab: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
  dask_worker: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
```

## Storage

Control the amount of storage allocated to shared filesystems. Note
that when you change the storage size it will delete the previous
storage!

```yaml
storage:
  conda_store: 20Gi
  shared_filesytem: 10Gi
```

## Profiles

Profiles are used to control the jupyterlab user instances and
dask-workers provided by dask-gateway.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      users:
        - costrouc
      groups:
        - admin
      default: true
      kubespawner_override:
        cpu_limit: 1
        cpu_guarentee: 1
        mem_limit: 1G
        mem_guarentee: 1G
        image: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarentee: 1.25
        mem_limit: 2G
        mem_guarentee: 2G
        image: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
```

For each `profiles.jupyterlab` is a named jupyterlab profile. It
closely follows the
[KubeSpawner](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html)
api. The only exception is that two keys are added `users` and
`groups` which allow restriction of profiles to  a given set of groups and users. We recommend using groups to manage profile access.

Finally we allow for configuration of the dask workers. In general
similar to the jupyterlab instances you only need to configuration the
cores and memory.

## Environments

```yaml
environments:
  "environment-default.yaml":
    name: default
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.7
      - ipykernel
      - ipywidgets
      - dask==2.14.0
      - distributed==2.14.0
      - dask-gateway=0.6.1
      - numpy
      - numba
      - pandas

  "environment-example-2.yaml":
    name: example-2
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.7
      - ipykernel
      - ipywidgets
      - dask==2.14.0
      - distributed==2.14.0
      - dask-gateway=0.6.1
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```

QHub is experimenting with a new way of distributing environments
using [conda-store](https://github.com/quansight/conda-store). Please
expect this environment distribution method to change over time. Each
environment configuration is a `environment.<filename>` mapping to a
conda environment definition file. If you need to pin specific version
please include it in the definition. One current requirement is that
each environment include `ipykernel`, `ipywidgets`, `dask==2.14.0`,
`distributed==2.14.0`, `dask-gateway==0.6.1`. Upon changing the
environment definition expect 1-10 minutes upon deployment of the
configuration for the environment to apear.

# Example Full Configuration

Everything in the configuration is set besides 

```yaml
project_name: do-jupyterhub
provider: do
ci_cd: github-actions
domain: "do.qhub.dev"

security:
  authentication:
    type: GitHub
    config:
      client_id: CLIENT_ID
      client_secret: CLIENT_SECRET
      oauth_callback_url: https://jupyter.do.qhub.dev/hub/oauth_callback
  users:
    costrouc:
      uid: 1000
      primary_group: users
      secondary_groups:
        - billing
    dharhas:
      uid: 1001
      primary_group: admin
    tonyfast:
      uid: 1002
      primary_group: admin
    prasunanand:
      uid: 1003
      primary_group: admin
    aktech:
      uid: 1004
      primary_group: users
      secondary_groups:
        - admin
  groups:
    users:
      gid: 100
    admin:
      gid: 101
    billing:
      gid: 102


digital_ocean:
  region: nyc3
  kubernetes_version: "1.16.6-do.2"
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
      min_nodes: 2
      max_nodes: 4


default_images:
  jupyterhub: "quansight/qhub-jupyterhub:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
  jupyterlab: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
  dask_worker: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"


profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      groups:
        - admin
      kubespawner_override:
        cpu_limit: 1
        cpu_guarentee: 1
        mem_limit: 1G
        mem_guarentee: 1G
        image: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      default: true
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarentee: 1.25
        mem_limit: 2G
        mem_guarentee: 2G
        image: "quansight/qhub-jupyterlab:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:8425c36fe1d407e226eb8061f4f27ad1706e0a6f"


environments:
  "environment-default.yaml":
    name: default
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.7
      - ipykernel
      - ipywidgets
      - dask==2.14.0
      - distributed==2.14.0
      - dask-gateway=0.6.1
      - numpy
      - numba
      - pandas

  "environment-example-2.yaml":
    name: example-2
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.7
      - ipykernel
      - ipywidgets
      - dask==2.14.0
      - distributed==2.14.0
      - dask-gateway=0.6.1
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```

# Initializing Repository

1. Create a repository

2. Put configuration file in directory in name `qhub-ops-config.yaml`

3. Initialize the qhub repository

```shell
pip install qhub-ops
qhub-ops render -c qhub-ops-config.yaml -o ./ -f
```

This will initialize the repository and next proceed to
installation. Do not commit to repo to github until you have
initialized the `terraform-state` directory seen in installation.
