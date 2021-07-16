# Monitoring

Cluster monitoring via Grafana/Prometheus comes built in with QHub, and is enabled by default.

## Accessing the Grafana Dashboards

The monitoring dashboards can be accessed via Grafana at: `your-qhub-domain.com/monitoring`.  The initial login credentials are username: `admin` and password: `prom-operator`, but users should change the admin password immediately after the first log in. 

## Disabling Cluster Monitoring

1. To disable cluster monitoring on QHub deployments, simply disable the feature flag within your `qhub-config.yaml` file. For example:

```yaml
monitoring:
  enabled: false
```
