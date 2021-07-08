# ClearML

ClearML integration comes built in with QHub, here is how you would
enable this integration.  Currently ClearML integration is only
supported on Google Cloud Platform.

## Setting subdomain DNS Record for ClearML

ClearML components requires subdomains, you would need to set a CNMAE
or A record for the following subdomains on your QHub.

- app.clearml.your-qhub-domain.com
- files.clearml.your-qhub-domain.com
- api.clearml.your-qhub-domain.com

Note: These domains are automatically setup for you, if you're using Cloudflare and the
args `--dns-provider cloudflare --dns-auto-provision` passed to `qhub deploy`.


## Create a node group

1. To enable ClearML integration on GCP QHub deployments, simply enable the feature flag within your `qhub-config.yaml` file. For example:

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

## Accessing the ClearML server

The ClearML server can be accessed at: `app.clearml.your-qhub-domain.com`
