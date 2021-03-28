# Testing

## Modifying Docker Images

All QHub docker images are located in [qhub/templates/{{
cookiecutter.repo_directory
}}/image/](https://github.com/Quansight/qhub-cloud/tree/main/qhub/template/%7B%7B%20cookiecutter.repo_directory%20%7D%7D/image). You
can build any image locally. Additionally, on Pull Requests each Docker-build
will be tested.

```shell
docker build -f Dockerfile.<filename> .
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
[this Python script](https://github.com/Quansight/qhub-cloud/blob/dev/tests/scripts/minikube-loadbalancer-ip.py) on your terminal.


#### Enable MetalLB

Lastly, enable MetalLB by running
```shell
minikube addons enable metallb
```
To which the output should be `The 'metallb' addon is enabled`.

### Debug your Kubernetes cluster

 [K9s](https://k9scli.io/) is a terminal-based UI to manage Kubernetes clusters that aims to
 simplify navigating, observing, and managing your applications in K8s.
 K9s continuously monitors Kubernetes clusters for changes and provides
 shortcut commands to interact with the observed resources becoming a
 fast way to review and resolve day-to-day issues in Kubernetes. It's
 definitely a huge improvement to the general workflow, and a best-to-have
 tool for debugging your Kubernetes cluster sessions.

Installation can be done on a macOS, in Windows, and Linux. Instructions
for each operating system can be found [here](https://github.com/derailed/k9s).
Be sure to complete installation to be able to follow along.

By default, K9s starts with the standard directory that is set as the
context (in this case Minkube). To view all the current process press `0`:

![Image of K9s termina UI](https://k9scli.io/assets/screens/pods.png)

---
> NOTE: In some circumstances you will be confronted with the
  necessity to inspect in your ‘localhost’ any services launched by
  your cluster. For instance, if your cluster has issues with the
  network traffic tunnel configuration it may limit or block the user's
  access to destination resources over the connection.

K9s port-forward option `<kbd>shift</kbd> + <kbd>f</kbd>` allows you to access and interact
with internal Kubernetes cluster processes from your localhost you can
then use this method to investigate issues and adjust your services
locally without the need to expose them beforehand.

---

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

## Cloud Testing

TODO: Write detailed documentation on Cloud testing

Cloud testing on AWS, GCP, Azure, and DigitalOcean is significantly
more complicated and time-consuming. When possible, you should always
prefer to perform your tests locally.
