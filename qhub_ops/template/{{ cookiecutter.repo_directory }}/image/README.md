# Pinning

It is extremely important to pin specific packages:
 - dask
 - dask-gateway

# Building Dockerfile

```shell
docker build -f Dockerfile.jupyterlab -t qhub-jupyterlab:latest .
```

```shell
docker build -f Dockerfile.dask-gateway -t qhub-dask-gateway:latest .
```

```shell
docker build -f Dockerfile.dask-worker -t qhub-dask-worker:latest .
```
