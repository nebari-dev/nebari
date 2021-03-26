# Configuration

The configuration file is split into several sections. In this page, we detail the requirements necessary for
the YAML configuration file.

## General

```yaml
project_name: do-jupyterhub # name of the kubernetes/Cloud deployment 
namespace: dev
provider: <provider_alias> # determines the choice of cloud provider for the deployment
ci_cd: github-actions # continuous integration and continuous deployment framework to use
domain: "do.qhub.dev" # top level URL exposure to monitor JupyterLab
terraform_state: remote
```

`project_name` should be compatible with the Cloud provider naming convention.

`namespace` is used in combination with `project_name` to label
resources. In addition `namespace` also determines the `namespace`
that used when deploying kubernetes resources for qhub. Has a default
value of `dev`.

`provider` possible values are `do` for DigitalOcean, `aws` for Amazon AWS, `gcp` for Google Could Provider and `azure`
for Microsoft Azure.

`ci_cd` is the continuous integration and continuous deployment
framework to use. Currently `github-actions` is supported.

`domain` is the top level URL to put JupyterLab and future services
under such a monitoring. For example `jupyter.do.qhub.dev` would be
the domain for JupyterHub to be exposed under.

`terraform_state` is either `remote` or `local` with a default value
of `remote`. This decides whether to control the state of the cluster
locally or remotely. See [terraform remote
state](https://www.terraform.io/docs/language/state/index.html) docs.

## Security

This section is for configuring security relating to the QHub deployment. [obvious sentence]

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://jupyter.do.qhub.dev/hub/oauth_callback
  users:
    example-user:
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

`security.authentication` is for configuring the OAuth provider used
for authentication. Currently, the configuration shows GitHub but Auth0
is also supported.

```yaml
security:
  authentication:
    type: Auth0
    config:
      client_id: ...
      client_secret: ...
      oauth_callback_url: ...
      scope: ["openid", "email", "profile"]
      auth0_subdomain: ...
```

`users` and `groups` allows one to provision UNIX permissions to each
user. Any user is assigned a `uid`, `primary_group`, and optionally
any number of `secondary_groups`.
* The `primary_group` is the group name assigned to files that are
written for the user.
* `groups` are a mapping of group name to group IDs. It is
  recommended to not change the IDs assigned to groups and users
  after creation, since it may lead to login issues.
  > NOTE: While the demo shows IDs between `100` and
`1000`, it is recommended to start with high User ID numbers
e.g. `10000000`. `ids` technically supports 2 billion `ids`.

## Provider Infrastructure

Finally, comes the Kubernetes infrastructure deployment. Although quite similar,
each provider has a different configuration.

The following configuration sets up a kubernetes deployment with
autoscaling node groups. Depending on the cloud provider there
might be restrictions, which are detailed on each section.

For any of the providers, adding a node group is as easy as
the following, which adds a `high-memory` group:

```yaml
high-memory:
  instance: "s-2vcpu-4gb"
  min_nodes: 1
  max_nodes: 50
```

> For each provider details such as **instance names**, **availability zones**,
and **Kubernetes versions** will be DIFFERENT. [duplicated info]

### Providers
#### DigitalOcean

DigitalOcean has a restriction with autoscaling in that the minimum
nodes allowed (`min_nodes` = 1) is one. Below is the recommended setup.
> Note: DigitalOcean regularly updates Kubernetes versions hence, the
> field `kubernetes_version` will most likely have to be changed.
> [See available instance types for DigitalOcean](https://www.digitalocean.com/docs/droplets/).

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


#### Google Cloud Provider (GCP)

Google Cloud has the best support for QHub. It allows auto-scaling to
zero within the node group. There are no major restrictions.

To see available instance types refer to
[GCP docs](https://cloud.google.com/compute/docs/machine-types).

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

#### Amazon Web Services (AWS)

Amazon Web Services has similar support to DigitalOcean and does not
allow auto-scaling below 1 node. Additionally, AWS requires that a
Kubernetes cluster run in two Availability Zones (AZs).

Consult [AWS instance types](https://aws.amazon.com/ec2/instance-types/)
for possible options.

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

#### Local (Existing) Kubernetes Cluster

Deploying to a local existing kuberentes cluster has different options
than the cloud providers. `kube_context` is an optional key that can
be used to deploy to a non-default context. The default node selectors
will allow pods to be scheduled anywhere. This can be adjusted to
schedule pods on different labeled nodes. Allowing for similar
functionality to node groups in the cloud.

```yaml
local:
  kube_context: minikube
  node_selectors:
    general:
      key: kubernetes.io/os
      value: linux
    user:
      key: kubernetes.io/os
      value: linux
    worker:
      key: kubernetes.io/os
      value: linux
```

## Default Images

Default images are to the default image run if not specified in a
profile (described in the next section). The `jupyterhub` key controls
the jupyterhub image run.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:b89526c59a5c269c776b535b887bd110771ad601"
  jupyterlab: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
  dask_worker: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"
```

## Storage

Control the amount of storage allocated to shared filesystems.
> Note: when the storage size is changed, it will automatically
> delete (!) the previous storage place.

```yaml
storage:
  conda_store: 20Gi
  shared_filesystem: 10Gi
```

## Profiles

Profiles are used to control the JupyterLab user instances and
Dask-workers provided by Dask-gateway.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      users:
        - example-user
      groups:
        - admin
      default: true
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"
```

For each `profiles.jupyterlab` is a named JupyterLab profile. It
closely follows the
[KubeSpawner](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html)
API. The only exception is that two keys are added `users` and
`groups` which allow restriction of profiles to a given set of groups and users.
We recommend using groups to manage profile access.

Finally, we allow for configuration of the Dask workers. In general,
similar to the JupyterLab instances you only need to configuration the
cores and memory.

## Themes

### Customizing JupyterHub theme

JupyterHub can be customized since QHub uses
[Quansight/qhub-jupyterhub-theme](https://github.com/quansight/qhub-jupyterhub-theme). Available
theme options. Note that if you want to change the logo it must be an
accessible url to the logo.

```yaml
theme:
  jupyterhub:
    hub_title: QHub - thisisatest
    hub_subtitle: Autoscaling Compute Environment
    welcome: |
      Welcome to jupyter.github-actions.qhub.dev. It is maintained by <a href="http://quansight.com">Quansight
      staff</a>. The hub's configuration is stored in a github repository based on
      <a href="https://github.com/Quansight/qhub/">https://github.com/Quansight/qhub/</a>.
      To provide feedback and report any technical problems, please use the 
      <a href="https://github.com/Quansight/qhub/issues">github issue tracker</a>.
    logo: /hub/custom/images/jupyter_qhub_logo.svg
    primary_color: '#4f4173'
    secondary_color: '#957da6'
    accent_color: '#32C574'
    text_color: '#111111'
    h1_color: '#652e8e'
    h2_color: '#652e8e'
```

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
      - dask==2.30.0
      - distributed==2.30.1
      - dask-gateway=0.9.0
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
      - dask==2.30.0
      - distributed==2.30.1
      - dask-gateway=0.9.0
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```

QHub is experimenting with a new way of distributing environments
using [conda-store](https://github.com/quansight/conda-store). Please
expect this environment distribution method to change over time.

Each environment configuration is a `environment.<filename>` mapping to a
conda environment definition file. If you need to pin a specific version,
please include it in the definition. One current requirement is that
each environment include `ipykernel`, `ipywidgets`, `dask==2.30.0`,
`distributed==2.30.1`, `dask-gateway==0.9.0`. Upon changing the
environment definition expect 1-10 minutes upon deployment of the
configuration for the environment to appear.

# Full Configuration Example

Everything in the configuration is set besides [???]

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
    example-user:
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
      min_nodes: 2
      max_nodes: 4

default_images:
  jupyterhub: "quansight/qhub-jupyterhub:b89526c59a5c269c776b535b887bd110771ad601"
  jupyterlab: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
  dask_worker: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"

theme:
  jupyterhub:
    hub_title: QHub - thisisatest
    hub_subtitle: Autoscaling Compute Environment
    welcome: |
      Welcome to jupyter.github-actions.qhub.dev. It is maintained by <a href="http://quansight.com">Quansight
      staff</a>. The hub's configuration is stored in a github repository based on
      <a href="https://github.com/Quansight/qhub/">https://github.com/Quansight/qhub/</a>.
      To provide feedback and report any technical problems, please use the 
      <a href="https://github.com/Quansight/qhub/issues">github issue tracker</a>.
    logo: /hub/custom/images/jupyter_qhub_logo.svg
    primary_color: '#4f4173'
    secondary_color: '#957da6'
    accent_color: '#32C574'
    text_color: '#111111'
    h1_color: '#652e8e'
    h2_color: '#652e8e'

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
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      default: true
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"

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
      - dask==2.30.0
      - distributed==2.30.1
      - dask-gateway=0.9.0
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
      - dask==2.30.0
      - distributed==2.30.1
      - dask-gateway=0.9.0
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```

# Initializing Repository

1. Create a repository

2. Put configuration file in directory in name `qhub-config.yaml`

~2. Put configuration file in the directory with name `qhub-config.yaml` [???]

3. Initialize the QHub repository

```shell
pip install qhub-ops
qhub render -c qhub-config.yaml
```
This will initialize the repository and next proceed to
installation. Do not commit to repo to GitHub until you have
initialized the `terraform-state` directory seen in installation.
