# QHub Cloud
Automated data science platform. From [JupyterHub](https://jupyter.org/hub "Multi-user version of the Notebook") to 
Cloud environments with [Dask](https://docs.dask.org/ "Parallel computing in Python").

[![PyPI version](https://badge.fury.io/py/qhub.svg)](https://badge.fury.io/py/qhub)

QHub is an open source tool that enables users to build and maintain
cost-effective and scalable compute/data science platforms [on-premises](#qhub-on-prem) or on 
[cloud providers](#qhub-cloud) with minimal DevOps experience.

**This repository details the [QHub Cloud](https://qhub.dev/ "Official QHub docs") version.**

## QHub On-Prem
The on-premises version of QHub is based on OpenHPC. 
> NOTE: The tool is currently under development. Curious? Check out the [Qhub On-Prem](https://github.com/Quansight/qhub-onprem) repository.

## QHub Cloud
The cloud version of QHub is built using [Terraform](https://www.terraform.io/), [Helm](https://helm.sh/), and 
[GitHub Actions](https://docs.github.com/en/free-pro-team@latest/actions).
Terraform handles the build, change, and versioning of the infrastructure. Helm helps to define, install and manage 
[Kubernetes](https://kubernetes.io/ "Automated container deployment, scaling, and management") applications. And GitHub 
Actions is used to automatically create commits when the configuration file (`qhub-config.yaml`) is rendered, as well as
to kick of the deployment action.

QHub aims to abstract all these complexities for our users. Hence, it is not necessary to know any of the above mentioned 
technologies to have your project successfully deployed.

> TLDR:
> If you know GitHub and feel comfortable generating and using API keys, you should have all it takes to deploy 
> and maintain your system without the need for a dedicated DevOps team. No Kubernetes, no Terraform, no Helm.

### Cloud Providers
QHub offers out-of-the-box support for [Digital Ocean](https://www.digitalocean.com/), Amazon [AWS](https://aws.amazon.com/)
 and [GCP](https://cloud.google.com/ "Google Cloud Provider"). Support for Microsoft [Azure](https://azure.microsoft.com/en-us/)
will be added soon.


![image](docs/images/brand-diagram.png "architecture diagram")

For more details, check out the release [blog post](https://www.quansight.com/post/announcing-qhub).

## Installation
### Pre-requisites
* QHub is supported by macOS and Linux operating systems (Windows is **NOT** currently supported
* Compatible with Python 3.6+. New to Python? We recommend using [Anaconda](https://www.anaconda.com/products/individual).
* Adoption of virtual environments (`conda`, `pipenv` or `venv`) is also encouraged. 

### Install
To install QHub run:
* `conda`:
  ```bash
  conda install -c conda-forge qhub
  ```
  
* or `pip`:
    ```bash
    pip install qhub
    ```  
Once finished, you can check QHub's version (and additional CLI args) by typing:
```
qhub --help
```
If successful, the CLI output will be similar to the following:

```bash
usage: qhub [-h] [-v] {deploy,render,init,validate} ...

QHub command line

positional arguments:
  {deploy,render,init,validate}
                        QHub Ops - 0.1.21

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         QHub Ops version
```

## Usage
QHub requires the setting of environment variables to automate the deployments fully. For details on how to obtain those
variables, check the [Step-by-Step](https://qhub.dev/docs/step-by-step-walkthrough.html) guide on the docs.

Once all the necessary credentials are gathered and set as [UNIX environment variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/),
QHub can be deployed in under 20 minutes using:
```bash
qhub init   ... # generates initial config file
qhub render ... # creates the Terraform config module
qhub deploy ... # deploys the project
```

## Questions?
We separate the queries for QHub into:
* [GitHub Discussions](https://github.com/Quansight/qhub/discussions) used to raise discussions about a subject, such as:
"What is the recommended way to do X with QHub?"
* [Issues](https://github.com/Quansight/qhub/issues/new/choose) for queries, bug reporting, feature requests, 
  documentation, etc.
> We work around the clock to make QHub Cloud more excellent. Which implies that sometimes your
> query might take a while to get a reply. We apologise in advance and ask you to please, be patient.

## Developer
To install the latest developer version use:
```bash
pip install git+https://github.com/Quansight/qhub.git
```

## Contributions
Thinking about contributing? Check out our [Contribution Guidelines](https://github.com/Quansight/qhub/CONTRIBUTING.md).

## License
[QHub is BSD3 licensed](LICENSE).
