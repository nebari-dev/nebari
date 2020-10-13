# `qhub` - automated data science environments on cloud environments

[`qhub`][qhub] is an opinionated deployment of open source data science tools (eg. [jupyterhub], [dask], and [kubernetes]) on different cloud service providers without vendor lock-in.

## Usage

        qhub init do
        qhub init aws
        qhub init gcp
        
`qhub` requires you to choose your the cloud provider you desire and the initialization will generate the necessary configuration files for that service.


This generates a configuration file. Now modify the configuration according to your needs.
See documentation on modifying your configuration file for all of the cloud providers: [Configuration File](https://github.com/Quansight/qhub/blob/master/docs/docs/aws/configuration.md) 

The configuration file is needed to trigger the CI
actions when the configuration is changed.


```bash
qhub render -c qhub-config.yaml -o ./ --force
```


## `qhub` interfaces

The `qhub` api normalizes with the nuances of configuring interactive data science environments across multiple client providers.

`qhub` generates intial configuration files that users can extend later.

Each cloud provider has different configuration specifications and you can learn more about the [Digital Ocean], [AWS], and [GCP].


## Installing `qhub`

```bash
pip install qhub
```

`qhub` is a pure python package that can be downloaded from the pypi.

## License

QHub is BSD3 licensed

## Developer

`qhub` is an open source project and welcomes issues and pull requrests.

## Contributing

# Release

Creating a release:

1. Increment the version number in `qhub/VERSION`
2. Ensure that the version number in `qhub/VERSION` is used in pinning qhub in the github actions `qhub/template/{{ cookiecutter.repo_directory }}/.github/workflows/qhub-config.yaml`

[jupyterhub]: https://jupyter.org/hub "A multi-user version of the notebook designed for companies, classrooms and research labs"
[dask]: #
[kubernetes]: #
[qhub]: #