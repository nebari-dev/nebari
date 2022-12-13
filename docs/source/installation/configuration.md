# Advanced configuration

This is a page dedicated to the `qhub-config.yaml` file, the file that `qhub` uses to deploy and redeploy changes to
your infrastructure. The `qhub-config.yaml` configuration file is split into several sections and in this page, we
detail the requirements necessary for this YAML-formatted configuration file. In the [Usage](usage.md) section we
covered how you can auto-generate this file using `qhub init` (and properly set options/flags and environment
variables).

> NOTE: The configuration file is always validated by a [pydantic schema](https://pydantic-docs.helpmanual.io/) in
> [qhub/schema.py](https://github.com/Quansight/qhub/blob/main/qhub/schema.py)

## General

```yaml
project_name: dojupyterhub # name of the kubernetes/Cloud deployment
namespace: dev
provider: <provider_alias> # determines the choice of cloud provider for the deployment
domain: "do.qhub.dev" # top level URL exposure to monitor JupyterLab
```

- `project_name`: should be compatible with the Cloud provider naming convention. Generally only use `A-Z`, `a-z`, `-`,
  and `_` (see [Project Naming Conventions](./usage.md#project-naming-convention) for more details).

- `namespace`: is used in combination with `project_name` to label resources. In addition `namespace` also determines
  the `namespace` that used when deploying kubernetes resources for qhub.

  - Default value: `dev`

- `provider`: possible values are

  - `do` for DigitalOcean
  - `aws` for Amazon AWS
  - `gcp` for Google Could Provider
  - `azure` for Microsoft Azure
  - `local` for a local or existing kubernetes deployment

- `domain`: is the top level URL to put JupyterLab and future services under (such a monitoring). For example `qhub.dev`
  would be the domain for JupyterHub to be exposed under.

## Continuous integration and continuous deployment

`ci_cd`: is optional and specifies the continuous integration and continuous deployment framework to use. QHub uses
infrastructure-as-code to allow developers and users of QHub to request change to the environment via pull requests
(PRs) which then get approved by administration. You may configure CI/CD process to watch for pull-requests or commits
on specific branches. Currently CI/CD can be setup for either GitHub Actions or GitLab CI.

```yaml
ci_cd:
  type: gitlab-ci
  branch: main
  commit_render: true
  before_script:
    - echo "running commands before ci completes"
  after_script:
    - echo "running commands after ci completes"
    - echo "additional commands to run"
```

- `type`: current supported CI providers are `github-actions` and `gitlab-ci`
- `branch`: branch to use to commit `qhub render` changes to
- `commit_render`: whether to commit the rendered changes back into the repo. Optional, defaults to `true`.
- `before_script`: optional script to run before CI starts QHub infrastructure deployment. This is useful in cases that
  additional setup is required for QHub to deploy the resources. Only supported on `gitlab-ci` at the moment.
- `after_script`: optional script to run after CI ends QHub infrastructure deployment. This is useful in cases to notify
  resources of successful QHub deployment. Only supported on `gitlab-ci` at the moment.

If `ci_cd` is not supplied, no CI/CD will be auto-generated, however, we advise employing an infrastructure-as-code
approach. This allows teams to more quickly modify their QHub deployment, empowering developers and data scientists to
request the changes and have them approved by an administrator.

## Certificate

By default, to simplify initial deployment `qhub` uses traefik to create a self-signed certificate. In order to create a
certificate that's signed so that web browsers don't throw errors we currently support
[Let's Encrypt](https://letsencrypt.org/).

```yaml
certificate:
  type: self-signed
```

To use Let's Encrypt you must specify an email address that Let's Encrypt will associate the generated certificate with
and whether to use the [staging server](https://acme-staging-v02.api.letsencrypt.org/directory) or
[production server](https://acme-v02.api.letsencrypt.org/directory). In general you should use the production server, as
seen below.

> NOTE: Let's Encrypt heavily rate limits their production endpoint and provisioning https certificates can often fail
> due to this limit.

```yaml
certificate:
  type: lets-encrypt
  acme_email: <your-email-address>
  acme_server: https://acme-v02.api.letsencrypt.org/directory
```

Note the above snippet will already be present if you provided an `--ssl-cert-email` when you ran `qhub init`.

You may also supply a custom self-signed certificate and secret key. Note that the kubernetes default namespace that
QHub uses is `dev`. Otherwise, it will be your `namespace` defined in the `qhub-config.yaml`.

```yaml
certificate:
  type: existing
  secret_name: <secret-name>
```

To add the tls certificate to kubernetes run the following command with existing files.

```shell
kubectl create secret tls <secret-name> \
  --namespace=<namespace> \
  --cert=path/to/cert/file --key=path/to/key/file
```

> NOTE: the default kubernetes namespace that QHub uses is `dev`, however you can change the `namespace` key in the
> `qhub-config.yaml`.

### Wildcard certificates

Some of QHub services might require special subdomains under your certificate, Wildcard certificates allow you to secure
all subdomains of a domain with a single certificate. Defining a wildcard certificate decreases the amount of CN names
you would need to define under the certificate configuration and reduces the chance of generating a wrong subdomain.

> NOTE: It's not possible to request a double wildcard certificate for a domain (for example *.*.local.com). As a
> default behavior of [Traefik](https://doc.traefik.io/traefik/https/tls/#default-certificate), if the Domain Name
> System (DNS) and Common Name (CN) name doesn't match, Traefik generates and uses a self-signed certificate. This may
> lead to some unexpected [TLS](https://www.internetsociety.org/deploy360/tls/basics) issues, so as alternative to
> including each specific domain under the certificate CN list, you may also define a wildcard certificate.

## Security

This section walks through security and user authentication as it relates to QHub deployments. There are a few different
ways to handle user authentication:

- Auth0
- GitHub
- Password
- Custom OAuth

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
```

In previous QHub versions (prior to `v0.4.0`), users and groups were added directly into the `qhub-config.yaml`.
Starting with `v0.4.0`, user and group management is handled by [Keycloak as described below](#keycloak).

### Omitting sensitive values

If you wish to avoid storing secrets etc. directly in the config yaml file you can instead set the values in environment
variables. This substitution is triggered by setting config values to "QHUB_SECRET\_" followed by the environment
variable name. For example, you could set the environment variables "github_client_id" and "github_client_key" and write
the following in your config file:

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: QHUB_SECRET_github_client_id
      client_secret: QHUB_SECRET_github_client_key
```

### Authentication

`security.authentication` is for configuring the OAuth and GitHub Provider, password based authentication, or custom
authentication.

#### Auth0 based authentication

[Auth0](https://auth0.com/#!) can be used for authentication. While it is not free, there is a reasonable free tier that
allows deployment of QHub clusters using many different social providers, passwordless, and email based authentication
methods.

QHub has command line options for `qhub init` which automates the creation Auth0 web app via:
`--auth-provider=auth0 --auth-auto-provision`.

Otherwise here are docs on [creating an Auth0 Application](https://auth0.com/docs/applications). Make sure to select
`Regular Web Application`. Important to note is the `auth0_subdomain` field which must be only the
`<auth0_subdomain>.auth0.com`. So for the following `qhub-dev.auth0.com` the subdomain would be `qhub-dev`. Note that
all the usernames will be the email addresses of users (not usernames).

> NOTE: This is a different and distinct step from one outlined in the [Setup](setup.md#auth0) stage.

```yaml
security:
  authentication:
    type: Auth0
    config:
      client_id: ...
      client_secret: ...
      auth0_subdomain: ...
```

#### GitHub based authentication

GitHub has instructions for
[creating OAuth applications](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app).
Note that QHub usernames will be their GitHub usernames.

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: ...
      client_secret: ...
```

#### Password based authentication

This is the simplest authentication method. This just defers to however Keycloak is configured. That's also true for
GitHub/Auth0 cases, except that for the single-sign on providers the deployment will also configure those providers in
Keycloak to save manual configuration. But it's also possible to add GitHub, or Google etc, as an Identity Provider in
Keycloak even if you formally select `password` authentication in the `qhub-config.yaml` file.

```yaml
security:
  authentication:
    type: password
```

### Keycloak

The `security.keycloak` section allows you to specify an initial password for the `root` user (to login at
`https://myqhubsite.com/auth/admin/`) to manage your Keycloak database.

We strongly recommend changing this `initial_root_password` after your initial deployment and deleting this value from
your `qhub-config.yaml`. Any changes to this value on the `qhub-config.yaml` after the initial deployment will have no
affect.

For more information on how to do this, see the
["Change Keycloak root password"](./login.md#change-keycloak-root-password) section.

It's also possible to provide overrides to the
[Keycloak Helm deployment](https://github.com/codecentric/helm-charts/tree/master/charts/keycloak).

```
security:
  keycloak:
    initial_root_password: initpasswd
    overrides:
      image:
        repository: quansight/qhub-keycloak
```

#### User and group management

Groups and users of QHub are all defined in Keycloak. As above, access Keycloak as the `root` user, noting that the
`root` user is not actually a QHub user - you cannot access the main features of QHub such as JupyterLab with at user.
It is only for Keycloak management.

Follow this links for more detailed information on
[Keycloak user management](./login.md#add-user-using-keycloak-console) and
[Keycloak group management](./login.md#groups).

## Provider Infrastructure

Finally, the Kubernetes infrastructure deployment. Although quite similar, each provider has a slightly different
configuration.

The following configuration sets up a kubernetes deployment with autoscaling node groups. Depending on the cloud
provider there might be restrictions, which are detailed on each section.

For any of the providers (besides local), adding a node group is as easy as the following: which adds a `high-memory`
group:

```yaml
<provider>:
  node_groups:
    ...
    high-memory:
      instance: "s-2vcpu-4gb"     # name of cloud provider instance type
      min_nodes: 1
      max_nodes: 50
    ...
```

> NOTE: For each provider, details such as **instance names**, **availability zones**, and **Kubernetes versions** will
> be DIFFERENT.

> NOTE: upgrading the `general` node instance type may not be possible for your chosen provider.
> [See FAQ.](../user_guide/faq.md#i-want-to-upgrade-the-instance-size-the-general-node-group-is-this-possible)

### Providers

To take advantage of the auto-scaling and dask-distributed computing capabilities, QHub can be deployed on a handful of
the most commonly used cloud providers. QHub utilizes many of the resources these cloud providers have to offer,
however, at it's core, is the Kubernetes engine (or service). Each cloud provider has slightly different ways Kubernetes
is configured but fear not, all of this is handled by QHub.

Listed below are the cloud providers QHub currently supports.

> NOTE: Many of the cloud providers regularly update their internal Kubernetes versions so if you wish to specify a
> particular version, please check the following resources. This is *completely optional* as QHub will, by default,
> select the most recent version available for your preferred cloud provider.
> [Digital Ocean](https://docs.digitalocean.com/products/kubernetes/changelog/)
> [Google Cloud Platform](https://cloud.google.com/kubernetes-engine/docs/release-notes-stable)
> [Amazon Web Services](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
> [Microsoft Azure](https://docs.microsoft.com/en-us/azure/aks/supported-kubernetes-versions?tabs=azure-cli)

#### DigitalOcean

DigitalOcean has a restriction with autoscaling in that the minimum nodes allowed (`min_nodes` = 1) is one but is by far
the cheapest provider even accounting for spot/preemptible instances. In addition Digital Ocean doesn't have
accelerator/gpu support. Digital Ocean is a great default choice for tying out QHub. Below is the recommended setup.

> NOTE: DigitalOcean regularly updates Kubernetes versions hence, the field `kubernetes_version` will most likely have
> to be changed. [See available instance types for DigitalOcean](https://www.digitalocean.com/docs/droplets/). If you
> used `qhub init` this version will automatically be computed for you. Do not copy the version you see below.

To see available instance types refer to [Digital Ocean Instance Types](https://www.digitalocean.com/docs/droplets/).
Additionally the Digital Ocean cli `doctl` has
[support for listing droplets](https://www.digitalocean.com/docs/apis-clis/doctl/reference/compute/droplet/list/).

```yaml
digital_ocean:
  region: nyc3
  kubernetes_version: "1.21.10-do.0"
  node_groups:
    general:
      instance: "g-4vcpu-16gb"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "g-2vcpu-8gb"
      min_nodes: 1
      max_nodes: 5
    worker:
      instance: "g-2vcpu-8gb"
      min_nodes: 1
      max_nodes: 5
```

#### Google cloud provider

Google Cloud has the best support for QHub and is a great default choice for a production deployment. It allows
auto-scaling to zero within the node group. There are no major restrictions.

To see available instance types refer to [GCP docs](https://cloud.google.com/compute/docs/machine-types).

```yaml
google_cloud_platform:
  project: test-test-test
  region: us-central1
  kubernetes_version: "1.18.16-gke.502"
  node_groups:
    general:
      instance: n1-standard-4
      min_nodes: 1
      max_nodes: 1
    user:
      instance: n1-standard-2
      min_nodes: 0
      max_nodes: 5
    worker:
      instance: n1-standard-2
      min_nodes: 0
      max_nodes: 5
```

#### Amazon Web Services (AWS)

Amazon Web Services has similar support to DigitalOcean and doesn't allow auto-scaling below 1 node.

Consult [AWS instance types](https://aws.amazon.com/ec2/instance-types/) for possible options.

```yaml
amazon_web_services:
  region: us-west-2
  kubernetes_version: "1.18"
  node_groups:
    general:
      instance: "m5.xlarge"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "m5.large"
      min_nodes: 1
      max_nodes: 5
    worker:
      instance: "m5.large"
      min_nodes: 1
      max_nodes: 5
```

#### Azure

Microsoft Azure has similar settings for Kubernetes version, region, and instance names - using Azure's available values
of course.

Azure also requires a field named `storage_account_postfix` which will have been generated by `qhub init`. This allows
qhub to create a Storage Account bucket that should be globally unique.

```
azure:
  region: Central US
  kubernetes_version: 1.19.11
  node_groups:
    general:
      instance: Standard_D4_v3
      min_nodes: 1
      max_nodes: 1
    user:
      instance: Standard_D2_v2
      min_nodes: 0
      max_nodes: 5
    worker:
      instance: Standard_D2_v2
      min_nodes: 0
      max_nodes: 5
  storage_account_postfix: t65ft6q5
```

#### Local (existing) Kubernetes cluster

Originally designed for QHub deployments on a "local" minikube cluster, this feature has now expanded to allow users to
deploy QHub to any existing kubernetes cluster. The default options for a `local` deployment are still set deploy QHub
to a minikube cluster.

If you wish to deploy QHub to an existing kubernetes cluster on one of the cloud providers, please refer to a more
detailed walkthrough found in the [Deploy QHub to an Existing Kubernetes Cluster](./existing.md).

Deploying to a local existing kubernetes cluster has different options than the cloud providers. `kube_context` is an
optional key that can be used to deploy to a non-default context. The default node selectors will allow pods to be
scheduled anywhere. This can be adjusted to schedule pods on different labeled nodes. Allowing for similar functionality
to node groups in the cloud.

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

## Terraform state

Terraform manages the state of all the deployed resources via
[backends](https://www.terraform.io/language/settings/backends). Terraform requires storing the state in order to keep
track of the names, ids, and states of deployed resources. The simplest approach is storing the state on the local
filesystem but isn't recommended and isn't the default of QHub. `terraform_state` is either `remote`, `existing` or
`local` with a default value of `remote`. This decides whether to control the state of the cluster `local` via tfstate
file (not recommended), on an already `existing` terraform state store or remotely and auto creating the terraform state
store. See [terraform remote state](https://www.terraform.io/language/state/remote) docs. If you are doing anything
other than testing we highly recommend `remote` unless you know what you are doing.

The following are examples. `remote` and `local` are straightforward. For a `local` provider that deploys on an existing
kubernetes cluster the kubernetes remote backend is used.

```yaml
terraform_state:
  type: remote
```

```yaml
terraform_state:
  type: local
```

Using an existing terraform backend can be done by specifying the `backend` and arbitrary key/value pairs in the
`config`.

```yaml
terraform_state:
  type: existing
  backend: s3
  config:
    bucket: mybucket
    key: "path/to/my/key"
    region: "us-east-1"
```

## Default Images

Default images are to the default image run if not specified in a profile (described in the next section). The
`jupyterhub` key controls the jupyterhub image run. These control the docker image used to run JupyterHub, the default
JupyterLab image, and the default Dask worker image.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:v||QHUB_VERSION||"
  jupyterlab: "quansight/qhub-jupyterlab:v||QHUB_VERSION||"
  dask_worker: "quansight/qhub-dask-worker:v||QHUB_VERSION||"
```

## Storage

Control the amount of storage allocated to shared filesystem.

> NOTE 1: when the storage size is changed, for most providers it will automatically delete (!) the previous storage
> place. NOTE 2: changing the storage size on an AWS deployment after the initial deployment can be especially tricky so
> it might be worthwhile padding these storage sizes.

```yaml
storage:
  conda_store: 200Gi
  shared_filesystem: 200Gi
```

## Profiles

Profiles are used to control the JupyterLab user instances and Dask workers provided by Dask Gateway.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      access: all
      default: true
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      access: yaml
      groups:
        - admin
        - developers
      users:
        - bob
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
    - display_name: Large Instance
      description: Stable environment with 2 cpu / 4 GB ram
      access: keycloak
      kubespawner_override:
        cpu_limit: 2
        cpu_guarantee: 2
        mem_limit: 4G
        mem_guarantee: 4G
  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
```

### JupyterLab Profiles

For each `profiles.jupyterlab` is a named JupyterLab profile.

Use the `kubespawner_override` field to define behavior as per the
[KubeSpawner](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html) API.

It is possible to control which users have access to which JupyterLab profiles. Each profile has a field named `access`
which can be set to `all` (default if omitted), `yaml`, or `keycloak`.

`all` means every user will have access to the profile.

`yaml` means that access is restricted to anyone with their username in the `users` field of the profile or who belongs
to a group named in the `groups` field.

`keycloak` means that access is restricted to any user who in Keycloak has either their group(s) or user with the
attribute `jupyterlab_profiles` containing this profile name. For example, if the user is in a Keycloak group named
`developers` which has an attribute `jupyterlab_profiles` set to `Large Instance`, they will have access to the Large
Instance profile. To specify multiple profiles for one group (or user) delimit their names using `##` - for example,
`Large Instance##Another Instance`.

### Dask Profiles

Finally, we allow for configuration of the Dask workers. In general, similar to the JupyterLab instances you only need
to configuration the cores and memory.

When configuring the memory and CPUs for profiles there are some important considerations to make. Two important terms
to understand are:

- `limit`: the absolute max memory that a given pod can consume. If a process within the pod consumes more than the
  `limit` memory the linux OS will kill the process. LimIt is not used for scheduling purposes with kubernetes.
- `guarantee`: is the amount of memory the kubernetes scheduler uses to place a given pod. In general the `guarantee`
  will be less than the limit. Often times the node itself has less available memory than the node specification. See
  this [guide from digital ocean](https://docs.digitalocean.com/products/kubernetes/#allocatable-memory) which is
  generally applicable to other clouds.

For example if a node has 8 GB of ram and 2 CPUs you should guarantee/schedule roughly 75% and follow the digital ocean
guide linked above. For example 1.5 CPU guarantee and 5.5 GB guaranteed.

### Dask Scheduler

In a few instances, the Dask worker node-group might be running on quite a large instance, perhaps with 8 CPUs and 32 GB
of memory (or more). When this is the case, you might also want to increase the resource levels associated with the Dask
Scheduler.

```yaml
dask_worker:
    "Huge Worker":
      worker_cores_limit: 7
      worker_cores: 6
      worker_memory_limit: 30G
      worker_memory: 28G
      scheduler_cores_limit: 7
      scheduler_cores: 6
      scheduler_memory_limit: 30G
      scheduler_memory: 28G
```

### JupyterLab Profile Node Selectors

A common operation is to target jupyterlab profiles to specific node labels. In order to target a specific node groups
add the following. This example shows a GKE node groups with name `user-large`. Other cloud providers will have
different node labels.

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

### Specifying GPU/Accelerator Requirements

If you want to ensure that you have GPU resources use the following annotations.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      ...
      kubespawner_override:
        ...
        extra_resource_limits:
          nvidia.com/gpu: 1
        ...
```

## Themes

### Customizing JupyterHub theme

JupyterHub can be customized since QHub uses
[Quansight/qhub-jupyterhub-theme](https://github.com/quansight/qhub-jupyterhub-theme). Available theme options.

> NOTE: if you want to change the logo it must be an accessible URL to the logo.

```yaml
theme:
  jupyterhub:
    hub_title: QHub - thisisatest
    hub_subtitle: Autoscaling Compute Environment
    welcome: |
      Welcome to jupyter.github-actions.qhub.dev. It's maintained by <a href="http://quansight.com">Quansight
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

Its also possible to display the current version of qhub by using the `display_version: 'True'` in the above
`theme.jupyterhub` configuration. If no extra information is passed, the displayed version will be the same as
`qhub_version`, an overwrite can be done by passing the `version: v.a.b.c` key as well.

## Environments

```yaml
environments:
  "environment-default.yaml":
    name: default
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - ipykernel
      - ipywidgets
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas

  "environment-example-2.yaml":
    name: example-2
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - ipykernel
      - ipywidgets
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```

QHub is experimenting with a new way of distributing environments using
[conda-store](https://github.com/quansight/conda-store). Please expect this environment distribution method to change
over time.

Each environment configuration is a `environment.<filename>` mapping to a conda environment definition file. If you need
to pin a specific version, please include it in the definition. One current requirement is that each environment include
`ipykernel`, `ipywidgets`, `qhub-dask==0.2.3`. Upon changing the environment definition expect 1-10 minutes upon
deployment of the configuration for the environment to appear.

## qhub_version

All `qhub-config.yaml` files must now contain a `qhub_version` field displaying the version of QHub which it's intended
to be deployed with.

QHub will refuse to deploy if it doesn't contain the same version as that of the `qhub` command.

Typically, you can upgrade the qhub-config.yaml file itself using the
[`qhub upgrade` command](../admin_guide/upgrade.md). This will update image numbers, plus updating qhub_version to match
the installed version of `qhub`, as well as any other bespoke changes required.

## JupyterHub

JupyterHub uses the [zero to jupyterhub helm chart](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/). This chart
has many options that are not configured in the QHub default installation. You can override specific values in the
[values.yaml](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/main/jupyterhub/values.yaml).
`jupyterhub.overrides` is optional.

```yaml
jupyterhub:
  overrides:
    cull:
      users: true
```

## Terraform Overrides

The QHub configuration file provides a huge number of configuration options for customizing your QHub Infrastructure,
while these options are sufficient for an average user, but aren't exhaustive by any means. There are still a plenty of
things you might want to achieve which cannot be configured directly by the above mentioned options, hence we've
introduced a new option called terraform overrides (`terraform_overrides`), which lets you override the values of
terraform variables in specific modules/resource. This is a relatively advance feature and must be used with utmost care
and you should really know, what you're doing.

Here we describe the overrides supported via QHub config file:

### Ingress

You can configure the IP of the load balancer and add annotations for the same via `ingress`'s terraform overrides, one
such example for GCP is:

```yaml
ingress:
  terraform_overrides:
      load-balancer-annotations:
          "networking.gke.io/load-balancer-type": "Internal"
          "networking.gke.io/internal-load-balancer-subnet": "pre-existing-subnet"
      load-balancer-ip: "1.2.3.4"
```

This is quite useful for pinning the IP Address of the load balancer.

### Deployment inside Virtual Private Network

#### Azure

Using terraform overrides you can also deploy inside a virtual private network.

An example configuration for Azure is given below:

```yaml
azure:
  terraform_overrides:
      private_cluster_enabled: true
      vnet_subnet_id: '/subscriptions/<subscription_id>/resourceGroups/<resource_group>/providers/Microsoft.Network/virtualNetworks/<vnet-name>/subnets/<subnet-name>'
  region: Central US
```

#### Google Cloud

Using terraform overrides you can also deploy inside a VPC in GCP, making the Kubernetes cluster private. Here is an
example for configuring the same:

```yaml
google_cloud_platform:
  terraform_overrides:
    networking_mode: "VPC_NATIVE"
    network: "your-vpc-name"
    subnetwork: "your-vpc-subnet-name"
    private_cluster_config:
      enable_private_nodes: true
      enable_private_endpoint: true
      master_ipv4_cidr_block: "172.16.0.32/28"
    master_authorized_networks_config:
      cidr_block: null
      display_name: null
```

As the name suggests the cluster will be private, which means it would not have access to the internet either, which is
not ideal for deploying pods in the cluster, hence we need to allow internet access for the cluster, which can be
achieved by creating a NAT router by running the following two commands for your vpc network.

```
gcloud compute routers create qhub-nat-router --network your-vpc-name --region your-region

gcloud compute routers nats create nat-config --router qhub-nat-router  --nat-all-subnet-ip-ranges --auto-allocate-nat-external-ips --region your-region
```

#### Deployment Notes

Deployment inside a virtual network is slightly different from deploying inside a public network, as the name suggests,
since its a virtual private network, you need to be inside the network to able to deploy and access QHub. One way to
achieve this is by creating a Virtual Machine inside the virtual network, just select the virtual network and subnet
name under the networking settings of your cloud provider while creating the VM and then follow the usual deployment
instructions as you would deploy from your local machine.

# Full configuration example

```yaml
project_name: do-jupyterhub
provider: do
domain: "do.qhub.dev"

ci_cd:
  type: github-actions
  branch: main
  commit_render: true

certificate:
  type: self-signed

security:
  keycloak:
    initial_root_password: initpasswd
    overrides:
      image:
        repository: quansight/qhub-keycloak

  authentication:
    type: GitHub
    config:
      client_id: CLIENT_ID
      client_secret: CLIENT_SECRET

  shared_users_group: true

digital_ocean:
  region: nyc3
  kubernetes_version: "1.21.10-do.0"
  node_groups:
    general:
      instance: "g-4vcpu-16gb"
      min_nodes: 1
      max_nodes: 1
    user:
      instance: "g-2vcpu-8gb"
      min_nodes: 1
      max_nodes: 5
    worker:
      instance: "g-2vcpu-8gb"
      min_nodes: 1
      max_nodes: 5

default_images:
  jupyterhub: "quansight/qhub-jupyterhub:v||QHUB_VERSION||"
  jupyterlab: "quansight/qhub-jupyterlab:v||QHUB_VERSION||"
  dask_worker: "quansight/qhub-dask-worker:v||QHUB_VERSION||"

theme:
  jupyterhub:
    hub_title: QHub - thisisatest
    hub_subtitle: Autoscaling Compute Environment
    welcome: |
      Welcome to jupyter.github-actions.qhub.dev. It's maintained by <a href="http://quansight.com">Quansight
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
      access: yaml
      groups:
        - admin
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      default: true
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G

environments:
  "environment-default.yaml":
    name: default
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - ipykernel
      - ipywidgets
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas

  "environment-example-2.yaml":
    name: example-2
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - ipykernel
      - ipywidgets
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas
      - jinja2
      - pyyaml
```
