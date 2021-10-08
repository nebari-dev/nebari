# Upgrade

Here we suppose a user would like to upgrade to a version
`<version>`. Here we have outlined the following steps. These docs
outline two paths: upgrading qhub locally on your own terminal or via
CI.

If you are deploying QHub on your terminal locally you will need to
upgrade via pip.

```shell
pip install --upgrade qhub=<version>
```

If you are using CI you will need to modify the CI provider code to reflect the new CI version:
 - github-actions `.github/workflows/qhub-ops.yaml` change the line `pip install qhub==<version>`
 - gitlab-ci `.gitlab-ci.yml` change the line to `pip install qhub==<version>`

If you are using the default images being provided by QHub you will
want to upgrade the images being used. As of `v0.3.9` there are docker
images built for each release. If you are using your own QHub images
it may be a difficult process to upgrade the images. We strive to
minimize the number of changes to the images.

```yaml
...
default_images:
  jupyterhub: quansight/qhub-jupyterhub:v<version>
  jupyterlab: quansight/qhub-jupyterlab:v<version>
  dask_worker: quansight/qhub-dask-worker:v<version>
  dask_gateway: quansight/qhub-dask-gateway:v<version>
  conda_store: quansight/qhub-conda-store:v<version>
...
profiles:
  jupyterlab:
    - display_name: Small Instance
      ...
      kubespawner_override:
        ...
        image: quansight/qhub-jupyterlab:v<version>
    ...
  dask_worker:
    Small Worker:
      ...
      image: quansight/qhub-dask-worker:v<version>
```

We try to make QHub backwards compatible with configuration in
`qhub-config.yaml`. There is a schema [validator
pydantic](https://pydantic-docs.helpmanual.io/) for QHub which will
report any errors in the configuration file.

If you are deploying QHub on your terminal locally run:

```shell
qhub deploy --config qhub-config.yaml
```

If you are deploying via CI commit the two changes to
`qhub-config.yaml` and the CI at the same time.
