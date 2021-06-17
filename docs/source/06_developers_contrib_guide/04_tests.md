# Testing

## Using a development branch

To use qhub from a development branch such as `main` set the environment variable `QHUB_GH_BRANCH` before running qhub commands:

```
export QHUB_GH_BRANCH=main
```

Then `qhub init` will create a qhub-config.yaml containing, for example, `quansight/qhub-jupyterlab:main` which is the Docker image 
built based on the Dockerfiles specified in the main branch of the qhub repo (see below for more info on how these are specified). 
There is a GitHub workflow that will build these images and push to Docker Hub whenever a change is made to the relevant files on GitHub.

In addition, `qhub deploy` can use QHUB_GH_BRANCH to create GitHub/GitLab workflows which install the development branch of qhub 
for their own deploy steps.

If you want to use the development version of qhub for your init and deploy but want your resulting deployment to be based on a 
full release version, do not set the QHUB_GH_BRANCH environment variable. In that case, Docker tags and workflow `pip install qhub` 
commands will be based on the qhub version specified in the qhub/version.py file, but these tags and releases may not yet exist, 
perhaps if the version has been updated to include a beta/dev component which has not been released. 
So you may need to manually modify the qhub-config.yaml to 'downgrade' the tags to a full release version.

## Modifying Docker Images

All QHub docker images are located in [`qhub/templates/{{
cookiecutter.repo_directory
}}/image/`](https://github.com/Quansight/qhub-cloud/tree/main/qhub/template/%7B%7B%20cookiecutter.repo_directory%20%7D%7D/image). You
can build any image locally. Additionally, on Pull Requests each Docker-build
will be tested.

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

## Local Testing

Local testing is a great way to test the components of QHub. It is
important to highlight that while it is possible to test most of QHub
with this version, components that are Cloud provisioned such as:
VPCs, managed Kubernetes cluster and managed container registries
cannot be locally tested, due to their Cloud dependencies.

### Compatibility
Currently, **QHUb local deployment is only compatible with Linux-based Operating Systems**. The primary limitation for the
installation on macOS relates to [Docker Desktop for Mac](https://docs.docker.com/docker-for-mac/networking/#known-limitations-use-cases-and-workarounds)
being unable to route traffic to containers.
Theoretically, the installation of HyperKit Driver could solve the issue, although the proposed solution has not yet been tested.

This guide assumes that you have the QHub repository downloaded, and you are at the root of the repository.

### Dependencies
> NOTE: The following instructions apply **only to Linux OS**.

To deploy QHub locally requires the installation of the following dependencies:
+ [Minukube](https://v1-18.docs.kubernetes.io/docs/tasks/tools/install-minikube/) version 1.10.0-beta and up
+ [Docker Engine driver](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) install.

The installation of a hypervisor is **not** necessary.

> NOTE: Minikube requires `kubectl`. To install `kubectl`,
> [follow the instructions](https://v1-18.docs.kubernetes.io/docs/tasks/tools/install-kubectl/) according to your operating system.


### Initialize kubernetes cluster

Before proceeding with the initialization, make sure to add yourself to the
Docker group by executing the command `sudo usermod -aG docker <username>`.

Testing is done with Minikube.

To confirm successful installation of both Docker and Minikube,
you can run the following command to start up a local Kubernetes
cluster:

```shell
minikube start --cpus 2 --memory 4096 --driver=docker
```
The command will download a Docker image of around 500Mb in size and initialise a cluster with 2 CPUs and 4Gb
of RAM, with Docker as the chosen driver.


Once `minikube start` finishes, run the command below to check the
status of the cluster:

```bash
minikube status
```

If your cluster is running, the output from minikube status should be
similar to:

```bash
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
timeToStop: Nonexistent
```

After you have confirmed that Minikube is working, you can either continue to
use, or you can stop your cluster. To stop your cluster, run:

```bash
minikube stop
```

Next, we will install `nfs-common` drivers. This is required by the JupyterLab instances, which require NFS mount for
`PersistentVolumeClaims` (PVCs). To install it, run:

```shell
minikube ssh "sudo apt update; sudo apt install nfs-common -y"
```
For more details on PVs and PVCs, read the [JupyterHub documentation](https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/customizing/user-storage.html).

### MetalLB

[MetalLB](https://metallb.universe.tf/) is the load balancer for bare-metal Kubernetes clusters. We will need to configure
MetalLB to match the QHub configuration.

#### Configure MetalLB

Configure the `metallb` load balancer to have a start IP address of
`192.168.49.100` and an end of `192.168.49.150`. These IP addresses were not
randomly chosen. Make sure that the IP range is within the Docker interface subnet.
To determine the range of IP addresses, inspect the running Docker-Minikube
image with the following command:

```shell
$ docker ps --format "{{.Names}} {{.ID}}"
minikube <image-id>

$ docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}/{{.IPPrefixLen}}{{end}}' <image-id>
192.168.49.2/24
```

This means that you have to ensure that the start/stop ip range for
the load balancer is within the `192.168.49.0/24` subnet. Your docker
subnet may (and likely is) different.

You can run `metallb` manually or use a python script to do so. We suggest using
the commands below.

To manually configure `metallb` run:

```shell
minikube addons configure metallb
```
If successful, the output should be `✅  metallb was successfully configured`.


Minikube does not provide a simple interactive way to configure addons,
([as shown in this repository issue](https://github.com/kubernetes/minikube/issues/8283)). Hence, we suggest setting the
load balancer IP address using a Python script with pre-established values. The recommendation to keep the values is due
to an existing DNS name that already points to the address. To do so, paste
[this Python script](https://github.com/Quansight/qhub/blob/dev/tests/scripts/minikube-loadbalancer-ip.py) on your terminal.


#### Enable MetalLB

Lastly, enable MetalLB by running
```shell
minikube addons enable metallb
```
To which the output should be `The 'metallb' addon is enabled`.

---

### Note for Development on Windows Subsystem for Linux 2 (WSL2)
The browser can have trouble reaching the load balancer running on WSL2. A workaround is to port forward the proxy-... pod to the host (ip 0.0.0.0). Get the ip address of the WSL2 machine via ```ip a```, it should be a 127.x.x.x address. To change the port forwarding after opening k9s you can type ```:pods <enter>```, hover over the proxy-... pod and type ```<shift-s>```, and enter the ip addresses.

### Deploy QHub
To deploy QHub handle setup dependencies and create a new sub-directory by running:
```bash
pip install -e .
mkdir -p data
cd data
```
### Initialize configuration
Then, initialize the configuration file `qhub-config.yaml` with:
```shell
python -m qhub init local --project=thisisatest  --domain github-actions.qhub.dev --auth-provider=password --terraform-state=local
```
### Generate user password
Each user on the `qhub-config.yaml` file will need a password.
A random password is auto generated for the user `example-user` when
the auth provider `password` is run, the value is then printed to the standard output (stdout).

In case you would like to change the generated password (optional), You can use
[bcrypt](https://pypi.org/project/bcrypt/) to generate your own salted password by using the following _Python command_
script:

```bash
python -c "import bcrypt; bcrypt.hashpw(b'<password>', bcrypt.gensalt())"
```
Where `<password>` can be changed to any desired value.

This requires the Python package `bcrypt` to be
installed in your virtual environment. The password must then be added to the `qhub-config.yaml` in the users
section, as illustrated below:

```yaml
  users:
    example-user:
      uid: 1000
      ...
      password: '$2b$12$lAk2Bhw8mu0QJkSecPiABOX2m87RF8N7vv7rBw9JksOgewI2thUuO'
      ...
      primary_group: users

```

### Deploy and render the infrastructure
Next, we will render the infrastructure files from `qhub-config.yaml` running

```shell
python -m qhub deploy --config qhub-config.yaml --disable-prompt
```

To ease development, we have already pointed the DNS record
`github-actions.qhub.dev` to `192.168.49.100` so the next step
is optional unless you end up with the load-balancer giving you
a different IP address.

Make sure to point the DNS domain `github-actions.qhub.dev` to
`192.168.49.100` from the previous commands. This can be done in many
ways, the easiest one is by modifying `/etc/hosts` and adding the
line below. The command will override any DNS server.

```ini
192.168.49.100 github-actions.qhub.dev
```
### Verify the local deployment

Finally, if everything is set properly you should be able to `cURL` the JupyterHub Server. Run
```bash
curl -k https://github-actions.qhub.dev/hub/login
```

It is also possible to visit `https://github-actions.qhub.dev` in your web
browser to check the deployment.

Since this is a local deployment, hence not visible to the internet;
`https` certificates will not be signed by [Let's
Encrypt](https://letsencrypt.org/). Thus, the certificates will be
[self-signed by Traefik](https://en.wikipedia.org/wiki/Self-signed_certificate).

Several
browsers will make it difficult to view a self-signed certificate that
has not been added to your certificate registry.

Each web browser handles this differently. A workaround for Firefox:

 - Visit `about:config` and change the `network.stricttransportsecurity.preloadlist` to `false`

### Cleanup

To delete all the QHub resources run the `destroy` command. Note that
this will not delete your `qhub-config.yaml` and related rendered
files thus a re-deployment via `deploy` is possible afterwards.

```shell
python -m qhub destroy --config qhub-config.yaml
```

To delete the Minikube Kubernetes cluster run the following command:

```shell
minikube delete
```
The command will delete all instances of QHub, cleaning up the deployment environment.

## Debug Kubernetes clusters

 To debug Kubernetes clusters, we advise you to use [K9s](https://k9scli.io/), a terminal-based UI that aims to
 simplify navigation, observation, and management of applications in Kubernetes.
 K9s continuously monitors Kubernetes clusters for changes and provides
 shortcut commands to interact with the observed resources becoming a
 fast way to review and resolve day-to-day issues in deployed clusters.

Installation can be done on a macOS, in Windows, and Linux and instructions
 can be found [here](https://github.com/derailed/k9s). For more details on usage,
check out the [Troubleshooting documentation](../02_get_started/06_troubleshooting.md#debug-your-kubernetes-cluster)

## Cloud Testing

TODO: Write detailed documentation on Cloud testing

Cloud testing on aws, gcp, azure, and digital ocean is significantly
more complicated and time consuming. You should always prefer the
local testing when possible.

## Testing on Mac

The earlier instructions for minikube on Linux should work on Mac except:

1 - When working out the IP addresses to configure metallb try this:
```
docker ps --format "{{.Names}} {{.ID}}"
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}/{{.IPPrefixLen}}{{end}}' <ID of minikube from previous cmd>
```

This will display something like `192.168.49.2/24`, in which case a suitable IP range would be on the same subnet, e.g. start IP 192.168.49.100, end IP 192.168.49.150.

2 - This load balancer won't actually work, so you need to port-forward directly to the JupyterHub service:
```
minikube kubectl -- --namespace=dev port-forward svc/proxy-public 8000:80
```
Then you can access QHub on http://127.0.0.1:8000/
