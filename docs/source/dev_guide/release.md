# Release Process for QHub

## Pre-release Checklist

Although we do rely on end-to-end integration tests that run (in a private repo) on a weekly basis. This process is currently not fully integrated into the release process.

Cloud providers to validate:
 - [ ] `azure` - Azure
 - [ ] `aws` - Amazon Web Services
 - [ ] `do` - Digital Ocean
 - [ ] `gcp` - Google Cloud Platform
 - [ ] `local` - Existing Kubernetes Cluster / Minikube

Authentication providers to validate:
- [ ] password
- [ ] GitHub
- [ ] Auth0

CI/CD providers to validate:
- [ ] GitHub-Actions
- [ ] GitLab-CI

Although some of the tasks listed below are tested during the end-to-end integration tests, many others still need to be tested manually.

Validate the following services:
- [ ] Initialize `qhub-config.yaml`
- [ ] QHub deploy
- [ ] Commit to repo and use CI/CD to deploy
- [ ] Log into Keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
- [ ] Launch conda-store and validate environments are available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy
- [ ] Test Qhub upgrade command to assert compatibility 


## Release

After testing any release-candidates, to create an official release:

1. On the Conda-Forge [`qhub-dask-feedstock`](https://github.com/conda-forge/qhub-dask-feedstock) repo, update the `qhub-dask` version to match the version to be released.

2. On the GitHub repo homepage, select "Release" on the left-hand side and then click "Draft a new release". Add any breaking changes, features/improvements and bug fixes. Give it a title of `Release <version> - <month>/<day>/<year>`.

3. When ready, create the new tag name and select branch from which the release will be created, then click "Publish release". This will automatically upload the new release to [PyPI](https://pypi.org/project/qhub/) and also automatically
trigger the all appropriate Docker images to be built, tagged, and pushed up to DockerHub.

4. Finally, when the new release is published on PyPI, it's time to release the package on Conda-Forge. On the Conda-Forge [`qhub-feedstock`](https://github.com/conda-forge/qhub-feedstock) repo, update the `qhub` version to match the version to be released as well any other related package information that needs updating.
