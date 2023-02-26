<p align="center">
<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup.svg">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg">
  <img alt="Nebari logo mark - text will be black in light color mode and white in dark color mode." src="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg" width="50%"/>
</picture>
</p>

<h1 align="center"> Your open source data science platform. Built for scale, designed for collaboration. </h1>

---

| Information | Links |
| :---------- | :-----|
|   Project   | [![License](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Nebari documentation](https://img.shields.io/badge/%F0%9F%93%96%20Read-the%20docs-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://www.nebari.dev/docs/welcome) [![PyPI](https://img.shields.io/pypi/v/nebari)](https://badge.fury.io/py/nebari) [![conda version](https://img.shields.io/conda/vn/conda-forge/nebari)]((https://anaconda.org/conda-forge/nebari))  |
|  Community  | [![GH discussions](https://img.shields.io/badge/%F0%9F%92%AC%20-Participate%20in%20discussions-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/discussions) [![Open an issue](https://img.shields.io/badge/%F0%9F%93%9D%20Open-an%20issue-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/issues/new/choose) [![Community guidelines](https://img.shields.io/badge/🤝%20Community-guidelines-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://www.nebari.dev/docs/community/) |
|     CI      | [![Kubernetes Tests](https://github.com/nebari-dev/nebari/actions/workflows/kubernetes_test.yaml/badge.svg)](https://github.com/nebari-dev/nebari/actions/workflows/kubernetes_test.yaml) [![Tests](https://github.com/nebari-dev/nebari/actions/workflows/test.yaml/badge.svg)](https://github.com/nebari-dev/nebari/actions/workflows/test.yaml) |

## Table of contents

- [Table of contents](#table-of-contents)
- [QHub HPC](#qhub-hpc)
- [Nebari](#nebari)
  - [Cloud Providers ☁️](#cloud-providers-️)
- [Installation 💻](#installation-)
  - [Pre-requisites](#pre-requisites)
  - [Install Nebari](#install-nebari)
- [Usage 🚀](#usage-)
- [Contributing to Nebari 👩🏻‍💻](#contributing-to-nebari-)
  - [Installing the Development version of Nebari ⚙️](#installing-the-development-version-of-nebari-️)
  - [Questions? 🤔](#questions-)
- [Code of Conduct 📖](#code-of-conduct-)
- [Ongoing Support](#ongoing-support)
- [License](#license)

> **⚠️ Warning ⚠️**
> The project has recently been renamed from QHub to Nebari. If your deployment is still managed by `qhub`, performing an in place upgrade will **IRREVOCABLY BREAK** your deployment.
> This will cause you to lose any data stored on the platform, including but not limited to, NFS (file system) data,
> `conda-store` environments, Keycloak users and groups, etc.
> Make sure to [back up your data before attempting an upgrade](https://www.nebari.dev/docs/how-tos/manual-backup).

Automated data science platform. From [JupyterHub](https://jupyter.org/hub "Multi-user version of the Notebook") to Cloud environments with
[Dask Gateway](https://docs.dask.org/ "Parallel computing in Python").

Nebari is an open source data platform that enables users to build and maintain cost-effective and scalable compute platforms
on [HPC](#nebari-hpc) or [Kubernetes](#nebari) with minimal DevOps overhead.

**This repository details the [Nebari](https://nebari.dev/ "Official Nebari docs") (Kubernetes) version.**

Not sure what to choose? Check out our [Setup Initialization](docs/source/installation/setup.md) page.

## QHub HPC

The HPC version of Nebari is based on [OpenHPC](https://openhpc.community/).

> NOTE: The tool is currently under development. Curious? Check out the [Nebari HPC](https://github.com/Quansight/qhub-hpc) repository.

## Nebari

The Kubernetes version of Nebari uses [Terraform](https://www.terraform.io/), [Helm](https://helm.sh/), and
[GitHub Actions](https://docs.github.com/en/free-pro-team@latest/actions).

- Terraform handles the build, change, and versioning of the infrastructure.
- Helm helps to define, install, and manage [Kubernetes](https://kubernetes.io/ "Automated container deployment, scaling, and management") resources.
- GitHub Actions is used to automatically create commits when the configuration file (`nebari-config.yaml`) is rendered,
  as well as to kick off the deployment action.

Nebari aims to abstract all these complexities for its users.
Hence, it is not necessary to know any of the technologies mentioned above to have your project successfully deployed.

> TLDR: If you know GitHub and feel comfortable generating and using API keys, you should have all it takes to deploy and maintain your system without the need for a dedicated
> DevOps team. No need to learn Kubernetes, Terraform, or Helm.

### Cloud Providers ☁️

Nebari offers out-of-the-box support for the major public cloud providers: [Digital Ocean](https://www.digitalocean.com/),
Amazon [AWS](https://aws.amazon.com/), [GCP](https://cloud.google.com/ "Google Cloud Provider"), and Microsoft [Azure](https://azure.microsoft.com/en-us/).
![High-level illustration of Nebari architecture](https://raw.githubusercontent.com/nebari-dev/nebari-docs/main/docs/static/img/welcome/nebari_overview_sequence.png)

## Installation 💻

### Pre-requisites

- Operating System: Currently, Nebari supports development on macOS and Linux operating systems. Windows is NOT supported.
  However, we would welcome contributions that add and improve support for Windows.
- You need Python >= 3.7 on your local machine or virtual environment to work on Nebari.
- Adopting virtual environments ([`conda`](https://docs.conda.io/en/latest/), [`pipenv`](https://github.com/pypa/pipenv) or
  [`venv`](https://docs.python.org/3/library/venv.html)) is also encouraged.

### Install Nebari

To install Nebari type the following commands in your command line:

- Install using `conda`:

  ```bash
  conda install -c conda-forge nebari

  # if you prefer using mamba
  mamba install -c conda-forge nebari
  ```

- Install using `pip`:

  ```bash
  pip install nebari
  ```

Once finished, you can check Nebari's version (and additional CLI arguments) by typing:

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

## Usage 🚀

Nebari requires setting multiple environment variables to automate the deployments fully.
For details on obtaining those variables, check the [Nebari Get started documentation][docs-get-started].

Once all the necessary credentials are gathered and set as [UNIX environment variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/), Nebari can be
deployed in minutes.

For detailed step-by-step instructions on how to deploy Nebari, check the [Nebari documentation][docs-deploy].

## Contributing to Nebari 👩🏻‍💻

Thinking about contributing? Check out our [Contribution Guidelines](CONTRIBUTING.md) to get started.

### Installing the Development version of Nebari ⚙️

To install the latest developer version (unstable) use:

```bash
pip install git+https://github.com/nebari-dev/nebari.git
```

### Questions? 🤔

Have a look at our [Frequently Asked Questions (FAQ)][nebari-faqs] to see if your query has been answered.

Getting help:

- [GitHub Discussions][gh-discussions] is our user forum. It can be used to raise discussions about a subject,
    such as: "What is the recommended way to do _X_ with Nebari?"
- [Issues][nebari-issues] for queries, bug reporting, feature requests, documentation, etc.

> We work around the clock to make Nebari better, but sometimes your query might take a while to get a reply. We
> apologize in advance and ask you to please, be patient :pray:.

## Code of Conduct 📖

To guarantee a welcoming and friendly community, we require all community members to follow our [Code of Conduct](https://github.com/Quansight/.github/blob/master/CODE_OF_CONDUCT.md).

## Ongoing Support

The `v0.4.0` release introduced many changes that will irrevocably break your deployment if you attempt an in-place upgrade; for details, see our
[RELEASE](RELEASE.md#release-v040---march-17-2022) notes. To focus on the future direction of the project, we have decided as a team that we will provide **limited** support for older versions. Any new user is encouraged to use `v0.4.0` or greater.

If you're using an older version of Nebari and would like professional support, please get in touch with the Nebari development team.

## License

[Nebari is BSD3 licensed](LICENSE).

<!-- links -->
[nebari-issues]: https://github.com/nebari-dev/nebari/issues
[nebari-faqs]: https://www.nebari.dev/docs/faq
[gh-discussions]: https://github.com/nebari-dev/nebari/discussions
[docs-get-started]: https://www.nebari.dev/docs/category/get-started
[docs-deploy]: https://www.nebari.dev/docs/get-started/deploy
