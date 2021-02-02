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

```
-- Enter Load Balancer Start IP: 172.17.1.100
-- Enter Load Balancer End IP: 172.17.1.200
✅  metallb was successfully configured
```

Enable metallb

```shell
minikube addons enable metallb
```

```
🌟  The 'metallb' addon is enabled
```

## Deploy qhub

```shell
mkdir -p data
```

Initialize the `qhub-config.yaml`

```shell
python -m qhub init local --auth-provider=password --terraform-state=local
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
cd infrastructure
terraform init
terraform apply
```
