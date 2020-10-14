# `qhub` - automated data science environments on cloud environments

[![PyPI version](https://badge.fury.io/py/qhub.svg)](https://badge.fury.io/py/qhub)

[`qhub`][qhub] is an opinionated deployment of open source data science infrastructure (eg. [jupyterhub], [dask], and [kubernetes]) on different cloud service providers without vendor lock-in. [`qhub`][qhub] is easy to install and maintain.

## Usage

`qhub` is installed as a command line application in Python. It requires you to choose your the cloud provider you desire. once you've decided on a provider `qhub` will walk you through the following steps to configure your deployment:

1. initialize
2. render
3. deploy

these steps realized using the `qhub` CLI.

### initialize configurations

        qhub init do
        qhub init aws
        qhub init gcp

The `qhub init` command will generate configuration files for that service. The configutation files can be tailored to the needs of your organization. Each file specifies general project information, security, infrastructure settings, computational resource profiles and data science environments. See documentation on modifying your configuration file for all of the cloud providers: [Configuration File](https://github.com/Quansight/qhub/blob/master/docs/docs/aws/configuration.md) 

The configuration file is your user interface into deploying and scaling your data science environment. Each change triggers [Github Action] that will seamlessly update your infrastructure.

![](docs/images/brand-diagram.png "architecture diagram")

Check out the [`qhub` documentation][docs] for more detailed information.

### rendering the configuration file

_we need more information here._

```bash
qhub render -c qhub-config.yaml -o ./ --force
```

_what is this business?_

## `qhub` interfaces

The `qhub` api normalizes with the nuances of configuring interactive data science environments across multiple client providers. The python command line interfaces define an initial environment state that is modified, and its changes are propogated by continuous integration.

Each `qhub` cloud provider has different configuration specifications; more details can be found at the following links about the [Digital Ocean], [AWS], and [GCP] configurations.


## Installing `qhub`

`qhub` is a pure python package that can be downloaded from the pypi.

```bash
pip install qhub
```


## License

[QHub is BSD3 licensed](LICENSE).

## Developer

[`qhub`][qhub gh] is an open source project and welcomes issues and pull requests.

## Contributing

# Release

Creating a release:

1. Increment the version number in `qhub/VERSION`
2. Ensure that the version number in `qhub/VERSION` is used in pinning qhub in the github actions `qhub/template/{{ cookiecutter.repo_directory }}/.github/workflows/qhub-config.yaml`

[jupyterhub]: https://jupyter.org/hub "A multi-user version of the notebook designed for companies, classrooms and research labs"
[dask]: https://docs.dask.org/ "Dask is a flexible library for parallel computing in Python."
[kubernetes]: https://kubernetes.io/ "Automated container deployment, scaling, and management"
[qhub]: https://qhub.dev/ ""
[Github Action]: https://github.com/features/actions
[Digital Ocean]: https://www.digitalocean.com/ "digital ocean"
[AWS]: https://aws.amazon.com/ "amazon web services"
[GCP]: https://cloud.google.com/ "google cloud provider"
[qhub gh]: https://github.com/Quansight/qhub "qhub github page"
[docs]: https://qhub.dev/ "qhub documentation"