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

## Clearml configuration overrides

You can override your configuration without having to modify the helm files directly. The extra variable `overrides` makes this possible by changing the default values for the clearml helm chart according to the settings presented on your qhub-config.yaml file.

For example, if you just want to override the node selector used for the agent you could use the following:

```yaml
prefect:
 enabled: true
 overrides:
     agentServices:
       NodeSelector:
         app: "clearml_agent"
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
