# Configuration

The configuration file is split into several sections. In this page,
we detail the requirements necessary for the YAML configuration
file. The configuration file is always validated by a [pydantic
schema](https://pydantic-docs.helpmanual.io/) in `qhub/schema.py`. For
the ultimate source of truth visit this file though these docs should
be accurate.

## General

```yaml
project_name: do-jupyterhub # name of the kubernetes/Cloud deployment 
namespace: dev
provider: <provider_alias> # determines the choice of cloud provider for the deployment
ci_cd: github-actions # continuous integration and continuous deployment framework to use
domain: "do.qhub.dev" # top level URL exposure to monitor JupyterLab
```

 - `project_name`: should be compatible with the Cloud provider naming
   convention. Generally only use `A-Z`, `a-z`, `-`, and `_`.

 - `namespace`: is used in combination with `project_name` to label
   resources. In addition `namespace` also determines the `namespace`
   that used when deploying kubernetes resources for qhub. Has a
   default value of `dev`.

 - `provider` possible values are `do` for DigitalOcean, `aws` for
    Amazon AWS, `gcp` for Google Could Provider, `azure` for Microsoft
    Azure, and `local` for a local or existing kubernetes deployment.

 - `ci_cd`: is the continuous integration and continuous deployment
   framework to use. Currently only `github-actions` is supported.

 - `domain`: is the top level URL to put JupyterLab and future
   services under such a monitoring. For example `jupyter.qhub.dev`
   would be the domain for JupyterHub to be exposed under. Note that
   this domain does not have to have `jupyter` in it.

## Certificate

By default to simplify initial deployment `QHub` uses traefik to
create a self-signed certificate. In order to create a certificate
that is signed so that web browsers do not throw errors we currently
support [Let's Encrypt](https://letsencrypt.org/).

```yaml
certificate:
  type: self-signed
```

To use Let's Encrypt you must specify an email address that let's
encrypt will associate the generated certificate with and whether to
use the [staging server](https://acme-staging-v02.api.letsencrypt.org/directory) or [production server](https://acme-v02.api.letsencrypt.org/directory). In general you
should use the production server.

```yaml
certificate:
  type: lets-encrypt
  acme_email: <your-email-address>
  acme_server:
```

You may also supply a custom self signed certificate and secret
key. Note that the kubernetes default namespace that QHub uses is
`dev` if not specified. Otherwise it will be your `namespace` defined
in the `qhub-config.yaml`.

```yaml
certificate:
  type: existing
  secret_name: <secret-name>
```

To add the tls certificate to kubernetes run the following command
with existing files.

```shell
kubectl create secret tls <secret-name> \
  --namespace=<namespace> \
  --cert=path/to/cert/file --key=path/to/key/file
```

## Security

This section is for configuring security relating to the QHub
deployment. [obvious sentence]

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

### Authentication

`security.authentication` is for configuring the OAuth and GitHub
Provider, password based authentication, or custom
authentication. 

#### Auth0 Based Authentication

[Auth0](https://auth0.com/#!) can be used for authentication. While it
is not free there is a reasonable free tier that allows deployment of
QHub clusters on many different social providers, passwordless, and
email based authentication. QHub has command line options with running
`qhub init` which allow for automation of creation of the application
via `--auth-provider=auth0 --auth-auto-provision`. However for most
users this may not be the most convenient solution. Here are docs on
[creating an Auth0
Application](https://auth0.com/docs/applications). Make sure to select
`Regular Web Application`. Important to note is the `auth0_subdomain`
field which must be only the `<auth0_subdomain>.auth0.com`. So for the
following `qhub-dev.auth0.com` the subdomain would be `qhub-dev`. Note
that all the usernames will be the email addresses of users (not
usernames).

```yaml
security:
  authentication:
    type: Auth0
    config:
      client_id: ...
      client_secret: ...
      oauth_callback_url: 'http[s]://[your-host]/hub/oauth_callback'
      scope: ["openid", "email", "profile"]
      auth0_subdomain: ...
```

#### GitHub Based Authentication

Github has instructions for [creating OAuth
applications](https://docs.github.com/en/developers/apps/creating-an-oauth-app). Note
that QHub usernames will their GitHub usernames.

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: ...
      client_secret: ...
      oauth_callback_url: 'http[s]://[your-host]/hub/oauth_callback'
```

#### Password Based Authentication

For Password based authentication. Note that users will require a
`password` field that can be generated via the following command:
`python -c "import bcrypt; print(bcrypt.hashpw(b'<password>',
bcrypt.gensalt()).decode('utf-8'))"`. Make sure to replace
`<password>` with whatever password you are wanting.

```yaml
security:
  authentication:
    type: password
  users:
    ...
    <username>:
      ...
      password: $2b$....
```

#### Custom Authentication

You can specify arbitrary authentication via the `custom` type. All
`config` attributes will be set as traitlets to the configured
authentication class. The attributes will obey the type set via yaml
(e.g. True -> will be a boolean True for Traitets).

```yaml
security:
  authentication:
    type: custom
    authentication_class: "oauthenticator.google.GoogleOAuthenticator"
    config:
      login_service: "My Login Button"
      oauth_callback_url: 'http[s]://[your-host]/hub/oauth_callback'
      client_id: 'your-client-id'
      client_secret: 'your-client-secret'
```

### User Management

`users` and `groups` allows one to provision UNIX permissions to each
user. Any user is assigned a `uid`, `primary_group`, and optionally
any number of `secondary_groups`. Note that `uid` and `gid` fields
must be unique and are required.

```yaml
security:
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

* The `primary_group` is the group name assigned to files that are
written for the user.
* `groups` are a mapping of group name to group IDs. It is
  recommended to not change the IDs assigned to groups and users
  after creation, since it may lead to login issues.
  > NOTE: While the demo shows IDs between `100` and
`1000`, it is recommended to start with high User ID numbers
e.g. `10000000`. `ids` technically supports 2 billion `ids`.

## Provider Infrastructure

Finally, comes the Kubernetes infrastructure deployment. Although
quite similar, each provider has a different configuration.

The following configuration sets up a kubernetes deployment with
autoscaling node groups. Depending on the cloud provider there might
be restrictions, which are detailed on each section.

For any of the providers (besides local), adding a node group is as
easy as the following, which adds a `high-memory` group:

```yaml
<provider>:
  node_groups:
    ...
    high-memory:
      instance: "s-2vcpu-4gb"
      min_nodes: 1
      max_nodes: 50
    ...
```

> For each provider details such as **instance names**, **availability zones**,
and **Kubernetes versions** will be DIFFERENT. [duplicated info]

### Providers

#### DigitalOcean

DigitalOcean has a restriction with autoscaling in that the minimum
nodes allowed (`min_nodes` = 1) is one but is by far the cheapest
provider even accounting for spot/premptible instances. In addition
Digital Ocean does not have accelerator/gpu support. Digital Ocean is
a great default choice for tying out QHub. Below is the recommended
setup.

> Note: DigitalOcean regularly updates Kubernetes versions hence, the
> field `kubernetes_version` will most likely have to be changed.
> [See available instance types for
> DigitalOcean](https://www.digitalocean.com/docs/droplets/).  If you
> used `qhub init` this version will automatically be compute for you
> Do not copy the version you see bellow

To see available instance types refer to [Digital Ocean Instance
Types](https://www.digitalocean.com/docs/droplets/). Additionally the
digial ocean cli `doctl` has [support for listing
droplets](https://www.digitalocean.com/docs/apis-clis/doctl/reference/compute/droplet/list/).

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

Google Cloud has the best support for QHub and is a great default
choice for a production deployment. It allows auto-scaling to zero
within the node group. There are no major restrictions.

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

## Terraform State

Terraform manages the state of all the deployed resources via
[backends](https://www.terraform.io/docs/language/settings/backends/index.html). Terraform
requires storing the state in order to keep track of the names, ids,
and states of deployed resources. The simplest approach is storing the
state on the local filesystem but is not recommended and is not the
default of QHub. `terraform_state` is either `remote`, `existing` or
`local` with a default value of `remote`. This decides whether to
control the state of the cluster `local` via tfstate file (not
recommended), on an already `existing` terraform state store or
remotely and auto creating the terraform state store. See [terraform
remote state](https://www.terraform.io/docs/language/state/index.html)
docs. If you are doing anything other than testing we highly recommend
`remote` unless you know what you are doing.

The following are examples. `remote` and `local` are
straightforward. For a `local` provider that deploys on an existing
kubernetes cluster the kubernetes remote backend is used.

```yaml
terraform_state:
  type: remote
```

```yaml
terraform_state:
  type: local
```

Using an existing terraform backend can be done by specifying the
`backend` and arbitrary key/value pairs in the `config`.

```yaml
terraform_state:
  type: existing
  backend: s3
  config:
    bucket: mybucket
    key: "path/to/my/key"
    region: "us-east-1"
```



## Terraform Modules

By default QHub uses a set terraform modules developed by Quansight
managed at https://github.com/quansight/qhub-terraform-modules. This
collection is used to provide a consistent interface between cloud
providers and manage how jupyterlab, dask-gateway and related
resources are deployed. However, if you want to make modifications on
the deployed resources you can tweak the repository used. This field
is optional. This is usually the easiest way to tweak QHub outside of
the `qhub-config.yaml` file.

```yaml
terraform_modules:
  repository: "github.com/quansight/qhub-terraform-modules"
  rev: main
```

## Default Images

Default images are to the default image run if not specified in a
profile (described in the next section). The `jupyterhub` key controls
the jupyterhub image run. These control the docker image used to run
JupyterHub, the default JupyterLab image, and default Dask worker
image.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:c36eace493739be280c71bec59b80659115db5d5"
  jupyterlab: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
  dask_worker: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
```

## Storage

Control the amount of storage allocated to shared filesystems.

> Note: when the storage size is changed, in most providers it will
> automatically delete (!) the previous storage place.

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
        image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
        image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
```

For each `profiles.jupyterlab` is a named JupyterLab profile. It
closely follows the
[KubeSpawner](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html)
API. The only exception is that two keys are added `users` and
`groups` which allow restriction of profiles to a given set of groups
and users.  We recommend using groups to manage profile access.

Finally, we allow for configuration of the Dask workers. In general,
similar to the JupyterLab instances you only need to configuration the
cores and memory.

### Limiting profiles to specific users and groups

Sometimes on a select set of users should have access to specific
resources e.g. gpus, high memory nodes etc. QHub has support for
limiting resources.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      ...
      users:
        - example-user
      groups:
        - admin
        - users
```

### JupyterLab Profile Node Selectors

A common operation is to target jupyterlab profiles to specific node
labels. In order to target a specific node groups add the
following. This example shows a GKE node groups with name
`user-large`. Other cloud providers will have different node labels.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      ...
      kubespawner_override:
        ...
        node_selector:
          "cloud.google.com/gke-nodepool": "user-large"
        ...
```

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

certificate:
  type: self-signed

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
  jupyterhub: "quansight/qhub-jupyterhub:c36eace493739be280c71bec59b80659115db5d5"
  jupyterlab: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
  dask_worker: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"

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
        image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      default: true
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
        image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"

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
