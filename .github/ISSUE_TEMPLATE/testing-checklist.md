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

## AWS

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
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

## Azure

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
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

## Digital Ocean

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
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

## GCP

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
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

## Local

### Validate auth setup
- [ ] password
- [ ] github
- [ ] auth0

### Validate `gitops` workflow
- [ ] GitHub-Actions
- [ ] GitLab-Ci

### Validate the following services:
- [ ] QHub init
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
