---
name: Testing Checklist
about: For maintainers only.
title: 'Testing checklist for <version>'
labels:
 - 'type: release 🏷'
assignees: ''

---

# Testing Checklist

*Use/modify this checklist as a more comprehensive list of core services to validate before cutting a major release.*

## Test core services

If the integration tests for all of the cloud providers are successful, that is a good sign!
However, the following core services still need to be manually validated (until we can automate them).

At minimum, the following services will need to be tested:
- [ ] Log into keycloak as root user and add a user
- [ ] Log into conda-store and create
  - [ ] a conda environment in a shared namespace and,
  - [ ] a conda environment in your personal namespace
- [ ] Launch dask-gateway cluster, test auto-scaler and
  - [ ] validate that the dask-labextention is working
- [ ] Create a basic CDS Dashboard
- [ ] Open VS-Code extension and create a python file


## AWS

<details>
  <summary>Detailed checklist of AWS deployment</summary>

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
- [ ] Validate Backward compatibility with previous version
- [ ] QHub deploy
- [ ] Log into keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
  - [ ] Test dask-labextention
- [ ] Validate conda-store environments are created and available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy

</details>


## Azure

<details>
  <summary>Detailed checklist of Azure deployment</summary>

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
- [ ] Validate Backward compatibility with previous version
- [ ] QHub deploy
- [ ] Log into keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
  - [ ] Test dask-labextention
- [ ] Validate conda-store environments are created and available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy

</details>


## Digital Ocean

<details>
  <summary>Detailed checklist of Digital Ocean deployment</summary>

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
- [ ] Validate Backward compatibility with previous version
- [ ] QHub deploy
- [ ] Log into keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
  - [ ] Test dask-labextention
- [ ] Validate conda-store environments are created and available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy

</details>


## GCP

<details>
  <summary>Detailed checklist of GCP deployment</summary>

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
- [ ] Validate Backward compatibility with previous version
- [ ] QHub deploy
- [ ] Log into keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
  - [ ] Test dask-labextention
- [ ] Validate conda-store environments are created and available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy

</details>


## Local

<details>
  <summary>Detailed checklist of local deployment</summary>

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
- [ ] Validate Backward compatibility with previous version
- [ ] QHub deploy
- [ ] Log into keycloak as root user and add user
- [ ] Add user from command line
- [ ] Launch JupyterLab session with new user
- [ ] Launch dask-cluster and test auto-scaler
- [ ] Launch dask-gateway dashboard
  - [ ] Test dask-labextention
- [ ] Validate conda-store environments are created and available
- [ ] Launch basic CDS Dashboard
- [ ] Launch Grafana (validate SSO)
- [ ] Qhub destroy

</details>
