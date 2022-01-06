# Release Process for QHub

## Pre-release Checklist

Currently Qhub isn't fully automated. This makes it especially
important to manually check the features. This is a minimal set of
features that are guaranteed with each release.

Validate successful `qhub deploy` and `qhub destroy` of QHub on all
providers.

 - [ ] Azure
 - [ ] Amazon Web Services
 - [ ] Digital Ocean
 - [ ] Google Cloud Platform
 - [ ] Existing Kubernetes Cluster

Check services of Qhub on each.
 - [ ] Login and launch jupyterlab notebook and able to run basic python calculations
 - [ ] Launch dask-gateway
    - able to scale to 2 workers
    - run basic dask calculation
    - view dask gateway dashboard
 - [ ] Conda-store environments are created and available in jupyterlab notebook as kernels (dask, dashboard)
 - [ ] Create basic panel dashboard

## Release

In order to create a release:

1. Make sure the `RELEASE.md` is up to date with change, bug fixes,
   and breaking changes and move all the `Upcoming Release` into a new
   section titled `Release <version> - <month>/<day>/<year>`

2. Update file `qhub/version.py` to be `__version__ = "<version>"`

3. Commit these changes to `main` branch

4. Finally [create a Release on QHub](https://github.com/Quansight/qhub/releases/new). The tag should be `v<version>` off of the branch `main`. Use the `RELEASE.md` to get the title `Release <version> - <month>/<day>/<year>` and set the text description to the `RELEASE.md` for the given version. Click `Publish Release`.

If this worked a new version will be [uploaded to pypi for QHub](https://pypi.org/project/qhub/)

This should also trigger the all appropriate Docker images to be built, tagged, and pushed up to DockerHub.
