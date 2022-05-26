# Tips for Testing

## Using a development branch

To use qhub from a development branch such as `main` set the environment variable `QHUB_GH_BRANCH` before running qhub commands:

```
export QHUB_GH_BRANCH=main
```

Then `qhub init` will create a qhub-config.yaml containing, for example, `quansight/qhub-jupyterlab:main` which is the Docker image built based on the Dockerfiles specified in the
main branch of the QHub repo (see below for more info on how these are specified). There is a GitHub workflow that will build these images and push to Docker Hub whenever a change
is made to the relevant files on GitHub.

In addition, `qhub deploy` can use QHUB_GH_BRANCH to create GitHub/GitLab workflows which install the development branch of QHub for their own deploy steps.

If you want to use the development version of QHub for your init and deploy but want your resulting deployment to be based on a full release version, don't set the QHUB_GH_BRANCH
environment variable. In that case, Docker tags and workflow `pip install qhub` commands will be based on the qhub version specified in the `qhub/version.py` file, but these tags
and releases may not yet exist, perhaps if the version has been updated to include a beta/dev component which has not been released. So you may need to manually modify the
qhub-config.yaml to 'downgrade' the tags to a full release version.

### Kubernetes Version Check for Cloud Providers

When `qhub init <cloud provider>` is called, it checks that the `--kubernetes-version` provided is supported by the preferred cloud provider. This flag is optional and if not
provided, the `kubernetes_version` is set to the most recent kubernetes version available. This is achieved by using the cloud provider's SDK which thus requires their appropriate
credentials to be set. To get around this, simply set the `QHUB_K8S_VERSION` environment variable like so:

```
export QHUB_K8S_VERSION=1.20
```

## Modifying Docker Images

All QHub docker images are located in [`qhub/template/image`](https://github.com/Quansight/qhub/tree/main/qhub/template/image). You can build any image locally. Additionally, on
Pull Requests each Docker-build will be tested.

```shell
docker build -f Dockerfile.<filename> .
```

### Testing the JupyterLab Docker Image

Often times you would like to modify the JupyterLab default docker image and run the resulting configuration.

```shell
docker run -p 8888:8888 -it <image-sha> jupyter lab --ip=0.0.0.0
```

Then open the localhost (127.0.0.1) link that's in the terminal

```shell
[I 2021-04-05 17:37:17.345 ServerApp] Jupyter Server 1.5.1 is running at:
...
[I 2021-04-05 17:37:17.346 ServerApp]  or http://127.0.0.1:8888/lab?token=8dbb7ff1dcabc5fab860996b6622ac24dc71d1efc34fcbed
...
[I 2021-04-05 17:37:17.346 ServerApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
```

## Linting Dockerfiles

To lint Dockerfiles, developers use a tool called [Hadolint](https://github.com/hadolint/hadolint). Hadolint is a Dockerfile linter that allows to discover issues with the
Dockerfiles and recommends [best practices to be followed](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/). QHub CI automates Hadolint code reviews on
every commit and pull request, reporting code style and error prone issues.

To run Hadolint locally you can either install it locally or use a container image. Instructions are available on the
[install documentation for HadoLint](https://github.com/hadolint/hadolint#install). The `.hadolint.yml` on the root directory defines the ignored rules. To run Hadolint on
Dockerfiles run:

```shell
hadolint ./qhub/template/\{\{\ cookiecutter.repo_directory\ \}\}/image/Dockerfile.conda-store
hadolint ./qhub/template/\{\{\ cookiecutter.repo_directory\ \}\}/image/Dockerfile.dask-gateway
hadolint ./qhub/template/\{\{\ cookiecutter.repo_directory\ \}\}/image/Dockerfile.dask-worker
hadolint ./qhub/template/\{\{\ cookiecutter.repo_directory\ \}\}/image/Dockerfile.jupyterhub
hadolint ./qhub/template/\{\{\ cookiecutter.repo_directory\ \}\}/image/Dockerfile.jupyterlab
```

Hadolint will report `error`, `warning`, `info` and `style` while linting Dockerfiles. In case of an error, the CI fails.

## Debug Kubernetes clusters

To debug Kubernetes clusters, checkout [`k9s`](https://k9scli.io/), a terminal-based UI that aims to simplify navigation, observation, and management of applications in Kubernetes.
`k9s` continuously monitors Kubernetes clusters for changes and provides shortcut commands to interact with the observed resources becoming a fast way to review and resolve
day-to-day issues in deployed clusters.

Installation can be done on a macOS, in Windows, and Linux and instructions are located [here](https://github.com/derailed/k9s). For more details on usage, review the
[Troubleshooting documentation](https://docs.qhub.dev/en/stable/source/admin_guide/troubleshooting.html#debug-your-kubernetes-cluster).

## Cypress Tests

Cypress automates testing within a web browser environment. It's integrated into the GitHub Actions tests.yaml workflows in this repo, and you can also run it locally. To do so:

```shell
cd tests_e2e
npm install

export CYPRESS_BASE_URL=http://127.0.0.1:8000/
export QHUB_CONFIG_PATH=/Users/dan/qhub/data-mk/qhub-config.yaml
export CYPRESS_EXAMPLE_USER_PASSWORD=<password>

npm run cypress:open
```

The Base URL can point anywhere that should be accessible - it can be the URL of a QHub cloud deployment. The QHub Config Path should point to the associated yaml file for that
site. Most importantly, the tests will inspect the yaml file to understand what tests are relevant. To start with, it checks security.authentication.type to determine what should
be available on the login page, and how to test it. If the login type is 'password' then it uses the value in `CYPRESS_EXAMPLE_USER_PASSWORD` as the password (default username is
`example-user` but this can be changed by setting `CYPRESS_EXAMPLE_USER_NAME`).

The final command, in the preceding code-snippet, opens the Cypress UI where you can run the tests manually and see the actions in the browser.

Note that tests are heavily state dependent, so any changes or use of the deployed QHub could affect the results.

## Deployment and integration tests

Deployment and Integration testing makes it easier to test various features of deployed QHub on Minikube such as Dask Gateway, external integrations, state of the kubernetes
cluster via simple Python code. You can run the integration and deployment tests via the following command:

```shell
pytest tests_deployment/ -v
```

# Cloud Testing

Cloud testing on AWS, GCP, Azure, and Digital Ocean can be significantly more complicated and time consuming. But it's the only way to truly test the cloud deployments, including
infrastructure, of course. To test on cloud Kubernetes, just deploy QHub in the normal way on those clouds, but using the [linked pip install](./index.md) of the QHub package.

Even with the dev install of the qhub package, you may find that the deployed cluster doesn't actually reflect any development changes, for example to the Docker images for
JupyterHub or JupyterLab. That will be because your qhub-config.yaml references fully released versions. See [Using a development branch](#using-a-development-branch) above for how
to encourage the Docker images to be specified based on the latest development code.

You should always prefer the local testing when possible as it will be easier to debug, may be quicker to deploy, and is likely to be less expensive.
