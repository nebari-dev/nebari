# Release :tada:
> Contains description of QHub releases.
---
## To create a new release:

1. Increment the version number in `qhub/VERSION`
2. Ensure that the version number in `qhub/VERSION` is used in pinning QHub in the github actions 
`qhub/template/{{ cookiecutter.repo_directory }}/.github/workflows/qhub-ops.yaml`

---
## Upcoming release 0.3.0

### Feature changes and enhancements
* Full JupyterHub theming including colors now.
* JupyterHub docker image now independent from zero-to-jupyterhub.
* JupyterLab 3 now default user Docker image.
* Implemented the option to locally deploy QHub allowing for local testing.
* Removed the requirement for DNS, authorization is now password-based (no more OAuth requirements).
* Added option for password-based authentication
* CI now tests local deployment on each commit/PR.
* QHub Terraform modules are now pinned to specific git branch via
  `terraform_modules.repository` and `terraform_modules.ref`.

### Bug fixes

### Breaking changes

* Terraform version is now pinned to specific version


### Migration guide

0. Version `<version>` is in format `X.Y.Z`
1. Create release branch `release-<version>` based off `dev`
2. Ensure full functionality of QHub Cloud this involves at a minimum
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
* Revamp of README.md to make it concise and highlight QHub OnPrem.

### Breaking changes
* Removed the registry for DigitalOcean.

## Thank you for your contributions!
> [Brian Larsen](https://github.com/brl0), [Rajat Goyal](https://github.com/RajatGoyal), [Prasun Anand](https://github.com/prasunanand), and  [Rich Signell](https://github.com/rsignell-usgs) and [Josef Kellndorfer](https://github.com/jkellndorfer) for the insightful discussions.