# ClearML

ClearML integration comes built in with QHub, here is how you would
enable this integration.  Currently ClearML integration is only supported on Google Cloud Platform.

## Setting subdomain DNS Record for ClearML

ClearML components requires subdomains, you would need to set an A record
for the following subdomains on your QHub.

- app.clearml.your-qhub-domain.com
- files.clearml.your-qhub-domain.com
- api.clearml.your-qhub-domain.com

Note: These domains are automatically setup for you, if you're using Cloudflare and the
args `--dns-provider cloudflare --dns-auto-provision` passed to `qhub deploy`.


## Create a node group

To enable ClearML integration on GCP QHub deployments, simply enable the feature flag within your `qhub-config.yaml` file. For example:

```yaml
clearml:
  enabled: true
```

## Accessing the ClearML server

The ClearML server can be accessed at: `app.clearml.your-qhub-domain.com`
