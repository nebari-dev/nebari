# Day-to-day Maintenance

All modifications to the infrastructure should be done with GitHub
Pull-Requests. 

## Common Modifications

### Modifying docker images: jupyterlab, jupyterhub, dask-worker

The docker images used for dask-worker and jupyterlab user
environments are pulled from a docker container registry. The images
are built based on the images specified in
[image](../image). There are four images that are currently built

 - jupyterlab :: modification of jupyterlab instances for each user
 - dask-worker :: modification of dask workers and dask scheduler 
 - dask-gateway :: image currently not used (was intended as dask-gateway)
   (dask and dask-gateway versions MUST match jupyterlab)
 - jupyterhub :: the jupyterhub server (allows for customization of hub UI)

Each docker image is customized with its respective directory
(e.g. `image/Dockerfile.jupyterlab` -> `image/jupyterlab/*`. For
jupyterlab the environment is located at
`image/jupyterlab/environment.yaml`. Thus to add a package to the
environment simply submit a pull request with the new package.

At this current point in time once a user submits a pull request to
create the given docker image and the PR is accepted with images
built, a PR must follow that adds the image to the qhub
deployment. This can be done by modifying
`infrastructure/variables.tf` and the configuration file.

## General Modifications

The infrastructure was designed with the goal in mind that each
`module` is orthogonal.
