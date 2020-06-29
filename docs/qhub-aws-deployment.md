# QHub Deployment on Amazon Web Services (AWS)

This quide walks you through the steps to create a QHub deployment on AWS. **Deployments** represent a set of multiple, identical Pods with no unique identities. A deployment runs multiple replicas of your application and automatically replaces any instances that fail or become unresponsive. In this way, deployments help ensure that one or more instances of your application are available to serve user requests. Deployments are managed by the Kubernetes Deployment controller.


A **configuration** defines the structure of your deployment, including the type and properties of the resources that are part of the deployment, any templates the configuration should use, and additional subfiles that can be executed to create your final configuration. You must specify a configuration in order to create a deployment. A configuration allows you to define a variety of resources and features that you would like to setup for your deployment. Let's have a closer look into how you can configure your QHub deployment for AWS. 

## Configuration

You can start the deployment process by providing the configuration details of your project. To abstract away some of the complexities of writing up your own configuration file for QHub deployment on AWS, the configuration file, `qhub-ops-config.yaml`, written in the [YAML](https://yaml.org/about.html) syntax, is provided for you. The configuration file consists of three main sections: **General, Security, Provider Infrastructure** that you need to edit with your project and authentication details. 


### 1. General 

This section allows setting up the general information about your project. 

```yaml
project_name: qhub-aws-deployment
provider: aws
ci_cd: github-actions
domain: "aws.qhub.dev"
```


* `project_name` is the name that the resources within the cloud deployment/kubernetes will be deployed with.

* `provider` specifies which cloud provider to use for the deployment. For AWS, you will write `aws`. Other options include `do` for Digital Ocean and `gcp` for Google Cloud Platform.

* `ci_cd` refers to the continuous integration and continuous deployment framework to use. Currently, [github-actions](https://help.github.com/en/actions) is the supported framework.

* `domain` is the top level url to put qhub and future services under such a monitoring. In this example, `aws.qhub.dev` would be the domain for qhub to be exposed under. 


### 2. Security

The security section of the configuration file is for configuring security and authentication details, relating to your QHub deployment. You will need to provide your Amazon Web Services account credentials on the appropriate lines of the configuration file as shown below. 

```yaml
security:
  authentication:
    type: GitHub
    config:
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>
      oauth_callback_url: https://jupyter.aws.qhub.dev/hub/oauth_callback
      auth0_subdomain: qhub-dev
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


#### 2.1 Users and Groups 

The configuration file also allows you to specify `users` and `groups` that you would like to give access to your project and its deployment. This portion of the file enables you to provision unix permissions to each user. All users are assigned a `uid`, `primary_group`.

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

This section of the configuration file refers to the [kubernetes](https://kubernetes.io/) infrastructure deployment on AWS. Kubernetes is a cloud agnostic, portable, extensible, open-source platform for managing containerized workloads and services that facilitates both declarative configuration and automation. Kubernetes runs your workload by placing containers into [Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod/) to run on [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/#:~:text=Nodes,machine%2C%20depending%20on%20the%20cluster.&text=Typically%20you%20have%20several%20nodes,a%20node%20include%20the%20kubelet). A node may be a virtual or physical machine, depending on the cluster. The following configuration sets up a kubernetes deployment with [autoscaling](https://kubernetes.io/blog/2016/07/autoscaling-in-kubernetes/) node groups. 

In this section, you need to specify the region and instance types, and number of nodes that you would like to use for deployment. To see available instance types and pricing, please refer to [AWS website](https://aws.amazon.com/ec2/instance-types/)

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
For AWS, as well as for the other cloud service providers, adding an additional node group is as easy as adding a node group such as `high-memory`.

```yaml
high-memory:
  instance: "s-2vcpu-4gb"
  min_nodes: 1
  max_nodes: 50
```

### Default Images

An image is the term used to refer to a serialized copy of the state of an environment stored in a file. Default images section in the configuration file lists the images used to run the default image if it is not already specified in a *profile* (described in the next section). The `jupyterhub` key controls the jupyterhub image run.

```yaml
default_images:
  jupyterhub: "quansight/qhub-jupyterhub:b89526c59a5c269c776b535b887bd110771ad601"
  jupyterlab: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
  dask_worker: "quansight/qhub-dask-worker:b89526c59a5c269c776b535b887bd110771ad601"
```

### Storage

This section allows you to control the amount of storage allocated to shared filesystems. Please note, when you change the storage size, it will delete the previous storage. 

```yaml
storage:
  conda_store: 20Gi
  shared_filesytem: 10Gi
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
        cpu_guarentee: 1
        mem_limit: 1G
        mem_guarentee: 1G
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarentee: 1.25
        mem_limit: 2G
        mem_guarentee: 2G
        image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"

  dask_worker:
    "Small Worker":
      worker_cores_limit: 1
      worker_cores: 1
      worker_memory_limit: 1G
      worker_memory: 1G
      image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
    "Medium Worker":
      worker_cores_limit: 1.5
      worker_cores: 1.25
      worker_memory_limit: 2G
      worker_memory: 2G
      image: "quansight/qhub-jupyterlab:b89526c59a5c269c776b535b887bd110771ad601"
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


After you edit the configuration file, run `./scripts/00-guided-install.sh` to complete the QHub AWS deployment steps!
