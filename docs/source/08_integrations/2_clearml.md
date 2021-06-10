# ClearML

ClearML Integration comes built in with QHub, here is how you would
enable this integration.

## Setting subdomain DNS Record for ClearML

ClearML components requires subdomains, you would need to set an A record
for the following subdomains on your QHub.

- app.clearml.your-qhub-domain.com
- files.clearml.your-qhub-domain.com
- api.clearml.your-qhub-domain.com

Note: These domains are automatically setup for you, if you're using Cloudflare and the
args `--dns-provider cloudflare --dns-auto-provision` passed to `qhub deploy`.


## Create a node group

ClearML has a bunch of components, so it is necessary to create a separate node
group dedicated for ClearML. For example:

```yaml

google_cloud_platform:
  project: your-qhub
  region: us-central1
  kubernetes_version: 1.18.16-gke.502
  node_groups:
    #....
    clearml:
      instance: n1-highmem-16
      min_nodes: 1
      max_nodes: 5
```

## Accessing the ClearML server

The ClearML server can be accessed at: `app.clearml.your-qhub-domain.com`
