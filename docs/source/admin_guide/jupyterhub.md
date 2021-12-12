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

There is special behavior for the values `jupyterhub.overrides.hub.extraEnv` and `jupyterhub.overrides.hub.extraConfig`. Setting these would have naturally seen them be overridden in their entirety by QHub's own values, but there is special treatment whereby QHub's values are merged into the list of any values that you might have set as overrides.

In general, it is possible that other overrides will always be lost where QHub sets its own values, so caution must be taken, and in debugging ensure that you are prepared for unexpected results when using overrides.
