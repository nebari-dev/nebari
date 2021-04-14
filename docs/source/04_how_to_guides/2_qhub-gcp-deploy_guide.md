# QHub Deployment on Google Cloud Platform (GCP)

This guide walks you through the steps to create a QHub deployment on GCP. **Deployments** represent a set of multiple, identical Pods with no unique identities. A deployment runs multiple replicas of your application and automatically replaces any instances that fail or become unresponsive. In this way, deployments help ensure that one or more instances of your application are available to serve user requests. Deployments are managed by the Kubernetes Deployment controller.

A **configuration** defines the structure of your deployment, including the type and properties of the resources that are part of the deployment, any templates the configuration should use, and additional subfiles that can be executed to create your final configuration. You must specify a configuration in order to create a deployment. A configuration allows you to define a variety of resources and features that you would like to setup for your deployment. Let's have a closer look into how you can configure your QHub deployment for GCP.

## Configuration

You can start the deployment process by providing the configuration details of your project. To abstract away some of the complexities of writing up your own configuration file for QHub deployment on GCP, the configuration file, `qhub-config.yaml`, written in the [YAML](https://yaml.org/about.html) syntax, is provided for you. The configuration file consists of three main sections: **General, Security, Provider Infrastructure** that you need to edit with your project and authentication details.

### 1. General

This section allows setting up the general information about your project.

```yaml
project_name: qhub-gcp-deployment
provider: gcp
ci_cd: github-actions
domain: "gcp.qhub.dev"
```

* `project_name` is the name that the resources within the cloud deployment/kubernetes will be deployed with.

* `provider` specifies which cloud provider to use for the deployment. For GCP, you will write `gcp`. Possible options include `do` for Digital Ocean and `aws` for Amazon Web Services.

* `ci_cd` refers to the continuous integration and continuous deployment framework to use. Currently, [github-actions](https://help.github.com/en/actions) is the supported framework.

* `domain` is the top level url to put qhub and future services under such a monitoring. In this example, `gcp.qhub.dev` would be the domain for qhub to be exposed under.

### 2. Security

The security section of the configuration file is for configuring security and authentication details, relating to your QHub deployment. You will need to provide your Google Cloud [Service Account](https://cloud.google.com/iam/docs/service-accounts) credentials on the appropriate lines of the configuration file as shown below.

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://jupyter.gcp.qhub.dev/hub/oauth_callback
      auth0_subdomain: qhub-dev
```

To configure the oauth provider used for authentication, you will fill out the `security.authentication` section. You can choose the authentication type you would like to use. In the example above, the configuration shows authentication type as Github, but `Auth0` is also supported as seen below.

```yaml
security:
  authentication:
    type: Auth0
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://jupyter.gcp.qhub.dev/hub/oauth_callback
      scope: ['openid', 'email', 'profile']
      auth0_subdomain: qhub-dev
```

The configuration file also allows you to specify `users` and `groups` that you would like to give access to your project and its deployment. This portion of the file enables you to provision unix permissions to each user. All users are assigned a `uid`, `primary_group` and optionally any number of `secondary_groups`.

The `primary_group` is the group name assigned to files that are written for the user while `groups` is simply a mapping of group name to group ids. It is recommended to not change the ids assigned to groups and users after creation since it may lead to login problems. While the example below shows ids around 100 and 1000, it is recommended to start with high uid numbers, such as 10000000. `ids`, technically, supports 2 billion `ids`.

```yaml
users:
    <username1>:
      uid: 1000
      primary_group: users
      secondary_groups:
        - admin
    <username2>:
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

### 3. Provider Infrastructure

This section of the configuration file refers to the [kubernetes](https://kubernetes.io/) infrastructure deployment on GCP. Kubernetes is a cloud agnostic, portable, extensible, open-source platform for managing containerized workloads and services that facilitates both declarative configuration and automation. Kubernetes runs your workload by placing containers into [Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod/) to run on [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/#:~:text=Nodes,machine%2C%20depending%20on%20the%20cluster.&text=Typically%20you%20have%20several%20nodes,a%20node%20include%20the%20kubelet). A node may be a virtual or physical machine, depending on the cluster. The following configuration sets up a kubernetes deployment with [autoscaling](https://kubernetes.io/blog/2016/07/autoscaling-in-kubernetes/) node groups.

Among the cloud service providers on which QHub can be deployed, GCP has the best support for QHub. This is mainly because it allows autoscaling to zero within a node group. To see available instance types, please refer to [gcp docs](https://cloud.google.com/compute/docs/machine-types).

```yaml
google_cloud_platform:
  project: <project_id>
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

To interact with Google Cloud resources and perform a QHub deployment, you must provide the identifying project information for every request. On GCP, a project is identified by its project ID and project number. GCP deployment requires the project id and service account credentials.

`GOOGLE_CREDENTIALS` must be the contents of the json credentials file with sufficient permissions to create all resources on the cluster. Detailed instructions on [creating service accounts can be found here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys). `project_id` is a short string of around 32 characters that defines your project uniquely. To get the project ID and the project number, you will need to go to your GCP Dashboard as described [here](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects) and fill in the `project_id` line in the configuration file. The service account will need `Project->Editor` permissions. In addition, you will need to enable the `Cloud Resource Manager API`. The QHub deployment will fail without the api enabled.

For GCP, as well as for the other cloud service providers, adding an additional node group is as easy as adding a node group such as `high-memory`.

```yaml
high-memory:
  instance: "s-2vcpu-4gb"
  min_nodes: 1
  max_nodes: 50
```

### Default Images

An image is the term used to refer to a serialized copy of the state of an environment stored in a file. Default images section in the configuration file lists the images used to run the default image if it is not already specified in a profile (described in the next section). The `jupyterhub` key controls the jupyterhub image run.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:c36eace493739be280c71bec59b80659115db5d5"
  jupyterlab: "quansight/qhub-jupyterlab:c36eace493739be280c71bec59b80659115db5d5"
  dask_worker: "quansight/qhub-dask-worker:c36eace493739be280c71bec59b80659115db5d5"
```

### Storage

This section allows you to control the amount of storage allocated to shared filesystems. Please note, when you change the storage size, it will delete the previous storage.

```yaml
storage:
  conda_store: 20Gi
  shared_filesystem: 10Gi
```

### Profiles

Profiles are used to control the jupyterlab user instances and dask-workers provided by dask-gateway.

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

For each `profiles.jupyterlab` is a named jupyterlab profile. It closely follows the [KubeSpawner](<https://jupyterhub> kubespawner.readthedocs.io/en/latest/spawner.html) api. The only exception is that two keys are added `users` and `groups` which allow restriction of profiles to  a given set of groups and users. We recommend using groups to manage profile access. Finally, we allow for configuration of the [dask workers](https://distributed.dask.org/en/latest/worker.html). In general, similar to the jupyterlab instances, you only need to configure the cores and memory.

### Environments

An environment generally refers to a directory on your machine that contains a set of packages/dependencies that the program/application you want to run needs. One might think of a programming environment similar to a namespace as used in computer science, which refers to an abstract container (or environment) created to hold a logical grouping of names.

In your configuration file, you can add to the list of dependencies, as well as change the name of your environment if you would like to.

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
```

After you edit the configuration file, run `./scripts/00-guided-install.sh` to complete the QHub AWS deployment steps!
