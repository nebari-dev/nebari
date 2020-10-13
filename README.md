# `qhub` - automated data science environments on cloud environments

:badges:

[`qhub`][qhub] is an opinionated deployment of open source data science infrastrcuture (eg. [jupyterhub], [dask], and [kubernetes]) on different cloud service providers without vendor lock-in. [`qhub`][qhub] is easy to install and maintain.

## Usage

`qhub` is install as a command line application in python. it requires you to choose your the cloud provider you desire.

        qhub init do
        qhub init aws
        qhub init gcp

The `qhub init` command will generate configuration files for that service. The configuartion files can be tailored to the needs of your organization. Each file specifies general project information, security, infrastracture settings, computational resource profiles, and data science environments. See documentation on modifying your configuration file for all of the cloud providers: [Configuration File](https://github.com/Quansight/qhub/blob/master/docs/docs/aws/configuration.md) 

The configuration file is your user interface into scaling your data science environment. Each change triggers [Github Action] that will seamlessly update your infrastructure.

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
[Github Action]: #
[Digital Ocean]: # "digital ocean"
[AWS]: # "amazon web services"
[GCP]: # "google cloud provider"
[qhub gh]: https://github.com/Quansight/qhub "qhub github page"
[docs]: # "qhub documentation"