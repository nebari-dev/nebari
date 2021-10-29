# Testing and Development

QHub is complex to test. In order to make testing easier a command
`qhub develop` is available for developing locally. This command
should be the primary way that you develop and test QHub. If your
contribution requires the cloud to properly test this command will
unfortunately not help you. With this command you can easily test PRs,
specific commits, and the current state working state of the qhub
repository.

```shell
$ python -m qhub develop --help
usage: __main__.py develop [-h] [-v] [--profile PROFILE] [--kubernetes-version KUBERNETES_VERSION]
                           [--pr PR] [--rev REV] [--config CONFIG] [--domain DOMAIN]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose of logging
  --profile PROFILE     minikube profile to use for development
  --kubernetes-version KUBERNETES_VERSION
                        kubernetes version to use for development
  --pr PR               develop using a specific QHub PR
  --rev REV             develop using a specific local git rev (commit or branch name)
  --config CONFIG       path to a qhub-config.yaml to use instead of the default
  --domain DOMAIN       domain that qhub cluster will be accessible at
```

This command does a lot of work for the user to ease testing:
 - checks out the appropriate PR, commit, or working state
 - runs QHub on the checked out version of the code
 - starts up a Minikube cluster on docker
 - configures a MetalLB load balancer
 - builds all the Docker images and uploads to Minikube
 - generated a default qhub configuration (can be overridden for testing)
 - deploys QHub to the Minikube cluster

This command is expected to work for Linux and OSX please report an
issue if this does not work for you.

## Dependencies

This command does not require that you have QHub installed
locally. Instead it requires an environment where you have all of the
`install_requires` dependencies in the `setup.py` installed. However,
it might just be easiest to install qhub locally.

```shell
pip install -e .[dev]
```

Alternatively if you are using conda you may

```shell
conda env create -f environment-dev.yaml
conda activate qhub-dev
```

## Usage

At a minimum 8 GB of RAM and 2 CPU should be available for the
Minikube cluster. QHub has three primary runs:

 - `qhub develop` deploys a local development QHub which matches the
   current working state of the repository including non-committed
   changes
 - `qhub develop --pr <pr>` deploys a local development QHub of the
   latest commit in PR `<pr>`
 - `qhub develop --rev <rev>` deploys a local development QHub of the
   commit or branch matching `<rev>`
 
The `--pr` and `--rev` commands use `git worktree` allowing your
current modifications and checked out branch to be untouched within
the repository. Read up on [git
worktree](https://git-scm.com/docs/git-worktree) to learn more about
the command. Note that knowledge of this command is not needed for
testing or development. If you are deploying locally on Linux this
will likely be all the options that you need to supply.

Initial deployment of the local test cluster will take awhile (10
minutes to an hour) depending on local machine speed and Internet
connection. However successive runs of this command will run much
faster once the docker builds are cached after the first
run. Therefore it is recommended to only delete your Minikube cluster
after development and not in between changes. The `qhub develop`
command is designed to be run many times as development is
progressing.

If your deployment was successful visit the domain mentioned at the
end. This text will look like `Visit https://<domain> to access your
QHub Cluster`. Attempt to visit the domain. If this does not work you
will need to read the next section (OSX users and remote Linux
deployments are in this category). The key issue after deployment via
`qhub develop` for a local or remote Minikube cluster is accessing the
load balancer that was created via
[MetalLB](https://metallb.universe.tf/).

### Setting the Domain

One of the key problems encountered with local deployment is the
`domain` name used for QHub. You must access your cluster's load
balancer via a DNS name. By default on Linux locally the IP address
assigned to the QHub load balancer is `192.168.49.100` which we have
conveniently assigned to `github-actions.qhub.dev`. Here we will cover
several cases to hopefully tell you how to set the proper `--domain`
if the default does not work when performing `qhub develop`.

After a deployment even if your domain is not accessible you will want
to check the load balancer IP. This address will be written at the end
of the deployment. The text will look like `DNS Domain "<domain>" is
set but does not resolve to load balancer at "<load-balancer-ip>"`.

For remote Linux development you will need to port forward the load
balancer IP locally and set the domain to `--domain localhost`.

```shell
sudo ssh -L 80:<load-balancer-ip>:80 -L 443:<load-balancer-ip>:443 <remote-host-ip>
```

The QHub cluster will then be accessible via your web browser at
`https://localhost`. This will require you to run `qhub develop` again
with `qhub develop ... --domain localhost`.

### Additional Options

Effort was put into minimizing the number of options for `qhub
develop`. Here we will outline convenient options for further testing.

 - `--kubernetes-version` this option allows you to control the
   version of Kubernetes that is spun up with Minikube and allows for
   testing of QHub across Kubernetes versions.
 - `--verbose` will show the detailed logs when running
 - `--profile` behind the scenes Minikube is used to start
   Kubernetes. Minikube has a profile option which allows it to run
   multiple clusters. Use this if you want to test a cluster without
   overwriting another deployment.
 - `--config` allows you to provide a `qhub-config.yaml` to override
   the default one generated by QHub. This is useful for testing
   specific features of a development.

# Tips for Testing

## Using a development branch

To use qhub from a development branch such as `main` set the
environment variable `QHUB_GH_BRANCH` before running qhub commands:

```
export QHUB_GH_BRANCH=main
```

Then `qhub init` will create a qhub-config.yaml containing, for
example, `quansight/qhub-jupyterlab:main` which is the Docker image
built based on the Dockerfiles specified in the main branch of the
qhub repo (see below for more info on how these are specified).  There
is a GitHub workflow that will build these images and push to Docker
Hub whenever a change is made to the relevant files on GitHub.

In addition, `qhub deploy` can use QHUB_GH_BRANCH to create
GitHub/GitLab workflows which install the development branch of qhub
for their own deploy steps.

If you want to use the development version of qhub for your init and
deploy but want your resulting deployment to be based on a full
release version, do not set the QHUB_GH_BRANCH environment
variable. In that case, Docker tags and workflow `pip install qhub`
commands will be based on the qhub version specified in the
qhub/version.py file, but these tags and releases may not yet exist,
perhaps if the version has been updated to include a beta/dev
component which has not been released.  So you may need to manually
modify the qhub-config.yaml to 'downgrade' the tags to a full release
version.

## Modifying Docker Images

All QHub docker images are located in [`qhub/templates/{{
cookiecutter.repo_directory
}}/image/`](https://github.com/Quansight/qhub-cloud/tree/main/qhub/template/%7B%7B%20cookiecutter.repo_directory%20%7D%7D/image). You
can build any image locally. Additionally, on Pull Requests each
Docker-build will be tested.

```shell
docker build -f Dockerfile.<filename> .
```

### Testing the JupyterLab Docker Image

Often times you would like to modify the jupyterlab default docker
image and run the resulting configuration.

```shell
docker run -p 8888:8888 -it <image-sha> jupyter lab --ip=0.0.0.0
```

Then open the localhost (127.0.0.1) link that is in the terminal

```
[I 2021-04-05 17:37:17.345 ServerApp] Jupyter Server 1.5.1 is running at:
...
[I 2021-04-05 17:37:17.346 ServerApp]  or http://127.0.0.1:8888/lab?token=8dbb7ff1dcabc5fab860996b6622ac24dc71d1efc34fcbed
...
[I 2021-04-05 17:37:17.346 ServerApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
```

## Debug Kubernetes clusters

 To debug Kubernetes clusters, we advise you to use [K9s](https://k9scli.io/), a terminal-based UI that aims to
 simplify navigation, observation, and management of applications in Kubernetes.
 K9s continuously monitors Kubernetes clusters for changes and provides
 shortcut commands to interact with the observed resources becoming a
 fast way to review and resolve day-to-day issues in deployed clusters.

Installation can be done on a macOS, in Windows, and Linux and instructions
 can be found [here](https://github.com/derailed/k9s). For more details on usage,
check out the [Troubleshooting documentation](https://docs.qhub.dev/en/stable/source/admin_guide/troubleshooting.html#debug-your-kubernetes-cluster).

## Cypress Tests

Cypress automates testing within a web browser environment. It is integrated into the GitHub Actions tests.yaml workflows in this repo, and 
you can also run it locally. To do so:

```
cd tests_e2e
npm install

export CYPRESS_BASE_URL=http://127.0.0.1:8000/
export QHUB_CONFIG_PATH=/Users/dan/qhub/data-mk/qhub-config.yaml
export CYPRESS_EXAMPLE_USER_PASSWORD=<password>

npm run cypress:open
```

The Base URL can point anywhere that should be accessible - it can be the URL of a QHub cloud deployment.
The QHub Config Path should point to the associated yaml file for that site. Most importantly, the tests will inspect the yaml file to understand 
what tests are relevant. To start with, it checks security.authentication.type to determine what should be available on the login page, and 
how to test it. If the login type is 'password' then it uses the value in CYPRESS_EXAMPLE_USER_PASSWORD as the password (default username is 
`example-user` but this can be changed by setting CYPRESS_EXAMPLE_USER_NAME).

The final command above should open the Cypress UI where you can run the tests manually and see the actions in the browser.

Note that tests are heavily state dependent, so any changes or use of the deployed QHub could affect the results.

# Cloud Testing

Cloud testing on aws, gcp, azure, and digital ocean can be significantly more complicated and time consuming. But it is the only way to truly test the cloud deployments, including infrastructure, of course. To test on cloud Kubernetes, just deploy qhub in the normal way on those clouds, but using the [linked pip install](./index.md) of the qhub package.

Even with the dev install of the qhub package, you may find that the deployed cluster doesn't actually reflect any development changes, e.g. to the Docker images for JupyterHub or JupyterLab. That will be because your qhub-config.yaml references fully released versions. See [Using a development branch](#using-a-development-branch) above for how to encourage the Docker images to be specified based on the latest development code.

You should always prefer the local testing when possible as it will be easier to debug, may be quicker to deploy, and is likely to be less expensive.

# Docs testing

QHub uses [Vale](https://github.com/errata-ai/vale), a syntax-aware linter to lint documentation and recommend regions that needs improvement. Vale works with the [Google developer documentation style guide](https://developers.google.com/style), with specific configurations that are specific to Quansight. To test the documentation on the local machine, follow these steps:

- [Install Vale command-line tool](https://docs.errata.ai/vale/install).
- Run Vale on the entire documentation source or a specific documentation piece.
  ```sh
  # Run Vale on the entire documentation source
  $ vale docs/

  # Run Vale on a specific file
  $ vale README.md
  ```
- Utilize the errors, warnings and the suggestions to make appropriate changes to the documentation.
- In case of false positives, make appropriate changes to the Vale configurations hosted in the `tests/vale/styles` directory.

Vale runs on the GitHub Actions CI to automatically validate the documentation language. By default, Vale only checks the modified documentation to ensure that Vale doesn't generate a lot of noise over the Pull Requests.
