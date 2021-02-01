# Local Testing 

## Initialize kubernetes cluster

Testing done with minikube

```shell
minikube start --cpus 2 --memory 4096 --driver=docker
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

```shell
python -m qhub init local --auth-provider=password
```

```shell
python -m qhub render --config qhub-config.yaml -f
```

```shell
cd infrastructure
terraform init
terraform apply
```
