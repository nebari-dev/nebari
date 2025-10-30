<p align="center">
<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup.svg">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg">
  <img alt="Nebari logo mark - text will be black in light color mode and white in dark color mode." src="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg" width="50%"/>
</picture>
</p>

---

# Nebari base Docker images

| Information | Links                                                                                                                                                                                                                                                                                                                                                                |
| :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project     | [![License - BSD3 License badge](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Nebari documentation badge - nebari.dev](https://img.shields.io/badge/%F0%9F%93%96%20Read-the%20docs-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)][nebari-docs] |
| Community   | [![GH discussions badge](https://img.shields.io/badge/%F0%9F%92%AC%20-Participate%20in%20discussions-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)][nebari-discussions] [![Open a GH issue badge](https://img.shields.io/badge/%F0%9F%93%9D%20Open-an%20issue-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)][nebari-docker-issues]                     |
| CI          | ![Build Docker Images - GitHub action status badge](https://github.com/nebari-dev/nebari-docker-images/actions/workflows/build-push-docker.yaml/badge.svg)                                                                                                                                                                                                           |

- [Nebari base Docker images](#nebari-base-docker-images)
  - [Getting started ⚡️](#getting-started-️)
    - [Prerequisites 💻](#prerequisites-)
    - [Building the Docker images 🛠](#building-the-docker-images-)
    - [Pre-commit hooks 🧹](#pre-commit-hooks-)
  - [Reporting an issue 📝](#reporting-an-issue-)
  - [Contributions 🤝](#contributions-)
  - [License 📄](#license-)

This repository contains the source code for Docker (container) images used by the [Nebari platform][nebari-docs]. It also contains an automated means of building and pushing these images to public container registries through [GitHub actions][nebari-docker-actions]. Currently, these images are built and pushed to the following registries:

**GitHub Container Registry (ghcr.io)**

- [`nebari-jupyterlab`](https://github.com/orgs/nebari-dev/packages/container/package/nebari-jupyterlab)
- [`nebari-jupyterlab-gpu`](https://github.com/orgs/nebari-dev/packages/container/package/nebari-jupyterlab-gpu)
- [`nebari-jupyterhub`](https://github.com/orgs/nebari-dev/packages/container/package/nebari-jupyterhub)
- [`nebari-dask-worker`](https://github.com/orgs/nebari-dev/packages/container/package/nebari-dask-worker)
- [`nebari-dask-worker-gpu`](https://github.com/orgs/nebari-dev/packages/container/package/nebari-dask-worker-gpu)

**Quay Container Registry (quay.io)**

- [`nebari-jupyterlab`](https://quay.io/repository/nebari/nebari-jupyterlab)
- [`nebari-jupyterlab-gpu`](https://quay.io/repository/nebari/nebari-jupyterlab-gpu)
- [`nebari-jupyterhub`](https://quay.io/repository/nebari/nebari-jupyterhub)
- [`nebari-dask-worker`](https://quay.io/repository/nebari/nebari-dask-worker)
- [`nebari-dask-worker-gpu`](https://quay.io/repository/nebari/nebari-dask-worker-gpu)

## Getting started ⚡️

Whether you want to contribute to this project or whether you wish use these images, to get started, fork this repo and then clone the forked repo onto your local machine.

### Prerequisites 💻

- [`docker`](https://docs.docker.com/get-docker/), make sure to read the [Docker official documentation on how to install Docker on your machine](https://docs.docker.com/get-docker/).
- [pre-commit](https://pre-commit.com/), which can be installed with:

  ```bash
  pip install pre-commit
  # or using conda
  conda install -c conda-forge pre-commit
  ```

### Building the Docker images 🛠

From the repository's root folder, you can build these images locally by running the listed commands on your terminal.

- To build nebari-jupyterlab

  ```shell
  make jupyterlab
  ```

- To build nebari-jupyterhub

  ```shell
  make jupyterhub
  ```

- To build nebari-dask-worker

  ```shell
  make dask-worker
  ```

- To build nebari-workflow-controller

  ```shell
  make workflow-controller
  ```

- To build all of the images
  
  ```shell
  make all
  ```
- To delete built images
  
  ```shell
  make clean
  ```

> **NOTE**
> It is extremely important to pin specific packages `dask-gateway` and `distributed` as they need to run the same version for the `dask-workers` to work as expected.

### Pre-commit hooks 🧹

This repository uses the `prettier` pre-commit hook to standardize our YAML and markdown structure.
To install and run it, use these commands from the repository root:

```bash
# install the pre-commit hooks
pre-commit install

# run the pre-commit hooks
pre-commit run --all-files
```

## Reporting an issue 📝

If you encounter an issue or want to make suggestions on how we can make this project better, feel free to [open an issue on this repository's issue tracker](https://github.com/nebari-dev/nebari-docker-images/issues/new/choose).

## Contributions 🤝

Thinking about contributing to this repository or any other in the Nebari org? Check out our
[Contribution Guidelines](https://nebari.dev/community).

## License 📄

[Nebari is BSD3 licensed](LICENSE).

<!-- Links -->

[nebari-docker-repo]: https://github.com/nebari-dev/nebari-docker-images
[nebari-docker-issues]: https://github.com/nebari-dev/nebari-docker-images/issues/new/choose
[nebari-docker-actions]: https://github.com/nebari-dev/nebari-docker-images/actions
[nebari-discussions]: https://github.com/orgs/nebari-dev/discussions
[nebari-docs]: https://nebari.dev
