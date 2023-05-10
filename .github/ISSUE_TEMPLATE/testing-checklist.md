______________________________________________________________________

name: Testing Checklist about: For maintainers only. title: "Testing checklist for <version>" labels:

- "type: release 🏷" assignees: ""

______________________________________________________________________

# Testing Checklist

_Use/modify this checklist to capture the platform's core services that need to be manually tested ._

## Manual testing: core services

If the integration tests for all of the cloud providers are successful, that is a good sign! However, the following core
services still need to be manually validated (until we can automate them).

At minimum, the following services will need to be tested:

- \[ \]
  [Log into keycloak as root user](https://nebari-docs.netlify.app/how-tos/configuring-keycloak#change-keycloak-root-password)
  - \[ \] [Add a user](https://nebari-docs.netlify.app/how-tos/configuring-keycloak#adding-a-nebari-user)
- \[ \] [Log into conda-store and create](https://nebari-docs.netlify.app/tutorials/creating-new-environments)
  - \[ \] a conda environment in a shared namespace and,
  - \[ \] a conda environment in your personal namespace
- \[ \] [Launch dask-gateway cluster, test auto-scaler and](https://nebari-docs.netlify.app/tutorials/using_dask)
  - \[ \]
    [Validate that the dask-labextention is working](https://nebari-docs.netlify.app/tutorials/using_dask#step-5---viewing-the-dashboard-inside-of-jupyterlab)
- \[ \] [Create a basic CDS Dashboard](https://nebari-docs.netlify.app/tutorials/creating-cds-dashboard)
- \[ \] [Open VS-Code extension](https://nebari-docs.netlify.app/tutorials/using-vscode)
  - \[ \] [Add the Python extension](https://nebari-docs.netlify.app/tutorials/using-vscode#adding-extensions)
  - \[ \] [Create a `.py` file and run it](https://nebari-docs.netlify.app/tutorials/using-vscode#running-python-code)
