# JupyterHub

QHub has the JupyterHub project at its core.

Within the `qhub deploy` step, JupyterHub is installed using the [Zero2JupyterHub Helm package](https://zero-to-jupyterhub.readthedocs.io/).

It is possible to specify Helm overrides (i.e. your own values for selected fields in the JupyterHub deployment's `values.yaml` file) from the `qhub-config.yaml` file. However, be aware that this may conflict with values that are needed to be set in a certain way in order for QHub to operate correctly.

To set a Helm override, for example enabling auth state:

```
jupyterhub:
  overrides:
    hub:
      config:
        Authenticator:
          enable_auth_state: true
```

Where it is possible to influence a value using 'native' QHub configuration, you should use that as a preference. For example, you would not set `jupyterhub.overrides.hub.image.name` to use a custom JupyterHub Docker image. Instead you would set `default_images.jupyterhub`.
