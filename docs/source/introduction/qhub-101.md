# QHub 101

QHub is an open-source framework that allows data science team to initialize and maintain their data science stack on cloud. QHub makes use of Terraform to deploy JupyterHub, JupyterLab, Dask and Conda environments on Kubernetes clusters across all major cloud providers.

Though QHub, the deployment is managed using a single configuration file and is powered by GitHub Actions. This allows teams to build and maintain cost-effective and scalable infrastructure for compute/data science on cloud or on-premises. QHub can be used and deployed by anyone with a minimal DevOps experience.

## Features

With QHub, you can:

- Install and manage a shared compute environment on cloud using a single configuration file.
- Choose compute instance types and storage sizes flexibly as per your needs.
- Autoscale your JupyterHub installation and Dask compute clusters based on your cloud provider and instance type.
- Get remote editing access through KubeSSH with full shell access.
- Monitor your cluster health and usage using Grafana.
- Access compute environments that handles both pre-built and ad-hoc environments.
- Integrate JupyterLab extensions with your QHub environment.
- Embed a Jitsi conference with your JupyterLab for remote collaboration.

## QHub Architecture

The QHub architecture facilitates:

- Managing data science and compute environments flexibly on cloud.
- Seamless deployment with GitHub Actions using a single configuration file.
- Allow multiple teams to collaborate together with control permissions.

On a high-level, QHub makes use of Network File System (NFS) to provide storage access to Kubernetes applications. This setus up a Kubernetes Persistent Volume that allows NFS to share files directly. With the aid of Dask integration and environment management with conda-store, QHub allows users a simple deployment process.

For infrastructure provisioning, QHub makes use of Terraform to deploy Kubernetes clusters on AWS, GCP, Azure and Digital Ocean. For Kubernetes deployments, QHub uses Helm Charts to allow ease of distribution and allow us to deploy QHub on any Kubernetes cluster.

To know more about the internal nits and grits of QHub architecture, refer to the [QHub Architecture](../dev_guide/architecture) section.

## Installation and management

QHub can be easily installed using either `conda` or `pip`.

- `conda`:
    `conda install -c conda-forge qhub`
- `pip`:
    `pip install qhub`

QHub CLI would be installed automatically after installation. After installation, QHub CLI can be used to deploy and manage your environment on HPC, cloud, on-premises or even locally. To install QHub locally, follow the [testing](../dev_guide/testing) section.

For HPC deployment, follow the [QHub HPC](https://hpc.qhub.dev/en/latest/) documentation. For individual cloud deployment, follow the [installation instructions](../installation/setup). After setting up all the credentials, you can deploy QHub using:

```sh
qhub init
qhub deploy
```

After installing QHub, you can further manage your deployment. You can add new users to QHub, upgrade dependencies, manage your environment and monitor your deployment. Refer to our [managament instructions](../installation/management) for more details.

## Using QHub

After setting up QHub, you can visit the URL where QHub is running. Based on your authentication mechanism, you wil be greeted by a login page after which the user will be prompted to use a set of profile available to them. With fixed resources allocated to each user, you can start a cluster by clicking `Start` which will initiate the launch.

After the launch, you will be greeted by specific Python environments, which when clicked will start a JupyterLab notebook. To use VS Code, you can use Code Server by clicking `VS Code IDE` icon. To remotely access the clusters, we use the [jupyterhub-ssh](https://github.com/yuvipanda/jupyterhub-ssh) extension. For further usage instructions, follow the [using QHub](../user_guide/using_qhub) section.

## Community & support

QHub is supported by [Quansight](https://quansight.com) community. We maintain a [Frequently Asked Questions (FAQ) page](https://github.com/Quansight/qhub/blob/main/docs/source/user_guide/faq.md) for QHub users. For QHub queries, we ideally rely upon the following channels:

- [GitHub Discussions](https://github.com/Quansight/qhub/discussions): Raise discussions around particular subjects and specific queries around usage, maintenance and administration.

- [GitHub Issues](https://github.com/Quansight/qhub/issues/new/choose): Use Issues to report bugs, request new features, new documentation or potential refactors.

## How can I contribute?

QHub welcomes new contributors. If you are interested in contributing to QHub, please refer to the [contributing guide](../dev_guide/contribution) for more details.

We require contrbutors to strictly follow our [Code of Conduct](https://github.com/Quansight/.github/blob/master/CODE_OF_CONDUCT.md) and propose features, bug fixes and documentation changes on our [issues page](https://github.com/Quansight/qhub/issues/new/choose).
