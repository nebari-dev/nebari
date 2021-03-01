# Testing

## Modifying Docker Images

All QHub docker images are located in [qhub/templates/{{
cookiecutter.repo_directory
}}/image/](https://github.com/Quansight/qhub-cloud/tree/main/qhub/template/%7B%7B%20cookiecutter.repo_directory%20%7D%7D/image). You
can build any image locally. Additionally on PRs each docker build
will be tested.

```shell
docker build -f Dockerfile.<filename> .
```

## Local Testing

Local testing is a great way to test the components of QHub. While it
does test most of everything it does not test cloud provisioned
components such as the managed kubernetes cluster, vpcs, managed
container registries, etc.

This guide assumes that you have the QHub Cloud repository downloaded
and you are at the root of the repository.

### Dependencies

In order to develop with QHub you will need to download the following
dependencies and have them available in your path.

 - [terraform](https://www.terraform.io/downloads.html)
 - [minikube](https://v1-18.docs.kubernetes.io/docs/tasks/tools/install-minikube/)

### Initialize kubernetes cluster

Testing is done with minikube. Note that this will download a ~500MB
docker image.

Note: The testing instructions mentioned below works well on Linux. They
don't work very well with Mac OS at the moment, due to the
[limitations of docker for Mac](https://docs.docker.com/docker-for-mac/networking/#known-limitations-use-cases-and-workarounds),
the primary limitation being Docker Desktop for Mac can’t route traffic
to containers. It should be possible to achieve these with hyperkit driver
with minikube, but it has not been tested yet.

```shell
minikube start --cpus 2 --memory 4096 --driver=docker
```

The jupyterlab instances require mounting nfs pvcs. This requires
nfs-common drivers be installed on the nodes themselves.

```shell
minikube ssh "sudo apt update; sudo apt install nfs-common -y"
```

Configure the `metallb` load balancer to have a start ip of
`172.17.10.100` and an end ip of `172.17.10.200`. These ips were not
randomly chosen. You must make sure that the ip range is within the
docker interface subnet. You can see your docker subnet via

```shell
$ ip route
default via 192.168.1.1 dev wlp4s0 proto dhcp metric 600 
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 
```

This means that you have to ensure that the start/stop ip range
for the load balancer is within the `172.17.0.0/16` subnet. Your
docker subnet may be different. You can run `metallb` manually as
shown below or use the python command shown below. We suggest using
these values since there is a dns name that already points to the
address.

```shell
minikube addons configure metallb
```

If you don't want to configure metallb interactively run the below
bash/python command. This is also used in github actions since
the minikube command does not [provide a non interactive way to
configure addons](https://github.com/kubernetes/minikube/issues/8283)

```shell
python <<EOF
import json
import os

filename = os.path.expanduser('~/.minikube/profiles/minikube/config.json')
with open(filename) as f:
     data = json.load(f)

data['KubernetesConfig']['LoadBalancerStartIP'] = '172.17.10.100'
data['KubernetesConfig']['LoadBalancerEndIP'] = '172.17.10.200'

with open(filename, 'w') as f:
     json.dump(data, f)
EOF
```

Enable metallb

```shell
minikube addons enable metallb
```

```
  The 'metallb' addon is enabled
```

### Deploy qhub

```shell
pip install -e .
mkdir -p data
cd data
```

Initialize the `qhub-config.yaml`

```shell
python -m qhub init local --project=thisisatest  --domain github-actions.qhub.dev --auth-provider=password --terraform-state=local
```

Give a password to the default user. For this the example password is
`example-user`. You can generate your own via `python -c "import bcrypt;
bcrypt.hashpw(b'<password>', bcrypt.gensalt())"`. Where you can change
`<password>` to be the password you want. This requires the bcrypt python 
package to be installed. This must be added to the `qhub-config.yaml` in 
the users section shown like below.

```
  users:
    example-user:
      uid: 1000
      ...
      password: '$2b$12$lAk2Bhw8mu0QJkSecPiABOX2m87RF8N7vv7rBw9JksOgewI2thUuO'
      ...
      primary_group: users

```

Render the files from the `qhub-config.yaml`

```shell
python -m qhub render --config qhub-config.yaml -f
```

```shell
python -m qhub deploy --config qhub-config.yaml --disable-prompt
```

To ease development we have already pointed the dns record
`jupyter.github-actions.qhub.dev` to `172.17.10.100` so the next step
is optional unless you end up with the load-balancer giving you
a different ip address.

Make sure to point the dns domain `jupyter.github-actions.qhub.dev` to
`172.17.10.100` from the previous commands. This can be done in many
ways possibly the easiest is modifying `/etc/hosts` and adding the
following line. This will override any dns server.

```ini
172.17.10.100 jupyter.github-actions.qhub.dev
```

Finally, if everything is set properly you should be able to `curl` the JupyterHub Server.
jupyterhub server.

```
curl -k https://jupyter.github-actions.qhub.dev/hub/login
```

You can also visit `https://jupyter.github-actions.qhub.dev` in your
web browser.

### Cleanup

```shell
python -m qhub destroy --config qhub-config.yaml 
```

```shell
minikube delete
```

## Cloud Testing

TODO: write docs on cloud testing

Cloud testing on aws, gcp, azure, and digital ocean is significantly
more complicated and time consuming. You should always prefer the
local testing when possible.
