# Keycloak

QHub includes a deployment of [Keycloak](https://www.keycloak.org/documentation.html) to centralise user management.

Within the `qhub deploy` step, Keycloak is installed using the [Helm chart](https://github.com/codecentric/helm-charts/tree/master/charts/keycloak).

It's possible to specify Helm overrides (i.e. your own values for selected fields in the Keycloak deployment's `values.yaml` file) from the `qhub-config.yaml` file. However, be aware that this may conflict with values that are needed to be set in a certain way in order for QHub to operate correctly.

To set a Helm override, for example:

```
security:
  keycloak:
    initial_root_password: password123
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
