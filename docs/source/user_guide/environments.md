# Managing Conda Environments

QHub has several ways to manage environments for users. The traditional approach, available in older QHub deployments, is still available by editing the `qhub-config.yaml`
`environments:` key within the configuration file. Here's an example:

```yaml
environments:
  "environment-default.yaml":
    name: default
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - ipykernel
      - ipywidgets
      - qhub-dask==||QHUB_VERSION||
      - numpy
      - numba
      - pandas
```

When the environments are updated in this file and an automated `qhub deploy` is kicked off, the environments are updated for all users. There is also a way to easily create ad-hoc
environments without modifying the file. Visiting `https://<qhub-domain>/conda-store/` will take you to [Conda-Store](https://conda-store.readthedocs.io/en/latest/) an open source
tool for managing conda environments within enterprise environments. For now the username is anything with a password of `password`, but soon this will be integrated with central
authentication via keycloak. The [create environment endpoint](https://conda-store.readthedocs.io/en/latest/user_guide.html#create-create-environment) will allow you to easily
create a new environment. Additionally, you can update existing environments by
[visiting the environment](https://conda-store.readthedocs.io/en/latest/user_guide.html#environment-namespace-name-environments) and clicking edit.

> NOTE: Environments, even global ones, created from the `/conda-store` user interface CANNOT be used when running dashboards via the CDSDashboard interface. Only those added via
> the `qhub-config.yaml`.

In order for your new environment to be properly visible in the list of available kernels, you will need to include `ipykernel` and `ipywidgets` in your environment's dependency
list. Also, if using Dask, you will need to include [extra dependencies](./faq.md/#whats-included-in-the-user-environment-if-a-user-wants-to-use-dask) to maintain version
compatibility between the Dask client and server.

We are working towards developing an extension within JupyterLab for editing these environments, but it is not complete at the moment. Follow
[gator](https://github.com/mamba-org/gator) for progress on this extension.
