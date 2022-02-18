# Managing Conda Environments

QHub has several ways to manage environments for users. The
traditional approach available in older QHub deployments is still
available by editing the `qhub-config.yaml` `environments:` key within
the configuration file. An example would be 

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
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas
```

When the environments are updated in this file and an automated `qhub
deploy` is kicked off the environments are updated for all users. An
additional method is allowed which enables users to easily create
ad-hoc environments. Visiting `https://<qhub-domain>/conda-store/`
will take you to
[Conda-Store](https://conda-store.readthedocs.io/en/latest/) an open
source tool for managing conda environments within enterprise
environments. For now the username is anything with a password of
`password`. Soon this will be integrated with central authentication
via keycloak. The [create environment
endpoint](https://conda-store.readthedocs.io/en/latest/user_guide.html#create-create-environment)
will allow you to easily create a new environment. Additionally you
can update existing environments via [visiting the
environment](https://conda-store.readthedocs.io/en/latest/user_guide.html#environment-namespace-name-environments)
and clicking edit. 

We are working towards developing an extension within jupyterlab for
editing these environments but it is not complete at the
moment. Follow [gator](https://github.com/mamba-org/gator) for
progress on this extension.
