---
id: dask-nebari-config
title: Configure Dask on Nebari
---

# Introduction

In this tutorial we will dive into the `Nebari-Dask` configuration details. Nebari config is essentially
a `yaml` file which is at the heart of all things (most of them) related to configurations.
Our main focus in this tutorial will be the `profiles` & `dask_worker` section of the config file.

### Basic infrastructure details

Before we dive deeper in configuration details, let's understand about how are the core configuration
components.

### Core components:

- Dask-gateway
- dask workers
- Dask scheduler

### How to configure dask gateway profiles?

```python
jupyterlab:
    - display_name: Small Instance
      description: Stable environment with 1 cpu / 1 GB ram
      access: all
      default: true
      kubespawner_override:
        cpu_limit: 1
        cpu_guarantee: 1
        mem_limit: 1G
        mem_guarantee: 1G
    - display_name: Medium Instance
      description: Stable environment with 1.5 cpu / 2 GB ram
      access: yaml
      groups:
        - admin
        - developers
      users:
        - bob
      kubespawner_override:
        cpu_limit: 1.5
        cpu_guarantee: 1.25
        mem_limit: 2G
        mem_guarantee: 2G
    - display_name: Large Instance
      description: Stable environment with 2 cpu / 4 GB ram
      access: keycloak
      kubespawner_override:
        cpu_limit: 2
        cpu_guarantee: 2
        mem_limit: 4G
        mem_guarantee: 4G
```