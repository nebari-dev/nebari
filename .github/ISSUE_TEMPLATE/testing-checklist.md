---
name: Testing Checklist
about: For maintainers only.
title: "Testing checklist for <version>"
labels:
  - "type: release 🏷"
assignees: ""
---

# Testing Checklist

_Use/modify this checklist to capture the platform's core services that need to be manually tested ._

## Manual testing: core services

If the integration tests for all of the cloud providers are successful, that is a good sign!
However, the following core services still need to be manually validated (until we can automate them).

At minimum, the following services will need to be tested:

- [ ] [Log into keycloak as root user](https://www.nebari.dev/docs/how-tos/configuring-keycloak/#change-keycloak-root-password)
  - [ ] [Add a user](https://www.nebari.dev/docs/how-tos/configuring-keycloak/#adding-a-nebari-user)
- [ ] [Log into conda-store and create](https://www.nebari.dev/docs/tutorials/creating-new-environments)
  - [ ] a conda environment in a shared namespace and,
  - [ ] a conda environment in your personal namespace
- [ ] [Launch dask-gateway cluster, test auto-scaler and](https://www.nebari.dev/docs/tutorials/using_dask)
  - [ ] [Validate that the dask-labextention is working](https://www.nebari.dev/docs/tutorials/using_dask/#step-4---understand-dasks-diagnostic-tools)
- [ ] [Confirm that a notebook can be submitted via Jupyter-Scheduler](https://nebari.dev/docs/tutorials/jupyter-scheduler)
- [ ] [Open VS-Code extension](https://www.nebari.dev/docs/how-tos/using-vscode)
  - [ ] [Add the Python extension](https://www.nebari.dev/docs/how-tos/using-vscode#adding-extensions)
  - [ ] [Create a `.py` file and run it](https://www.nebari.dev/docs/how-tos/using-vscode#running-python-code)
