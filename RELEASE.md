# Release :tada:
> Contains description of QHub releases.
---
## To create a new release:

1. Increment the version number in `qhub/VERSION`
2. Ensure that the version number in `qhub/VERSION` is used in pinning QHub in the github actions 
`qhub/template/{{ cookiecutter.repo_directory }}/.github/workflows/qhub-ops.yaml`

---
## Upcoming Release

### Feature changes and enhancements

### Bug fixes

### Breaking changes

## Release 0.3.0

### Feature changes and enhancements

* Support for self-signed certificate/secret keys via kubernetes secrets
* [jupyterhub-ssh](https://github.com/yuvipanda/jupyterhub-ssh) (`ssh` and `sftp` integration) accessible on port `8022` and `8023` respectively
* VSCode([code-server](https://github.com/cdr/code-server)) now provided in default image and integrated with jupyterlab
* [Dask Gateway](https://gateway.dask.org/) now accessible outside of cluster
* Moving fully towards traefik as a load balancer with tight integration with dask-gateway
* Adding ability to specify node selector label for general, user, and worker
* Ability to specify `kube_context` for local deployments otherwise will use default
* Strict schema validation for `qhub-config.yaml`
* Terraform binary is auto-installed and version managed by qhub
* Deploy stage will auto render by default removing the need for render command for end users
* Support for namespaces with qhub deployments on kubernetes clusters
* Full JupyterHub theming including colors now.
* JupyterHub docker image now independent from zero-to-jupyterhub.
* JupyterLab 3 now default user Docker image.
* Implemented the option to locally deploy QHub allowing for local testing.
* Removed the requirement for DNS, authorization is now password-based (no more OAuth requirements).
* Added option for password-based authentication
* CI now tests local deployment on each commit/PR.
* QHub Terraform modules are now pinned to specific git branch via
  `terraform_modules.repository` and `terraform_modules.ref`.
* Adds support for Azure cloud provider.

### Bug fixes

### Breaking changes

* Terraform version is now pinned to specific version
* `domain` attributed in `qhub-config.yaml` is now the url for the cluster

### Migration guide

0. Version `<version>` is in format `X.Y.Z`
1. Create release branch `release-<version>` based off `main`
2. Ensure full functionality of QHub this involves at a minimum
   ensuring
  - [ ] GCP, AWS, DO, and local deployment
  - [ ] "Let's Encrypt" successfully provisioned 
  - [ ] Dask Gateway functions properly on each
  - [ ] JupyterLab functions properly on each
3. Increment the version number in `qhub/VERSION` in format `X.Y.Z`
4. Ensure that the version number in `qhub/VERSION` is used in pinning
   QHub in the github actions `qhub/template/{{
   cookiecutter.repo_directory }}/.github/workflows/qhub-ops.yaml` in
   format `X.Y.Z`
5. Create a git tag pointing to the release branch once fully tested
   and version numbers are incremented `v<version>`

---

## Release 0.2.0

### Feature changes, and enhancements

* Added conda prerequisites for GUI packages.
* Added `qhub destroy` functionality that tears down the QHub deployment.
* Changed the default repository branch from `master` to `main`.
* Added error message when Terraform parsing fails.
* Added templates for GitHub issues.

### Bug fixes

* `qhub deploy -c qhub-config.yaml` no longer prompts unsuported argument for `load_config_file`.
* Minor changes on the Step-by-Step walkthrough on the docs.
* Revamp of README.md to make it concise and highlight QHub HPC.

### Breaking changes

* Removed the registry for DigitalOcean.

## Thank you for your contributions!
> [Brian Larsen](https://github.com/brl0), [Rajat Goyal](https://github.com/RajatGoyal), [Prasun Anand](https://github.com/prasunanand), and  [Rich Signell](https://github.com/rsignell-usgs) and [Josef Kellndorfer](https://github.com/jkellndorfer) for the insightful discussions.
