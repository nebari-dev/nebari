# Argo Workflows

Argo Workflows is an open source container-native workflow engine for orchestrating parallel jobs on Kubernetes. Argo
workflows comes enabled by default with Nebari deployments.

## Accessing Argo Server

If Argo Workflows is enabled, users can access argo workflows server at: `your-nebari-domain.com/argo`. Log in via
Keycloak with your usual credentials.

## Overrides of Argo Workflows Helm Chart values

Argo Workflows is deployed using the Argo Workflows Helm Chart. The values.yaml for the helm chart can be overridden as
needed via the overrides flag. The default values file can be found
[here](https://github.com/argoproj/argo-helm/blob/argo-workflows-0.22.9/charts/argo-workflows/values.yaml). For example,
the following could be done to add additional environment variables to the controller container.

```yaml
argo_workflows:
  enabled: true
  overrides:
    controller:
      extraEnv:
        - name: foo
          value: bar
```

## Disabling Argo Workflows

To turn off the cluster monitoring on Nebari deployments, simply turn off the feature flag within your
`nebari-config.yaml` file. For example:

```yaml
argo_workflows:
  enabled: false
```

Refer to the [Argo documentation](https://argoproj.github.io/argo-workflows/) for further details on Argo Workflows.
