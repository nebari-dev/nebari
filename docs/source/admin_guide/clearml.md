# ClearML

ClearML integration comes built in with QHub, here is how you would enable this integration. Currently ClearML integration is only supported on Google Cloud Platform.

## Setting subdomain DNS Record for ClearML

ClearML components requires subdomains, you would need to set a `CNAME` or A record for the following subdomains on your QHub.

- app.clearml.your-qhub-domain.com
- files.clearml.your-qhub-domain.com
- api.clearml.your-qhub-domain.com

These domains are automatically setup for you, if you're using Cloudflare and the args `--dns-provider cloudflare --dns-auto-provision` passed to `qhub deploy`.

## Create a node group

1. To enable ClearML integration on Google Cloud QHub deployments, simply enable the feature flag within your `qhub-config.yaml` file. For example:

```yaml
clearml:
  enabled: true
```

2. Create a node group with label `app: clearml`.

```yaml
google_cloud_platform:
  #...
  node_groups:
    # ....
    clearml:
      instance: n1-highmem-16
      min_nodes: 1
      max_nodes: 5
      labels:
        app: clearml
```

## Accessing the server

Users can access the ClearML server at: `app.clearml.your-qhub-domain.com`

## Authentication

QHub secures ClearML dashboard by default with JupyterHub OAuth via Traefik ForwardAuth. You can turn it off via a flag in the QHub config YAML:

```yaml
clearml:
  enabled: true
  enable_forward_auth: false
```

This is especially useful for accessing ClearML programmatically.

## Overrides

Addition helm chart variables may want to be overridden. For this an override hook is provided where you can specify anything with the
[values.yaml](https://github.com/allegroai/clearml-helm-charts/tree/main/charts/clearml).

```yaml
clearml:
  enabled: true
  overrides:
    clearml:
      defaultCompany: "d1bd92a3b039400cbafc60a7a5b1e5ab"
```
