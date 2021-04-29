# Changelog

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

## Release 0.3.7 - 04/30/2021

### Breaking changes

### Feature changes and enhancements

 - setting `/bin/bash` as the default terminal

### Bug fixes

 - `jhsingle-native-proxy` added to the base jupyterlab image

## Release 0.3.6 - 04/29/2021

### Breaking changes

 - simplified bash jupyterlab image to no longer have dashboard packages panel, etc.

### Feature changes and enhancements

 - added emacs and vim as default editors in image
 - added jupyterlab-git and jupyterlab-sidecar since they now support 3.0
 - improvements with `qhub destroy` cleanly deleting resources
 - allow user to select conda environments for dashboards
 - added command line argument `--skip-terraform-state-provision` to allow for skipping terraform state provisioning in `qhub deploy` step
 - no longer render `qhub init` `qhub-config.yaml` file in alphabetical order
 - allow user to select instance sizes for dashboards

### Bug fixes

 - fixed gitlab-ci before_script and after_script
 - fixed jovyan -> qhub_user home directory path issue with dashboards

## Release 0.3.5 - 04/28/2021

### Breaking changes

### Feature changes and enhancements

 - added a `--skip-remote-state-provision` flag to allow `qhub deploy` within CI to skip the remote state creation
 - added saner defaults for instance sizes and jupyterlab/dask profiles
 - `qhub init` no longer renders `qhub-config.yaml` in alphabetical order
 - `spawn_default_options` to False to force dashboard owner to pick profile
 - adding `before_script` and `after_script` key to `ci_cd` to allow customization of CI process

### Bug fixes

## Release 0.3.4 - 04/27/2021

### Breaking changes

### Feature changes and enhancements

### Bug fixes

 - remaining issues with ci_cd branch not being fully changed

## Release 0.3.3 - 04/27/2021

### Breaking changes

### Feature changes and enhancements

### Bug fixes

 - Moved to ruamel as yaml parser to throw errors on duplicate keys
 - fixed a url link error in cds dashboards
 - Azure fixes to enable multiple deployments under one account
 - Terraform formatting issue in acme_server deployment
 - Terraform errors are caught by qhub and return error code

### Breaking changes

## Release 0.3.2 - 04/20/2021

### Bug fixes

 - prevent gitlab-ci from freezing on gitlab deployment
 - not all branches were configured via the `branch` option in `ci_cd`

## Release 0.3.1 - 04/20/2021

### Feature changes an enhancements
 - added gitlab support for CI
 - `ci_cd` field is now optional
 - AWS provider now respects the region set
 - More robust errors messages in cli around project name and namespace
 - `git init` default branch is now `main`
 - branch for CI/CD is now configurable

### Bug fixes
 - typo in `authenticator_class` for custom authentication

## Release 0.3.0 - 04/14/2021

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

## Release 0.2.3 - 02/05/2021

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
