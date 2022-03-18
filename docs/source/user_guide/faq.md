# Frequently asked questions

Additional FAQ questions are available in the
[GitHub discussions](https://github.com/Quansight/qhub/discussions/categories/q-a).

## Environments

### How are QHub conda user environments created? Who creates them?

The environment specifications are available in `qhub_config.yml` in the
deployment repo, which serves to the QHub deployment using
[conda-store](https://conda-store.readthedocs.io/). When the user manages their
environments in this way, they get all of the benefits of environment
versioning that QHub does under the hood, including future features, such as
convenient environment rollback and environment encapsulation in containers.

Anyone with access to the QHub deployment repo can add an environment, and
there are no limits to the number of included environments.

> Be careful of the YAML indentation as it differs from the conda `environment.yml`

### What to do when the user requires `X` package and it's not available in the environment?

The proper solution is to add the package to the `qhub_config.yml` (See #1). If
they don't have access to the deployment repo, the user needs to contact
their QHub maintainer to get the required package. They *can* do a user install
for pip packages if necessary (this is not recommended) but they won't be
available to Dask workers.

### What's included in the user environment if a user wants to use Dask?

The user needs to include the
[QHub Dask metapackage](https://github.com/conda-forge/qhub-dask-feedstock).
Example: `qhub-dask==||QHUB_VERSION||`. This replaces `distributed`, `dask`,
and `dask-gateway` with the correct pinned versions.

### Why can't a user just create their own local conda environment or edit the existing conda environments?

The version of [conda-store](https://conda-store.readthedocs.io/) used in QHub
versions 0.3.11 and earlier is an alpha version. It doesn't support
using local conda environments or editing pre-exising environments directly.

> See the answer to #2 for information on how to modify environments properly.
> In the near future, the support for user-defined environments via conda-store
> is going to be implemented.

### How can a user install a local package? Is it available to the user's Dask workers?

If the user is using a `setuptools` package, they can install it into their
local user environment using:

```shell
pip install --no-build-isolation --user -e .
```

If they're using a `flit` package, they can install with

```shell
flit install -s
```

These aren't available to the Dask workers.

### How to use .bashrc on QHub?

Users can use `.bashrc` on QHub, but it's important to note that by default QHub
sources `.bash_profile`. The users might need to be sure to source the
`.bashrc` inside of the `.bash_profile`. It's important to note that if they set
environment variables in this way, they aren't available inside the notebooks.

### How to use environment variables on dask workers which aren't loaded via a package?

It's achieved through the UI:

```python
import dask_gateway
gateway = dask_gateway.Gateway()
options = gateway.cluster_options()
options
```

It's achieved in the same way programmatically:

```python
env_vars = {
"ENV_1": "VALUE_1",
"ENV_2": "VALUE_2"
}
options.environment_vars = env_vars
```

This feature is available in release 0.3.12 or later.

### What if a user can't see the active conda environment in the terminal?

Set the `changeps1` value in the conda config:

```shell
conda config --set changeps1 true
```

### What if a user wants to use the QHub server to compute a new pinned environment, which the user serves via the `qhub_config.yml`?

If the user needs to solve a conda env on a QHub server, they need to specify
the prefix. For example,
`conda env create -f env_test.yml --prefix/tmp/test-env` where `test-env` is
the env name. It's not recommended, but there are valid use cases of this
operation.
