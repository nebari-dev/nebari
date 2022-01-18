# Experimental features

> NOTE: The features listed below are experimental, proceed with caution.


## CentOS `jupyterlab` and `dask-worker` profiles

The default images used during a typical QHub deployment are running on `ubuntu`. If you need your `jupyterlab` or `dask-worker` pods to run on `centOS` instead, simply update the appropriate images in your `qhub-config.yaml`.

```
...
default_images:
  jupyterhub: quansight/qhub-jupyterhub:main
  jupyterlab: quansight/qhub-jupyterlab-centos:main     <--- here
  dask_worker: quansight/qhub-dask-worker-centos:main   <--- here
  dask_gateway: quansight/qhub-dask-gateway:main
  conda_store: quansight/conda-store-server:v0.3.3
...
profiles:
  jupyterlab:
  - display_name: Small Instance
    description: Stable environment with 1 cpu / 4 GB ram
    default: true
    kubespawner_override:
      cpu_limit: 0.25
      cpu_guarantee: 0.25
      mem_limit: 2G
      mem_guarantee: 2G
      image: quansight/qhub-jupyterlab-centos:main      <--- here
  dask_worker:
    Small Worker:
      worker_cores_limit: 0.5
      worker_cores: 0.5
      worker_memory_limit: 2G
      worker_memory: 2G
      worker_threads: 1
      image: quansight/qhub-dask-worker-centos:main     <--- here
```

Then to get these changes to take hold, simply redeploy QHub.
