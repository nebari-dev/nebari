# Local Testing

## Initialize kubernetes cluster

Testing done with minikube

```shell
minikube start --cpus 2 --memory 4096 --driver=docker
```

The jupyterlab instances require mounting nfs pvcs. This required
nfs-common drivers be installed.

```shell
minikube ssh "sudo apt update; sudo apt install nfs-common -y"
```

Configure `metallb`

```shell
minikube addons configure metallb
```

If you don't want to configure metallb interactively here is a short
bash command to run. This is used in the github actions since the
minikube command does [not provide a no interactive simple way to
configure addons](https://github.com/kubernetes/minikube/issues/8283)

```shell
python <<EOF
import json
import os

filename = os.path.expanduser('~/.minikube/profiles/minikube/config.json')
with open(filename) as f:
     data = json.load(f)

data['KubernetesConfig']['LoadBalancerStartIP'] = '172.17.1.100'
data['KubernetesConfig']['LoadBalancerEndIP'] = '172.17.1.200'

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

## Deploy qhub

```shell
export PYTHONPATH=$PWD:$PYTHONPATH
mkdir -p data
```

Initialize the `qhub-config.yaml`

```shell
python -m qhub init local --project=thisisatest  --domain qhub.test --auth-provider=password --terraform-state=local
```

Give a password to the default user. For this the example password is
`<password>`. You can generate your own via `import bcrypt;
bcrypt.hashpw(b'<password>', bcrypt.gensalt())`. Where you can change
`<password>` to be the password you want.

```
    costrouc:
      uid: 1000
      ...
      password: '$2b$12$VsGc2HK1HF0o.8eJGHLlDenkseUf6B1pxizxgAN6/elR.ZaX8u0OG'
      ...
      primary_group: users

```

Finder the files from the `qhub-config.yaml`

```shell
python -m qhub render --config qhub-config.yaml -f
```

```shell
python -m qhub deploy --config qhub-config.yaml --disable-prompt
```

Make sure to point the dns domain `jupyter.qhub.test` to
`172.17.1.100` from the previous commands. This can be done in many
ways possibly the easiest is modifying `/etc/hosts` and adding the
following line. This will override any dns server.

```ini
172.17.1.100 jupyter.qhub.test
```

Finally if everything is set properly you should be able to curl the
jupyterhub server.

```
curl -k https://jupyter.qhub.test/hub/login
```

You can also visit `https://jupyter.qhub.test`

## Cleanup

```shell
python -m qhub destroy --config qhub-config.yaml 
```

```shell
minikube delete
```
