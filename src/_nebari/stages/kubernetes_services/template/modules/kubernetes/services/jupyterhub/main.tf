resource "random_password" "service_token" {
  for_each = var.services

  length  = 32
  special = false
}

resource "random_password" "proxy_secret_token" {
  length  = 32
  special = false
}

resource "random_password" "jhub_apps_jwt_secret" {
  length  = 32
  special = false
}

locals {
  jhub_apps_secrets_name = "jhub-apps-secrets"
  jhub_apps_env_var_name = "JHUB_APP_JWT_SECRET_KEY"
}

resource "kubernetes_secret" "jhub_apps_secrets" {
  metadata {
    name      = local.jhub_apps_secrets_name
    namespace = var.namespace
  }

  data = {
    jwt_secret_key = random_password.jhub_apps_jwt_secret.result
  }

  type = "Opaque"
}

locals {
  jupyterhub_env_vars = [
    {
      name = local.jhub_apps_env_var_name,
      valueFrom : {
        secretKeyRef : {
          name : local.jhub_apps_secrets_name
          key : "jwt_secret_key"
        }
      }
    }
  ]
}


resource "helm_release" "jupyterhub" {
  name      = "jupyterhub-${var.namespace}"
  namespace = var.namespace

  repository = "https://jupyterhub.github.io/helm-chart/"
  chart      = "jupyterhub"
  version    = "3.2.1"

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      # custom values can be accessed via z2jh.get_config('custom.<path>')
      custom = {
        namespace                     = var.namespace
        external-url                  = var.external-url
        theme                         = var.theme
        profiles                      = var.profiles
        argo-workflows-enabled        = var.argo-workflows-enabled
        home-pvc                      = var.home-pvc
        shared-pvc                    = var.shared-pvc
        conda-store-pvc               = var.conda-store-pvc
        conda-store-mount             = var.conda-store-mount
        default-conda-store-namespace = var.default-conda-store-namespace
        conda-store-service-name      = var.conda-store-service-name
        conda-store-jhub-apps-token   = var.conda-store-jhub-apps-token
        jhub-apps-enabled             = var.jhub-apps-enabled
        initial-repositories          = var.initial-repositories
        skel-mount = {
          name      = kubernetes_config_map.etc-skel.metadata.0.name
          namespace = kubernetes_config_map.etc-skel.metadata.0.namespace
        }
        extra-mounts = merge(
          var.extra-mounts,
          {
            "/etc/ipython" = {
              name      = kubernetes_config_map.etc-ipython.metadata.0.name
              namespace = kubernetes_config_map.etc-ipython.metadata.0.namespace
              kind      = "configmap"
            }

            "/etc/jupyter" = {
              name      = kubernetes_config_map.etc-jupyter.metadata.0.name
              namespace = kubernetes_config_map.etc-jupyter.metadata.0.namespace
              kind      = "configmap"
            }

            "/opt/conda/envs/default/share/jupyter/lab/settings" = {
              name      = kubernetes_config_map.jupyterlab-settings.metadata.0.name
              namespace = kubernetes_config_map.jupyterlab-settings.metadata.0.namespace
              kind      = "configmap"
            }

          }
        )
        environments = var.conda-store-environments
      }

      hub = {
        image = var.jupyterhub-image
        nodeSelector = {
          "${var.general-node-group.key}" = var.general-node-group.value
        }

        extraVolumes = [{
          name = "conda-store-shared"
          persistentVolumeClaim = {
            claimName = var.conda-store-pvc
          }
        }]

        extraVolumeMounts = [{
          mountPath = var.conda-store-mount
          name      = "conda-store-shared"
        }]

        extraConfig = {
          "01-theme.py"    = file("${path.module}/files/jupyterhub/01-theme.py")
          "02-spawner.py"  = file("${path.module}/files/jupyterhub/02-spawner.py")
          "03-profiles.py" = file("${path.module}/files/jupyterhub/03-profiles.py")
        }

        services = {
          for service in var.services : service => {
            name      = service
            admin     = true
            api_token = random_password.service_token[service].result
          }
        }

        # for simple key value configuration with jupyterhub traitlets
        # this hub.config property should be used
        config = {
          JupyterHub = {
            authenticator_class = "generic-oauth"
          }
          Authenticator = {
            enable_auth_state = true
          }
          GenericOAuthenticator = {
            client_id          = module.jupyterhub-openid-client.config.client_id
            client_secret      = module.jupyterhub-openid-client.config.client_secret
            oauth_callback_url = "https://${var.external-url}/hub/oauth_callback"
            authorize_url      = module.jupyterhub-openid-client.config.authentication_url
            token_url          = module.jupyterhub-openid-client.config.token_url
            userdata_url       = module.jupyterhub-openid-client.config.userinfo_url
            login_service      = "Keycloak"
            username_key       = "preferred_username"
            claim_groups_key   = "roles"
            allowed_groups     = ["jupyterhub_admin", "jupyterhub_developer"]
            admin_groups       = ["jupyterhub_admin"]
            tls_verify         = false
          }
        }
      }

      proxy = {
        chp = {
          nodeSelector = {
            "${var.general-node-group.key}" = var.general-node-group.value
          }
        }
      }

      singleuser = {
        image = var.jupyterlab-image
        nodeSelector = {
          "${var.user-node-group.key}" = var.user-node-group.value
        }
      }

      scheduling = {
        userScheduler = {
          nodeSelector = {
            "${var.user-node-group.key}" = var.user-node-group.value
          }
        }
      }
    })],
    var.overrides,
    [jsonencode({
      hub = {
        extraEnv = concat([
          {
            name  = "OAUTH_LOGOUT_REDIRECT_URL",
            value = format("%s?redirect_uri=%s", "https://${var.external-url}/auth/realms/${var.realm_id}/protocol/openid-connect/logout", urlencode(var.jupyterhub-logout-redirect-url))
          },
          ],
          concat(local.jupyterhub_env_vars, jsondecode(var.jupyterhub-hub-extraEnv))
        )
      }
    })]
  )

  set {
    name  = "proxy.secretToken"
    value = random_password.proxy_secret_token.result
  }
}


resource "kubernetes_manifest" "jupyterhub" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "jupyterhub"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && (Path(`/`) || PathPrefix(`/hub`) || PathPrefix(`/user`) || PathPrefix(`/services`))"
          services = [
            {
              name = "proxy-public"
              port = 80
            }
          ]
        }
      ]
    }
  }
}


module "jupyterhub-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "jupyterhub"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["jupyterhub_admin", "dask_gateway_admin"]
    "developer" = ["jupyterhub_developer", "dask_gateway_developer"]
    "analyst"   = ["jupyterhub_developer"]
  }
  callback-url-paths = [
    "https://${var.external-url}/hub/oauth_callback",
    var.jupyterhub-logout-redirect-url
  ]
  jupyterlab_profiles_mapper = true
}


resource "kubernetes_secret" "argo-workflows-conda-store-token" {
  metadata {
    name      = "argo-workflows-conda-store-token"
    namespace = var.namespace
  }

  data = {
    "conda-store-api-token"    = var.conda-store-argo-workflows-jupyter-scheduler-token
    "conda-store-service-name" = var.conda-store-service-name
  }

  type = "Opaque"
}
