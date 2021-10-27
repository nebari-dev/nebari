# Other Helm Charts

Arbitrary helm charts can be deployed and managed with the qhub-config.yaml file.

Prefect is a workflow automation system. QHub integrates Prefect with a
feature flag as follows (in the top level):

As an example, deploying the redis helm chart with qhub might look like the below:

```yaml
helm_extensions:
  - name: my-redis-deployment
    repository: https://charts.bitnami.com/bitnami
    chart: redis
    version: 15.5.1
    overrides:
        diagnosticMode:
            enabled: true
```

The `overrides` section is optional, but corresponds to the helm chart's [values.yaml](https://helm.sh/docs/chart_template_guide/values_files/) file, and allows you to override the default helm chart settings.
