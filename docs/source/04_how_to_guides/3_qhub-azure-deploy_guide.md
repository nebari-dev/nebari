# QHub Deployment on Microsoft Azure


This guide walks you through the steps to create a QHub deployment on Microsoft Azure. 
**Deployments** are a set of multiple identical Pods with distinct identities. 
A deployment runs multiple replicas of an application and automatically replaces any instances that fail or become unresponsive. This ensures that one or more instances of the application are always available to serve user requests. Deployments are managed by the [Kubernetes Deployment Controller](https://kubernetes.io/docs/concepts/architecture/controller/).


To create a deployment, a configuration file **must** be specified. The file will define the deployment's structure, including the type and properties of the resources, any templates that should be used, and additional subfiles that can be executed to create the final configuration.

Have a look below at how you can configure your QHub deployment for Azure.

## Configuration

You can start the deployment process by providing the configuration details of your project. To abstract away some of the complexities of writing up your own configuration file for QHub deployment on Azure, the configuration file, `qhub-config.yaml`, written in the [YAML](https://yaml.org/about.html) syntax, is provided for you. The configuration file consists of three main sections: **General, Security, Provider Infrastructure** that you need to edit with your project and authentication details.

### 1. General

This section allows setting up the general information about your project.

```yaml
project_name: qhub-azure-deployment
provider: azure
ci_cd:
  type: github-actions
  branch: main
domain: "azure.qhub.dev"
```

* `project_name` is the name that the resources within the cloud deployment/kubernetes will be deployed with.

* `provider` specifies which cloud provider to use for the deployment. For Azure, you will write `azure`. Other options include `aws` for Amazon Web Services, `gcp` for Google Cloud Platform, and `do` for Digital Ocean.

* `ci_cd` refers to the continuous integration and continuous deployment framework to use. Currently, [github-actions](https://help.github.com/en/actions) is the supported framework. The `branch` parameter allow the user to control the main branch that is watched for PRs and commits.

* `domain` is the top level url to put qhub and future services under such a monitoring. In this example, `azure.qhub.dev` would be the domain for qhub to be exposed under.

### 2. Security

The security section of the configuration file specifies security and authentication details. You will need to provide your Azure account credentials on the appropriate lines of the configuration file as shown below.

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://azure.qhub.dev/hub/oauth_callback
```

You can choose the authentication type you would like to use. In the example above, the configuration shows authentication type as Github, but `Auth0` is also supported as seen below.

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

If the `config` is left blank (i.e.`config: {}`) the client will be auto provisioned by `auth0`.

#### 2.1 Users and Groups

The configuration file also allows you to specify `users` and `groups` that you would like to give access to your project and its deployment. This portion of the file enables you to provision unix permissions to each user. All users are assigned a `uid`, `primary_group`. This portion of the file enables you to provision UNIX permissions to each user. All users are assigned a `uid`, `primary_group`.

The `primary_group` is the group name assigned to files that are written for the user while `groups` is simply a mapping of group name to group ids. It is recommended to not change the ids assigned to groups and users after creation since it may lead to login problems. While the example below shows ids around 1000, it is recommended to start with high uid numbers, such as 10000000. `ids`, technically, supports 2 billion `ids`.

```yaml
users:
    <user_email>:
      uid: 1000
      primary_group: users
    <user_email>:
      uid: 1001
      primary_group: admin
  groups:
    users:
      gid: 1000
    admin:
      gid: 1001
```

### 3. Provider Infrastructure

This section of the configuration file refers to the [kubernetes](https://kubernetes.io/) infrastructure deployment on Azure. Kubernetes is a cloud agnostic, portable, extensible, open-source platform for managing containerized workloads and services that facilitates both declarative configuration and automation. Kubernetes runs your workload by placing containers into [Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod/) to run on [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/#:~:text=Nodes,machine%2C%20depending%20on%20the%20cluster.&text=Typically%20you%20have%20several%20nodes,a%20node%20include%20the%20kubelet). A node may be a virtual or physical machine, depending on the cluster. The following configuration sets up a kubernetes deployment with [autoscaling](https://kubernetes.io/blog/2016/07/autoscaling-in-kubernetes/) node groups.

In this section, you need to specify the region and instance types, and number of nodes that you would like to use for deployment. To see available instance types and pricing, please refer to [Azure's documentation](https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/).

```yaml
azure:
  project: PLACEHOLDER
  region: Central US
  kubernetes_version: 1.18.14
  node_groups:
    general:
      instance: Standard_D2_v2
      min_nodes: 1
      max_nodes: 1
    user:
      instance: Standard_D2_v2
      min_nodes: 0
      max_nodes: 4
    worker:
      instance: Standard_D2_v2
      min_nodes: 0
      max_nodes: 4
  storage_account_postfix: m5tzjrcg
```

The `storage_account_postfix` are eight random lowercase characters (number included) that help ensure the storage account created by QHub in Azure is unique.

### Default Images

An image is the term used to refer to a serialized copy of the state of an environment stored in a file. Default images section in the configuration file lists the images used to run the default image if it is not already specified in a *profile* (described in the next section). The `jupyterhub` key controls the jupyterhub image run.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:c36eace493739be280c71bec59b80659115db5d5"
  jupyterlab: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
  dask_worker: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
```

### Storage

This section controls the amount of storage allocated to shared filesystems.
> NOTE: When the storage size is changed, the previous storage will be deleted.

```yaml
storage:
  conda_store: 20Gi
  shared_filesystem: 10Gi
```

### Profiles

Profiles are used to control the `jupyterlab` user instances and `dask-workers` provided by Dask-Gateway.

```yaml
profiles:
  jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      users:
        - <username>
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
      image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
```

For each `profiles.jupyterlab` is a named jupyterlab profile. It closely follows the [KubeSpawner](https://jupyterhub kubespawner.readthedocs.io/en/latest/spawner.html) api. The only exception is that two keys are added `users` and `groups` which allow restriction of profiles to  a given set of groups and users. We recommend using groups to manage profile access. Finally, we allow for configuration of the [dask workers](https://distributed.dask.org/en/latest/worker.html). In general, similar to the jupyterlab instances, you only need to configure the cores and memory.

### Environments

An environment generally refers to a directory on your machine that contains a set of packages/dependencies that the program/application you want to run needs. One might think of a programming environment similar to a namespace as used in computer science, which refers to an abstract container (or environment) created to hold a logical grouping of names.

In your configuration file, you can add to the list of dependencies, as well as change the name of your environment if you would like to. You can also create multiple examples.

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

After you edit the configuration file, run `./scripts/00-guided-install.sh` to complete the QHub Azure deployment steps!
