# Keycloak

QHub includes a deployment of [Keycloak](https://www.keycloak.org/documentation.html) to centralise user management.

Within the `qhub deploy` step, Keycloak is installed using the [Helm chart](https://github.com/codecentric/helm-charts/tree/master/charts/keycloak).

It's possible to specify Helm overrides (i.e. your own values for selected fields in the Keycloak deployment's `values.yaml` file) from the `qhub-config.yaml` file. However, be aware that this may conflict with values that are needed to be set in a certain way in order for QHub to operate correctly.

To set a Helm override, for example:

```
security:
  keycloak:
    initial_root_password: password123
    realm_display_name: "Our Company QHub"
    overrides:
      extraEnv: |
        - name: KEYCLOAK_DEFAULT_THEME
          value: entqhubtheme
        - name: KEYCLOAK_WELCOME_THEME
          value: entqhubtheme
        - name: PROXY_ADDRESS_FORWARDING
          value: "true"
      image:
        repository: dockerusername/my-qhub-keycloak
```

If you do set `overrides.extraEnv` as above, you must remember to include `PROXY_ADDRESS_FORWARDING=true`. Otherwise, the Keycloak deployment will not work as you will have overridden an important default Helm value that's required by QHub.

To find out more about using Keycloak in QHub, see [Installation - Login](../installation/login.md)

The `security.keycloak.realm_display_name` setting is the text to display on the Keycloak login page for your QHub (and in some other locations). This is optional, and if omitted will default to "QHub <project_name>" where `project_name` is a field in the `qhub-config.yaml` file.
