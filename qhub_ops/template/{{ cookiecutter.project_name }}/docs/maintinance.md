# Day-to-day Maintenance

All modifications to the infrastructure should be done with GitHub
Pull-Requests. 

## Common Modifications

### Modifying dask-worker and jupyterlab user environments

The docker images used for dask-worker and jupyterlab user
environments are pulled from ECR (a docker container registry). The
images are built based on the image specified in
[image](../image). [environment.yml](../environment.yml) is the conda
environment that is used. Thus to add a package to the environment
simply submit a pull request with the new package.

At this current point in time once a user submits a pull request to
create the given docker image, a PR much follow that adds the image to
the infrastructure via `singleuser.image.*`
[infrastructure/jupyterhub.yaml](../infrastructure/jupyterhub.yaml). *TODO:*
Soon this will be automated.

## General Modifications

The infrastructure was designed with the goal in mind that each
`module` is orthogonal.
