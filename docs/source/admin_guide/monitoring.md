# Monitoring

Cluster monitoring via Grafana/Prometheus comes built in with QHub, here is how you would
enable this integration.

## Enabling Cluster Monitoring

1. To enable cluster monitoring on QHub deployments, simply enable the feature flag within your `qhub-config.yaml` file. For example:

```yaml
monitoring:
  enabled: true
```

## Accessing the Grafana Dashboards

The monitoring dashboards can be accessed via Grafana at: `your-qhub-domain.com/monitoring`.  The initial login credentials are username: `admin` and password: `prom-operator`, but users should change the admin password immediately after the first log in. 
