# Frequently Asked Questions

Additional FAQ questions can be found in the [GitHub
discussions](https://github.com/Quansight/qhub/discussions/categories/q-a).

## Environments

### How are QHub conda user environments created? Who creates them?

The environment specifications are located in `qhub_config.yml` in the
deployment repo. These are served to the QHub deployment using
[conda-store](https://conda-store.readthedocs.io/). When you manage
your environments in this way you get all of the benefits of
environment versioning that QHub does under the hood, including future
features such as convenient environment rollback and environment
encapsulation in containers.

Anyone with access to the QHub deployment repo can add an environment, and there are no limits to the number of environments that can be included.

> Do be careful of the yaml indentation as it will differ from a conda `environment.yml`

### I need X package and it's not in any available user environments - what do I do?

The proper solution is to add the package to the `qhub_config.yml`
(See #1). If you don't have access to the deployment repo, you will
need to contact your QHub maintainer to get the required package. Just
to note: you *can* do a user install for pip packages in a pinch (this
is not recommended) but they will not be available to Dask workers.

### I want to use Dask. What needs to be included in my user environment?

You will need to include the QHub Dask metapackage,
e.g. `qhub-dask==||QHUB_VERSION||`. This will replace `distributed`, `dask`, ad
`dask-gateway`.

### Why can't I just create my own local conda environment or edit the existing conda environments?

The version of [conda-store](https://conda-store.readthedocs.io/) used
in QHub versions 0.3.11 and earlier is an alpha version. This version
doesn't support using local conda environments or editing pre-exising
environments directly.

> See the answer to #2 for information on how to modify environments properly. In the near future the QHub team will be adding support for user-defined environments via conda-store.

### I have a local package - how can it be installed? Will it be available to my Dask workers?

If you're using a `setuptools` package, you can install it into your
local user environment using

```shell
pip install --no-build-isolation --user -e .
```

If you're using a `flit` package, you can install with

```shell
flit install -s
```

These will not be available to the Dask workers.

### How to use .bashrc on QHub?

You can use `.bashrc` on QHub, but its important to note that only
`.bash_profile` is sourced by default so you'll need to be sure to
source the `.bashrc` inside of the `.bash_profile`. Its important to
note that if you set environment variables in this way, they WILL NOT
be available inside of notebooks.


7. How do I use environment variables on dask workers (not loaded via a package)?
This can be achieved through the UI:
    ```python
    import dask_gateway

    gateway = dask_gateway.Gateway()
    options = gateway.cluster_options()
    options
    ```
    Or programmatically:
    ```python
    env_vars = {
        "ENV_1": "VALUE_1",
        "ENV_2": "VALUE_2"
    }
    options.environment_vars = env_vars
    ```
    This functionality is available in release 0.3.12 or later.

8. I can't see the active conda env in the terminal.
    Set the `changeps1` value in the conda config:
    ```shell
    conda config --set changeps1 true
    ```

9. I want to use QHub server to compute a new pinned environment (which I'll the serve via the qhub_config.yml). I understand it's not recommended I use this environment for working.
If you need to solve a conda env on a QHub server (not recommended,
but there are valid usecases for this), you'll need to specify the
prefix. For example, `conda env create -f env_test.yml --prefix
/tmp/test-env` where test-env will be the env name.
