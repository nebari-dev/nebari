<div align="center">
 <img alt="Nebari logo on white background" src="./docs/source/images/nebari_logo.png" width="300" />
</div>
<br>

| Information | Links |
| :---------- | :-----|
|   Project   | [![License](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![QHUb documentation](https://img.shields.io/badge/%F0%9F%93%96%20Read-the%20docs-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://docs.nebari.dev/en/stable/) [![PyPI version](https://badge.fury.io/py/nebari.svg)](https://badge.fury.io/py/nebari) |
|  Community  | [![GH discussions](https://img.shields.io/badge/%F0%9F%92%AC%20-Participate%20in%20discussions-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/discussions) [![Open an issue](https://img.shields.io/badge/%F0%9F%93%9D%20Open-an%20issue-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/issues/new/choose) |
|     CI      | [![Kubernetes Tests](https://github.com/nebari-dev/nebari/actions/workflows/kubernetes_test.yaml/badge.svg)](https://github.com/nebari-dev/nebari/actions/workflows/kubernetes_test.yaml) [![Tests](https://github.com/nebari-dev/nebari/actions/workflows/test.yaml/badge.svg)](https://github.com/nebari-dev/nebari/actions/workflows/test.yaml) |

## Table of contents

- [Table of contents](#table-of-contents)
- [QHub HPC](#qhub-hpc)
- [Nebari](#nebari)
  - [:cloud: Cloud Providers](#cloud-cloud-providers)
- [:computer: Installation](#computer-installation)
  - [Pre-requisites](#pre-requisites)
  - [Install Nebari](#install-nebari)
- [:label: Usage](#label-usage)
- [:question: Questions?](#question-questions)
- [:book: Code of Conduct](#book-code-of-conduct)
- [:gear: Installing the Development version of Nebari](#gear-installing-the-development-version-of-nebari)
- [:raised_hands: Contributions](#raised_hands-contributions)
- [Ongoing Support](#ongoing-support)
- [License](#license)

Automated data science platform. From [JupyterHub](https://jupyter.org/hub "Multi-user version of the Notebook") to Cloud environments with
[Dask Gateway](https://docs.dask.org/ "Parallel computing in Python").

Nebari is an open source tool that enables users to build and maintain cost-effective and scalable compute/data science platforms on [HPC](#nebari-hpc) or on [Kubernetes](#nebari) with
minimal DevOps experience.

**This repository details the [Nebari](https://nebari.dev/ "Official Nebari docs") (Kubernetes) version.**

Not sure what to choose? Check out our [Setup Initialization](docs/source/installation/setup.md) page.

## QHub HPC

Version of Nebari based on OpenHPC.

> NOTE: The tool is currently under development. Curious? Check out the [Nebari HPC](https://github.com/Quansight/qhub-hpc) repository.

## Nebari

The Kubernetes version of Nebari is built using [Terraform](https://www.terraform.io/), [Helm](https://helm.sh/), and
[GitHub Actions](https://docs.github.com/en/free-pro-team@latest/actions). Terraform handles the build, change, and versioning of the infrastructure. Helm helps to define, install,
and manage [Kubernetes](https://kubernetes.io/ "Automated container deployment, scaling, and management"). GitHub Actions is used to automatically create commits when the
configuration file (`nebari-config.yaml`) is rendered, as well as to kick off the deployment action.

Nebari aims to abstract all these complexities for its users. Hence, it is not necessary to know any of the above mentioned technologies to have your project successfully deployed.

> TLDR: If you know GitHub and feel comfortable generating and using API keys, you should have all it takes to deploy and maintain your system without the need for a dedicated
> DevOps team. No need to learn Kubernetes, Terraform, or Helm.

### :cloud: Cloud Providers

Nebari offers out-of-the-box support for [Digital Ocean](https://www.digitalocean.com/), Amazon [AWS](https://aws.amazon.com/),
[GCP](https://cloud.google.com/ "Google Cloud Provider"), and Microsoft [Azure](https://azure.microsoft.com/en-us/).

![High-level illustration of Nebari architecture](docs/source/images/nebari-cloud_architecture.png)

For more details, check out the release [blog post](https://www.quansight.com/post/announcing-nebari).

## :computer: Installation

### Pre-requisites

- Nebari is supported by macOS and Linux operating systems (Windows is **NOT** currently supported).
- Compatible with Python 3.7+. New to Python? We recommend using [Anaconda](https://www.anaconda.com/products/individual).
- Adoption of virtual environments ([`conda`](https://docs.conda.io/en/latest/), [`pipenv`](https://github.com/pypa/pipenv) or
  [`venv`](https://docs.python.org/3/library/venv.html)) is also encouraged.

### Install Nebari

To install Nebari type the following commands in your command line:

- Install using `conda`:

  ```bash
  conda install -c conda-forge nebari
  ```

- Install using `pip`:

  ```bash
  pip install nebari
  ```

Once finished, you can check Nebari's version (and additional CLI args) by typing:

```bash
nebari --help
```

If successful, the CLI output will be similar to the following:

```bash
usage: nebari [-h] [-v] {deploy,destroy,render,init,validate} ...

Nebari command line

positional arguments:
  {deploy,destroy,render,init,validate}
                        Nebari

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Nebari version
```

## :label: Usage

Nebari requires the setting of environment variables to automate the deployments fully. For details on how to obtain those variables, check the
[installation guide](docs/source/installation/installation.md) in the docs.

Once all the necessary credentials are gathered and set as [UNIX environment variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/), Nebari can be
deployed in under 20 minutes using:

```bash
nebari init   ... # generates initial config file and optionally automates deployment steps
nebari deploy ... # creates and configures the cloud infrastructure
```

## :question: Questions?

Have a look at our [FAQ](docs/source/user_guide/faq.md) to see if your query has been answered.

We separate the queries for Nebari into:

- [GitHub Discussions](https://github.com/nebari-dev/nebari/discussions) used to raise discussions about a subject, such as: "What is the recommended way to do X with Nebari?"

- [Issues](https://github.com/nebari-dev/nebari/issues/new/choose) for queries, bug reporting, feature requests,documentation, etc.

> We work around the clock to make Nebari better, but sometimes your query might take a while to get a reply. We apologise in advance and ask you to please, be patient :pray:.

## :book: Code of Conduct

To guarantee a welcoming and friendly community, we require contributors to follow our [Code of Conduct](https://github.com/nebari-dev/.github/blob/master/CODE_OF_CONDUCT.md).

## :gear: Installing the Development version of Nebari

To install the latest developer version (unstable) use:

```bash
pip install git+https://github.com/nebari-dev/nebari.git@dev
```

## :raised_hands: Contributions

Thinking about contributing? Check out our [Contribution Guidelines](https://github.com/nebari-dev/nebari/blob/main/CONTRIBUTING.md).

## Ongoing Support

The `v0.4.0` release introduced many changes that will irrevocably break your deployment if you attempt an inplace upgrade; for details see our
[RELEASE](RELEASE.md#release-v040---march-17-2022) notes. In order to focus on the future direction of the project, we have decided as a team that we will provide **limited** support for older versions. Any new user is encouraged to use `v0.4.0` or greater.

If you're using an older version of Nebari and would like professional support, please reach out to Quansight.

## License

[Nebari is BSD3 licensed](LICENSE).
