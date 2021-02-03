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
* Implemented the option to locally deploy QHub allowing for local testing.
* Removed requirement for DNS, authorization is now password-based (no more OAuth requirements).

### Bug fixes

### Breaking changes

### Migration guide
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

---
## Thank you for your contributions!
> [Brian Larsen](https://github.com/brl0), [Rajat Goyal](https://github.com/RajatGoyal), [Prasun Anand](https://github.com/prasunanand), and  [Rich Signell](https://github.com/rsignell-usgs) and [Josef Kellndorfer](https://github.com/jkellndorfer) for the insightful discussions.
